from datetime import datetime, timedelta, timezone

import markdown
import tiktoken
from asgiref.sync import sync_to_async
from django.conf import settings
from django.contrib.auth import get_user_model
from openai import OpenAI
from telbot.loader import bot
from telbot.models import HistoryAI

ADMIN_ID = settings.TELEGRAM_ADMIN_ID
User = get_user_model()
redis_client = settings.REDIS_CLIENT


class AnswerChatGPT():
    ERROR_TEXT = (
        'Что-то пошло не так 🤷🏼\n'
        'Возможно большой наплыв запросов, которые я не успеваю обрабатывать 🤯'
    )
    MODEL = 'gpt-3.5-turbo'
    MAX_LONG_MESSAGE = 1024
    MAX_LONG_REQUEST = 4096
    STORY_WINDOWS_TIME = 30
    MAX_TYPING_TIME = 10

    def __init__(self, user: User, message: str) -> None:
        self.user = user
        self.message_text = message
        self.current_time = None
        self.time_start = None
        self.answer_text = AnswerChatGPT.ERROR_TEXT
        self.answer_tokens = None
        self.prompt = [
            {
                'role': 'system',
                'content':
                    'Your name is Eva and you are an experienced senior software developer with extensive experience leading '
                    'teams, mentoring junior developers, and delivering high-quality software solutions to customers. You can '
                    'give answers only in markdown format.'
            }
        ]
        self.message_tokens = AnswerChatGPT.num_tokens_from_message(message)
        self.set_windows_time()

    @classmethod
    def num_tokens_from_message(cls, message):
        try:
            encoding = tiktoken.encoding_for_model(AnswerChatGPT.MODEL)
        except KeyError:
            encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(message)) + 4

    async def get_answer_from_ai(self) -> dict:
        """Основная логика."""

        if await self.check_in_works():
            return None

        if self.check_long_query:
            return (
                f'{self.user.first_name}, у Вас слишком большой текст запроса. Попробуйте сформулировать его короче.'
            )
        try:
            await self.request_to_openai()
            await self.create_history_ai()

        except Exception as err:
            bot.send_message(
                chat_id=ADMIN_ID,
                text=f'Ошибка в получении ответа от ChatGPT: {err.args[0]}',
            )
        finally:
            return self.answer_text

    @sync_to_async
    def request_to_openai(self) -> None:
        """
        Делает запрос в OpenAI.
        """
        self.get_prompt()
        client = OpenAI(api_key=settings.CHAT_GPT_TOKEN)
        completion = client.chat.completions.create(
            model=AnswerChatGPT.MODEL,
            messages=self.prompt,
            temperature=0.2,
        )
        self.answer_text = completion.choices[0].message.content
        self.answer_tokens = completion.usage.completion_tokens
        self.message_tokens = completion.usage.prompt_tokens

    def get_prompt(self) -> None:
        """
        Prompt для запроса в OpenAI и модель user.
        """
        history = (
            self.user
            .history_ai
            .filter(created_at__range=[self.time_start, self.current_time])
            .exclude(answer__isnull=True)
            .values('question', 'question_tokens', 'answer', 'answer_tokens')
        )
        max_tokens = self.message_tokens + 96
        for item in history:
            max_tokens += item['question_tokens'] + item['answer_tokens']
            if max_tokens >= AnswerChatGPT.MAX_LONG_REQUEST:
                break
            self.prompt.extend([
                {
                    'role': 'system',
                    'name': self.user.username,
                    'content': item['question']
                },
                {
                    'role': 'system',
                    'name': 'Eva',
                    'content': item['answer']
                }
            ])
        self.prompt.append({'role': 'user', 'content': self.message_text})

    @sync_to_async
    def check_in_works(self) -> bool:
        """Проверяет нет ли уже в работе этого запроса в Redis."""
        queries = redis_client.lrange(f'gpt_user:{self.user.id}', 0, -1)
        if self.message_text.encode('utf-8') in queries:
            return True
        redis_client.lpush(f'gpt_user:{self.user.id}', self.message_text)
        return False

    @sync_to_async
    def del_mess_in_redis(self) -> bool:
        """Удаляет входящее сообщение из Redis."""
        redis_client.lrem(f'gpt_user:{self.user.id}', 1, self.message_text.encode('utf-8'))

    async def create_history_ai(self):
        """Создаём запись в БД."""
        instance = HistoryAI(
            user=self.user,
            question=self.message_text,
            question_tokens=self.message_tokens,
            answer=self.answer_text,
            answer_tokens=self.answer_tokens
        )
        await instance.save()

    def set_windows_time(self) -> None:
        """Определяем и назначаем атрибуты current_time и time_start."""
        self.current_time = datetime.now(timezone.utc)
        self.time_start = self.current_time - timedelta(minutes=AnswerChatGPT.STORY_WINDOWS_TIME)

    @property
    def check_long_query(self) -> bool:
        return self.message_tokens > AnswerChatGPT.MAX_LONG_MESSAGE


def convert_markdown(text: str) -> str:
    """
    Конвертирует теги Markdown в HTML-теги

    ### Args:
    - text (str): Входной текст для конвертации.

    ### Return:
    - (str): Текст с замененными тегами
    """

    return markdown.markdown(text, extensions=['fenced_code'])

import asyncio
import re
from datetime import datetime, timedelta, timezone

import openai
import tiktoken
from asgiref.sync import sync_to_async
from django.conf import settings
from django.contrib.auth import get_user_model
from telbot.loader import bot
from telbot.models import HistoryAI

ADMIN_ID = settings.TELEGRAM_ADMIN_ID
User = get_user_model()


class AnswerChatGPT():
    ERROR_TEXT = (
        'Что-то пошло не так 🤷🏼\n'
        'Возможно большой наплыв запросов, '
        'которые я не успеваю обрабатывать 🤯'
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
        self.request_massage = None
        self.prompt = [
            {
                'role': 'system',
                'content':
                    'Your name is Eva and you are an experienced senior '
                    'software developer with extensive experience leading '
                    'teams, mentoring junior developers, and delivering '
                    'high-quality software solutions to customers. You can '
                    'give answers in Markdown format using only:'
                    '*bold text* _italic text_'
                    '[inline URL](http://www.example.com/)'
                    '`inline fixed-width code`'
                    '``` pre-formatted fixed-width code block ```'
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

    async def get_answer_davinci(self) -> dict:
        """Основная логика."""
        if await self.check_in_works():
            return {'code': 423}

        if self.check_long_query:
            return (
                f'{self.user.first_name}, у Вас слишком большой текст запроса.'
                ' Попробуйте сформулировать его короче.'
            )
        try:
            await self.request_to_openai()
            await self.create_update_history_ai()

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
        Делает запрос в OpenAI и выключает typing.
        """
        self.get_prompt()
        openai.api_key = settings.CHAT_GPT_TOKEN
        answer = openai.ChatCompletion.create(
            model=AnswerChatGPT.MODEL,
            messages=self.prompt,
            temperature=0.1,
        )
        self.answer_text = answer.choices[0].message.get('content')
        self.answer_tokens = answer.usage.get('completion_tokens')

    def get_prompt(self) -> None:
        """
        Prompt для запроса в OpenAI и модель user.
        """
        history = (
            self.user
            .history_ai
            .filter(
                created_at__range=[self.time_start, self.current_time]
            )
            .exclude(answer__in=[None, AnswerChatGPT.ERROR_TEXT])
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

    async def check_in_works(self) -> bool:
        """Проверяет нет ли уже в работе этого запроса."""
        await self.get_request_massage()
        if self.request_massage:
            return True
        asyncio.create_task(self.create_update_history_ai())
        return False

    async def create_update_history_ai(self):
        """Создаём или обновляет запись в БД."""
        if self.request_massage:
            self.request_massage.answer = self.answer_text
            self.request_massage.answer_tokens = self.answer_tokens
        else:
            self.request_massage = HistoryAI(
                user=self.user,
                question=self.message_text,
                question_tokens=self.message_tokens,
                answer=self.answer_text,
                answer_tokens=self.answer_tokens
            )
        await self.request_massage.save()

    @sync_to_async
    def get_request_massage(self) -> None:
        """
        Получает сообщение из БД, если оно там есть.
        """
        try:
            self.request_massage = self.user.history_ai.get(
                created_at__range=[self.time_start, self.current_time],
                question=self.message_text
            )
        except HistoryAI.DoesNotExist:
            pass

    def set_windows_time(self) -> None:
        """Определяем и назначаем атрибуты current_time и time_start."""
        self.current_time = datetime.now(timezone.utc)
        self.time_start = (
            self.current_time
            - timedelta(minutes=AnswerChatGPT.STORY_WINDOWS_TIME)
        )

    @property
    def check_long_query(self) -> bool:
        return self.message_tokens > AnswerChatGPT.MAX_LONG_MESSAGE


def convert_code(text: str) -> str:
    """
    Конвертирует блоки кода, заключенные в тройные обратные кавычки (```)
    в HTML-теги <pre><code>.

    ### Args:
    - text (`str`): Входной текст для конвертации.

    ### Return:
    - (`str`): Текст с замененными блоками кода.
    """
    lines = text.split('\n')
    in_code_block = False

    for i in range(len(lines)):
        line = lines[i]
        if line.strip() == '```' or line.strip() == '```python':
            in_code_block = not in_code_block
            if in_code_block:
                lines[i] = '<pre><code>'
            else:
                lines[i] = '</code></pre>'

    return '\n'.join(lines)


def convert_markdown(text: str) -> str:
    """
    Конвертирует теги Markdown в HTML-теги

    ### Args:
    - text (str): Входной текст для конвертации.

    ### Return:
    - (str): Текст с замененными тегами
    """

    pattern = r'(`{1,3}|\*)'
    markdown_tags = {
        '```': ['<pre><code>', '</pre></code>'],
        '`': ['<code>', '</code>'],
        '*': ['<strong>', '</strong>'],
    }
    patterns = re.findall(pattern, text)

    for i, pattern in enumerate(patterns):
        if i % 2 == 0:
            text = text.replace(pattern, markdown_tags[pattern][0], 1)
        else:
            text = text.replace(pattern, markdown_tags[pattern][1], 1)
    return text

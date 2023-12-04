import json
from datetime import datetime, timedelta, timezone

import httpx
import markdown
import tiktoken
from asgiref.sync import sync_to_async
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.conf import settings
from django.contrib.auth import get_user_model
from httpx_socks import AsyncProxyTransport
from openai import AsyncOpenAI
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
    MAX_TYPING_TIME = 3

    def __init__(self, channel_layer: AsyncWebsocketConsumer, room_group_name: str, user: User, message: str, message_count: int) -> None:
        self.channel_layer = channel_layer
        self.room_group_name = room_group_name
        self.message_text = message
        self.user = user
        self.message_count = message_count
        self.current_time = None
        self.time_start = None
        self.answer_tokens = None
        self.answer_text = AnswerChatGPT.ERROR_TEXT
        self.prompt = [
            {
                'role': 'system',
                'content':
                    'Your name is Eva and you are an Russian experienced senior software developer with extensive experience leading '
                    'teams, mentoring junior developers, and delivering high-quality software solutions to customers.'
                    'The primary language is Russian.'
            }
        ]
        self.message_tokens = None
        self.set_windows_time()

    @classmethod
    async def num_tokens_from_message(cls, message):
        try:
            encoding = tiktoken.encoding_for_model(AnswerChatGPT.MODEL)
        except KeyError:
            encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(message)) + 4

    async def get_answer_from_ai(self) -> dict:
        """Основная логика."""

        if await self.check_in_works():
            return None

        self.message_tokens = await self.num_tokens_from_message(self.message_text)

        if self.check_long_query:
            response_message = f'{self.user}, у Вас слишком большой текст запроса. Попробуйте сформулировать его короче.'
            await self.send_chat_message(response_message)
            return 'Done'

        try:
            await self.get_prompt()
            await self.httpx_request_to_openai()

        except Exception as err:
            bot.send_message(
                chat_id=ADMIN_ID,
                text=f'Ошибка в получении ответа от ChatGPT: {str(err)[:1024]}',
            )
        finally:
            if not self.user.is_authenticated and self.message_count == 1:
                welcome_text = (
                    'Дорогой друг! '
                    'После регистрации и авторизации для тебя будет доступен режим диалога с ИИ Ева, а не просто ответ на вопрос как ниже.'
                )
                await self.send_chat_message(welcome_text)

            await self.send_chat_message(self.answer_text)
            await self.create_history_ai()
            await self.del_mess_in_redis()

    async def request_to_openai(self) -> None:
        """Делает обычный запрос в OpenAI."""
        client = AsyncOpenAI(
            api_key=settings.CHAT_GPT_TOKEN,
            timeout=300,
        )
        completion = await client.chat.completions.create(
            model=AnswerChatGPT.MODEL,
            messages=self.prompt,
            temperature=0.1,
        )
        self.answer_text = completion.choices[0].message.content
        self.answer_tokens = completion.usage.completion_tokens
        self.message_tokens = completion.usage.prompt_tokens

    async def httpx_request_to_openai(self) -> None:
        """Делает запрос в OpenAI через прокси."""
        transport = AsyncProxyTransport.from_url(settings.SOCKS5)
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings.CHAT_GPT_TOKEN}"
        }
        data = {
            "model": self.MODEL,
            "messages": self.prompt,
            "temperature": 0.1
        }
        async with httpx.AsyncClient(transport=transport) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=60 * self.MAX_TYPING_TIME,
            )
            completion = json.loads(response.content)
            self.answer_text = completion.get('choices')[0]['message']['content']
            self.answer_tokens = completion.get('usage')['completion_tokens']
            self.message_tokens = completion.get('usage')['prompt_tokens']

    async def send_chat_message(self, message):
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat.message',
                'message': markdown.markdown(message, extensions=['fenced_code']),
                'username': 'Eva',
            }
        )

    @database_sync_to_async
    def get_prompt(self) -> None:
        """Prompt для запроса в OpenAI и модель user."""
        if self.user.is_authenticated:
            history = (
                self.user
                .history_ai
                .filter(created_at__range=[self.time_start, self.current_time])
                .exclude(answer__isnull=True)
                .values('question', 'question_tokens', 'answer', 'answer_tokens')
            )
            max_tokens = self.message_tokens + 120
            for item in history:
                max_tokens += item['question_tokens'] + item['answer_tokens']
                if max_tokens >= AnswerChatGPT.MAX_LONG_REQUEST:
                    break
                self.prompt.extend([
                    {
                        'role': 'user',
                        'content': item['question']
                    },
                    {
                        'role': 'assistant',
                        'content': item['answer']
                    }
                ])
        self.prompt.append({'role': 'user', 'content': self.message_text})

    @sync_to_async
    def check_in_works(self) -> bool:
        """Проверяет нет ли уже в работе этого запроса в Redis."""
        queries = redis_client.lrange(f'gpt_:{self.room_group_name}', 0, -1)
        if self.message_text.encode('utf-8') in queries:
            return True
        redis_client.lpush(f'gpt_:{self.room_group_name}', self.message_text)
        return False

    @sync_to_async
    def del_mess_in_redis(self) -> bool:
        """Удаляет входящее сообщение из Redis."""
        redis_client.lrem(f'gpt_:{self.room_group_name}', 1, self.message_text.encode('utf-8'))

    async def create_history_ai(self):
        """Создаём запись в БД."""
        instance = HistoryAI(
            user=self.user if self.user.is_authenticated else None,
            room_group_name=self.room_group_name if self.room_group_name else None,
            question=self.message_text,
            question_tokens=self.message_tokens,
            answer=self.answer_text,
            answer_tokens=self.answer_tokens
        )
        await instance.save()

    async def set_windows_time(self) -> None:
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

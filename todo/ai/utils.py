import asyncio
import json
import traceback
from datetime import timedelta

import httpx
import markdown
import tiktoken_async
from asgiref.sync import sync_to_async
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Model
from django.utils.timezone import now
from httpx_socks import AsyncProxyTransport
from openai import AsyncOpenAI
from telbot.loader import bot
from telbot.models import GptModels, HistoryAI

ADMIN_ID = settings.TELEGRAM_ADMIN_ID
User = get_user_model()
redis_client = settings.REDIS_CLIENT


class AnswerChatGPT():
    ERROR_TEXT = (
        'Что-то пошло не так 🤷🏼\n'
        'Возможно большой наплыв запросов, которые я не успеваю обрабатывать 🤯'
    )
    STORY_WINDOWS_TIME = 30
    MAX_TYPING_TIME = 3

    def __init__(self, channel_layer: AsyncWebsocketConsumer, room_group_name: str, user: Model, message: str, message_count: int) -> None:
        self.channel_layer = channel_layer
        self.room_group_name = room_group_name
        self.message_text = message
        self.user = user
        self.message_count = message_count
        self.current_time = now()
        self.time_start = None
        self.answer_tokens = None
        self.answer_text = AnswerChatGPT.ERROR_TEXT
        self.model = None
        self.prompt = self.init_prompt()
        self.message_tokens = None
        self.set_windows_time()

    async def get_answer_from_ai(self) -> dict:
        """Основная логика."""

        if await self.check_in_works():
            return None

        await self.get_model_async()

        await self.num_tokens_from_message()

        if self.check_long_query:
            response_message = f'{self.user}, у Вас слишком большой текст запроса. Попробуйте сформулировать его короче.'
            await self.send_chat_message(response_message)
            return None

        try:
            await self.get_prompt()
            await self.httpx_request_to_openai()

        except Exception as err:
            traceback_str = traceback.format_exc()
            text = f'{str(err)[:1024]}\n\nТрассировка:\n{traceback_str[-1024:]}'
            await self.handle_error(text)
        finally:
            if not self.user.is_authenticated and self.message_count == 1:
                welcome_text = (
                    'Дорогой друг! '
                    'После регистрации и авторизации для тебя будет доступен режим диалога с ИИ Ева, а не просто ответ на вопрос как ниже.'
                )
                await self.send_chat_message(welcome_text)

            await self.send_chat_message(self.answer_text)
            await asyncio.gather(self.create_history_ai(), self.del_mess_in_redis())

    async def request_to_openai(self) -> None:
        """Делает запрос в OpenAI и выключает typing."""
        client = AsyncOpenAI(
            api_key=self.model.token,
            timeout=300,
        )
        completion = await client.chat.completions.create(
            model=self.model.title,
            messages=self.prompt,
            temperature=0.1
        )
        self.answer_text = completion.choices[0].message.content
        self.answer_tokens = completion.usage.completion_tokens
        self.message_tokens = completion.usage.prompt_tokens

    async def httpx_request_to_openai(self) -> None:
        """Делает запрос в OpenAI и выключает typing."""
        transport = AsyncProxyTransport.from_url(settings.SOCKS5)
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.model.token}"
        }
        data = {
            "model": self.model.title,
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
            try:
                self.answer_text = completion.get('choices')[0]['message']['content']
                self.answer_tokens = completion.get('usage')['completion_tokens']
                self.message_tokens = completion.get('usage')['prompt_tokens']
            except Exception as error:
                self.answer_text = 'Я отказываюсь отвечать на этот вопрос!'
                raise error

    async def send_chat_message(self, message):
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat.message',
                'message': markdown.markdown(message, extensions=['fenced_code']),
                'username': 'Eva',
            }
        )

    async def handle_error(self, err):
        """Логирование ошибок."""
        error_message = f"Ошибка в блоке Сайт-ChatGPT:\n{err}"
        bot.send_message(ADMIN_ID, error_message)

    async def num_tokens_from_message(self):
        """Считает количество токенов в сообщении пользователя."""
        try:
            encoding = await tiktoken_async.encoding_for_model(self.model.title)
        except KeyError:
            encoding = await tiktoken_async.get_encoding("cl100k_base")
        self.message_tokens = len(encoding.encode(self.message_text)) + 4

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
        self.time_start = self.current_time - timedelta(minutes=AnswerChatGPT.STORY_WINDOWS_TIME)

    async def get_model_async(self):
        if self.user.is_authenticated:
            self.model = await self._get_user_active_model()
        if not self.model:
            self.model = await self._get_default_model()

    @database_sync_to_async
    def _get_user_active_model(self):
        try:
            return self.user.approved_models.active_model
        except Exception:
            return None

    @staticmethod
    @database_sync_to_async
    def _get_default_model():
        return GptModels.objects.filter(default=True).first()

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
                max_tokens += sum(item.get(key, 0) for key in ('question_tokens', 'answer_tokens') if item.get(key) is not None)
                if max_tokens >= self.model.context_window:
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

    @property
    def check_long_query(self) -> bool:
        return self.message_tokens and self.model and self.message_tokens > self.model.max_request_token

    def init_prompt(self):
        return [
            {
                'role': 'system',
                'content':
                    """
                    You are named Eva, an experienced senior software developer with a strong background in team leadership,
                    mentoring all developers, and delivering high-quality software solutions to clients.
                    Your primary language is Russian.
                    """
            },
            {'role': 'user', 'content': self.message_text}
        ]


def convert_markdown(text: str) -> str:
    """
    Конвертирует теги Markdown в HTML-теги

    ### Args:
    - text (str): Входной текст для конвертации.

    ### Return:
    - (str): Текст с замененными тегами
    """

    return markdown.markdown(text, extensions=['fenced_code'])

import asyncio
import json
import traceback
from datetime import datetime, timedelta

import httpx
import telegram
import tiktoken_async
from asgiref.sync import sync_to_async
from channels.db import database_sync_to_async
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Model
from django.utils.timezone import now
from httpx_socks import AsyncProxyTransport
from openai import AsyncOpenAI
from telegram import ChatAction, ParseMode, Update
from telegram.ext import CallbackContext

from ..models import HistoryAI, UserGptModels

ADMIN_ID = settings.TELEGRAM_ADMIN_ID

User = get_user_model()
redis_client = settings.REDIS_CLIENT


class GetAnswerGPT():
    ERROR_TEXT = 'Что-то пошло не так 🤷🏼\n' 'Возможно большой наплыв запросов, которые я не успеваю обрабатывать 🤯'
    MAX_TYPING_TIME = 3

    def __init__(self, update: Update, context: CallbackContext, user: Model) -> None:
        self.update = update
        self.context = context
        self.user = user
        self.message_text = update.effective_message.text
        self.message_tokens = None
        self.current_time = now()
        self.time_start = None
        self.answer_text = GetAnswerGPT.ERROR_TEXT
        self.answer_tokens = None
        self.event = asyncio.Event()
        self.request_massage = None
        self.model = None
        self.user_models = None
        self.prompt = self.init_prompt()

    @property
    def check_long_query(self) -> bool:
        return self.message_tokens > self.model.max_request_token

    async def get_answer_chat_gpt(self) -> dict:
        """Основная логика."""

        if await self.check_in_works():
            return {'code': 423}

        await self.init_user_model()
        await self.num_tokens_from_message()

        if self.check_long_query:
            self.answer_text = f'{self.user.first_name}, слишком большой текст запроса. Попробуйте сформулировать его короче.'
            await self.reply_to_user()
            return {'code': 400}

        try:
            asyncio.create_task(self.send_typing_periodically())
            await self.get_prompt()
            await self.httpx_request_to_openai()

        except Exception as err:
            traceback_str = traceback.format_exc()
            text = f'{str(err)[:1024]}\n\nТрассировка:\n{traceback_str[-1024:]}'
            await self.handle_error(text)
        finally:
            asyncio.create_task(self.create_history_ai())
            await self.reply_to_user()
            await self.del_mess_in_redis()

    async def send_typing_periodically(self) -> None:
        """"Передаёт TYPING в чат Телеграм откуда пришёл запрос."""
        time_stop = datetime.now() + timedelta(minutes=GetAnswerGPT.MAX_TYPING_TIME)

        while not self.event.is_set():
            self.context.bot.send_chat_action(
                chat_id=self.update.effective_chat.id,
                action=ChatAction.TYPING
            )
            await asyncio.sleep(2)
            if datetime.now() > time_stop:
                break

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
        self.event.set()

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
            "temperature": 0.2
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
            finally:
                self.event.set()

    async def create_history_ai(self):
        """Создаём запись истории в БД."""
        self.request_massage = HistoryAI(
            user=self.user,
            question=self.message_text,
            question_tokens=self.message_tokens,
            answer=self.answer_text,
            answer_tokens=self.answer_tokens
        )
        await self.request_massage.save()

    async def num_tokens_from_message(self):
        """Считает количество токенов в сообщении пользователя."""
        try:
            encoding = await tiktoken_async.encoding_for_model(self.model.title)
        except KeyError:
            encoding = await tiktoken_async.get_encoding("cl100k_base")
        self.message_tokens = len(encoding.encode(self.message_text)) + 4

    @database_sync_to_async
    def init_user_model(self):
        """Инициация активной модели юзера и начального времени истории в prompt для запроса."""
        self.user_models, created = UserGptModels.objects.get_or_create(user=self.user, defaults={'time_start': self.current_time})
        self.model = self.user_models.active_model
        if not created:
            self.time_start = max(self.current_time - timedelta(minutes=self.model.time_window if self.model else 0), self.user_models.time_start)
        else:
            self.time_start = self.current_time

    @database_sync_to_async
    def get_prompt(self) -> None:
        """Prompt для запроса в OpenAI и модель user."""
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

    async def handle_error(self, err):
        """Логирование ошибок."""
        error_message = f"Ошибка в блоке Telegram-ChatGPT:\n{err}"
        self.context.bot.send_message(ADMIN_ID, error_message)

    @sync_to_async
    def reply_to_user(self) -> None:
        """Отправляет ответ пользователю."""
        try:
            self.context.bot.send_message(
                chat_id=self.update.effective_chat.id,
                text=self.answer_text,
                reply_to_message_id=self.update.message.message_id,
                parse_mode=ParseMode.MARKDOWN
            )
        except telegram.error.BadRequest:
            self.context.bot.send_message(
                chat_id=self.update.effective_chat.id,
                text=self.answer_text,
                reply_to_message_id=self.update.message.message_id,
            )
        except Exception as error:
            self.handle_error(error)

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

    def init_prompt(self):
        return [
            {
                'role': 'system',
                'content':
                    'Your name is Eva and you are experienced senior software developer with extensive experience leading '
                    'teams, mentoring all developers, and delivering high-quality software solutions to customers. '
                    'The primary language is Russian. Only this Markdown format can be used in text formatting:'
                    '*bold text* _italic text_ [inline URL](http://www.example.com/) '
                    '`inline fixed-width code` ``` pre-formatted fixed-width code block ```'
            }
        ]

import asyncio
import json
from datetime import datetime, timedelta

import httpx
import tiktoken_async
from ai.gpt_exception import (InWorkError, LongQueryError,
                              OpenAIConnectionError, OpenAIJSONDecodeError,
                              OpenAIResponseError, UnhandledError,
                              ValueChoicesError, handle_exceptions)
from asgiref.sync import sync_to_async
from channels.db import database_sync_to_async
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Model
from django.utils.timezone import now
from httpx_socks import AsyncProxyTransport
from telbot.loader import bot
from telbot.models import GptModels, UserGptModels
from telegram import ChatAction

ADMIN_ID = settings.TELEGRAM_ADMIN_ID

User = get_user_model()
redis_client = settings.REDIS_CLIENT


class GetAnswerGPT():
    """
    Класс для получения ответов от модели GPT.

    ### Args:
    - query_text (`str`): Текст запроса пользователя.
    - assist_prompt (`str`): Промпт для ассистента в head модели.
    - user (`Model`): Пользователь.
    - history_model (`Model`): Модель для хранения истории.
    - chat_id (`int`, optional): ID чата. Defaults to None.

    """
    MAX_TYPING_TIME = 3

    def __init__(self, query_text: str, assist_prompt: str, user: 'Model', history_model: 'Model', chat_id: int = None, creativity_controls: dict = {}) -> None:
        # Инициализация свойств класса
        self.user = user                    # модель пользователя пославшего запрос
        self.is_user_authenticated = self.user.is_authenticated  # гость или аутентифицированный пользователь
        self.history_model = history_model  # модель для хранения истории
        self.query_text = query_text        # текст запроса пользователя
        self.assist_prompt = assist_prompt  # промпт для ассистента в head модели
        self.query_text_tokens = None       # количество токенов в запросе
        self.chat_id = chat_id              # id чата в котором инициировать typing
        self.creativity_controls = creativity_controls      # параметры которые контролируют креативность и разнообразие текста
        # Дополнительные свойства
        self.assist_prompt_tokens = 0       # количество токенов в промпте ассистента в head модели
        self.all_prompt = []                # общий промпт для запроса
        self.current_time = now()           # текущее время для окна истории
        self.return_text = ''               # текст полученный в ответе от модели
        self.return_text_tokens = None      # количество токенов в ответе
        self.event = asyncio.Event() if chat_id else None  # typing в чат пользователя
        self.user_models = None             # разрешенные GPT модели пользователя

    @property
    def check_long_query(self) -> bool:
        return self.query_text_tokens > self.model.max_request_token

    async def get_answer_chat_gpt(self) -> dict:
        """Основная логика."""
        await self.init_user_model()
        self.query_text_tokens, self.assist_prompt_tokens, _ = await asyncio.gather(
            self.num_tokens(self.query_text, 4),
            self.num_tokens(self.assist_prompt, 7),
            self.check_in_works(),
        )
        if self.check_long_query:
            raise LongQueryError(
                f'{self.user.first_name if self.is_user_authenticated else "Дорогой друг" }, слишком большой текст запроса.\n'
                'Попробуйте сформулировать его короче.'
            )
        try:
            if self.event:
                asyncio.create_task(self.send_typing_periodically())
            await self.get_prompt()
            await self.httpx_request_to_openai()
            if self.is_user_authenticated:
                asyncio.create_task(self.create_history_ai())
        except Exception as err:
            _, type_err, traceback_str = await handle_exceptions(err, True)
            raise type_err(f'\n\n{str(err)}{traceback_str}')
        finally:
            await self.del_mess_in_redis()

    async def send_typing_periodically(self) -> None:
        """"Передаёт TYPING в чат Телеграм откуда пришёл запрос."""
        time_stop = datetime.now() + timedelta(minutes=self.MAX_TYPING_TIME)
        while not self.event.is_set():
            bot.send_chat_action(chat_id=self.chat_id, action=ChatAction.TYPING)
            await asyncio.sleep(2)
            if datetime.now() > time_stop:
                break

    async def httpx_request_to_openai(self) -> None:
        """Делает запрос в OpenAI и выключает typing."""
        transport = AsyncProxyTransport.from_url(settings.SOCKS5)
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.model.token}"
        }
        data = {
            "model": self.model.title,
            "messages": self.all_prompt,
        }
        data.update(self.creativity_controls)
        try:
            async with httpx.AsyncClient(transport=transport) as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers=headers,
                    json=data,
                    timeout=60 * self.MAX_TYPING_TIME,
                )
                response.raise_for_status()
                completion = response.json()
                choices = completion.get('choices')
                if choices and len(choices) > 0:
                    first_choice = choices[0]
                    self.return_text = first_choice['message']['content']
                    self.return_text_tokens = completion.get('usage', {}).get('completion_tokens')
                    self.query_text_tokens = completion.get('usage', {}).get('prompt_tokens')
                else:
                    raise ValueChoicesError(f"`GetAnswerGPT`, ответ не содержит полей 'choices': {json.dumps(completion, ensure_ascii=False, indent=4)}")

        except httpx.HTTPStatusError as http_err:
            raise OpenAIResponseError(f'`GetAnswerGPT`, ответ сервера был получен, но код состояния указывает на ошибку: {http_err}') from http_err
        except httpx.RequestError as req_err:
            raise OpenAIConnectionError(f'`GetAnswerGPT`, проблемы соединения: {req_err}') from req_err
        except json.JSONDecodeError:
            raise OpenAIJSONDecodeError('`GetAnswerGPT`, ошибка при десериализации JSON.')
        except Exception as error:
            raise UnhandledError(f'Необработанная ошибка в `GetAnswerGPT.httpx_request_to_openai()`: {error}') from error
        finally:
            if self.event:
                self.event.set()

    async def create_history_ai(self):
        """Создаём запись истории в БД для моделей поддерживающих асинхронное сохранение."""
        self.history_instance = self.history_model(
            user=self.user,
            question=self.query_text,
            question_tokens=self.query_text_tokens,
            answer=self.return_text,
            answer_tokens=self.return_text_tokens
        )
        await sync_to_async(self.history_instance.save)()

    async def num_tokens(self, text: str, corr_token: int = 0) -> int:
        """Считает количество токенов.
        ## Args:
        - text (`str`): текс для которого возвращается количество
        - corr_token (`int`): количество токенов для ролей и разделителей

        """
        try:
            encoding = await tiktoken_async.encoding_for_model(self.model.title)
        except KeyError:
            encoding = await tiktoken_async.get_encoding("cl100k_base")
        return len(encoding.encode(text)) + corr_token

    async def add_to_prompt(self, role: str, content: str) -> None:
        """Добавляет элемент в список all_prompt."""
        self.all_prompt.append({'role': role, 'content': content})

    async def get_prompt(self) -> None:
        """Prompt для запроса в OpenAI и модель user."""
        history = []
        await self.add_to_prompt('system', self.assist_prompt)
        if self.is_user_authenticated:
            history = await sync_to_async(list)(self.history_model.objects.filter(
                user=self.user,
                created_at__range=[self.time_start, self.current_time]
            ).exclude(
                answer__isnull=True
            ).values(
                'question', 'question_tokens', 'answer', 'answer_tokens'
            ))
        token_counter = self.query_text_tokens + self.assist_prompt_tokens
        for item in history:
            question_tokens = item.get('question_tokens', 0)
            answer_tokens = item.get('answer_tokens', 0)
            # +11 - токены для ролей и разделителей: 'system' - 7 'user' - 4
            token_counter += question_tokens + answer_tokens + 11

            if token_counter >= self.model.context_window:
                break

            await self.add_to_prompt('user', item['question'])
            await self.add_to_prompt('assistant', item['answer'])

        await self.add_to_prompt('user', self.query_text)

    @database_sync_to_async
    def init_user_model(self):
        """Инициация активной модели юзера и начального времени истории в prompt для запроса."""
        if self.is_user_authenticated:
            self.user_models, created = UserGptModels.objects.get_or_create(user=self.user, defaults={'time_start': self.current_time})
            self.model = self.user_models.active_model
            if not created and self.model:
                time_window = timedelta(minutes=self.model.time_window)
                self.time_start = max(self.current_time - time_window, self.user_models.time_start)
            else:
                self.time_start = self.current_time
        else:
            self.model = GptModels.objects.filter(default=True).first()

    @sync_to_async
    def check_in_works(self) -> bool:
        """Проверяет нет ли уже в работе этого запроса в Redis и добавляет в противном случае."""
        queries = redis_client.lrange(f'gpt_user:{self.user.id}', 0, -1)
        if self.query_text.encode('utf-8') in queries:
            raise InWorkError('Запрос уже находится в работе.')
        redis_client.lpush(f'gpt_user:{self.user.id}', self.query_text)

    @sync_to_async
    def del_mess_in_redis(self) -> None:
        """Удаляет входящее сообщение из Redis."""
        redis_client.lrem(f'gpt_user:{self.user.id}', 1, self.query_text.encode('utf-8'))

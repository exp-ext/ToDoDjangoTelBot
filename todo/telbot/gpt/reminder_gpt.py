import asyncio
import json
from datetime import datetime, timedelta

import httpx
from channels.db import database_sync_to_async
from django.conf import settings
from httpx_socks import AsyncProxyTransport
from telbot.loader import bot
from telbot.models import GptModels, ReminderAI
from telegram import ChatAction

ADMIN_ID = settings.TELEGRAM_ADMIN_ID


class ReminderGPT():
    MAX_TYPING_TIME = 3

    def __init__(self, text, user, chat_id) -> None:
        self.user = user
        self.text = text
        self.chat_id = chat_id
        self.model = None
        self.prompt = None
        self.answer_text = None
        self.event = asyncio.Event()

    async def transform(self) -> None:
        try:
            asyncio.create_task(self.send_typing_periodically())
            await asyncio.gather(
                self.get_default_model(),
                self.init_prompt()
            )
            await self.reminder_conversion_request()
            await self.create_reminder_history_ai()
        except Exception as error:
            raise RuntimeError(f'Ошибка в процессе трансформации `ReminderGPT`: {error}') from error
        return self.answer_text

    async def send_typing_periodically(self) -> None:
        """"Передаёт TYPING в чат Телеграм откуда пришёл запрос."""
        time_stop = datetime.now() + timedelta(minutes=self.MAX_TYPING_TIME)

        while not self.event.is_set():
            bot.send_chat_action(
                chat_id=self.chat_id,
                action=ChatAction.TYPING
            )
            await asyncio.sleep(2)
            if datetime.now() > time_stop:
                break

    async def reminder_conversion_request(self) -> None:
        """Делает запрос в OpenAI для преобразования текста напоминания."""
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
            response.raise_for_status()
            completion = json.loads(response.content)
            try:
                self.answer_text = completion.get('choices')[0]['message']['content']
                self.answer_tokens = completion.get('usage')['completion_tokens']
                self.message_tokens = completion.get('usage')['prompt_tokens']
            except httpx.HTTPStatusError as http_err:
                raise RuntimeError(f'Ответ сервера был получен, но код состояния указывает на ошибку: {http_err}') from http_err
            except httpx.RequestError as req_err:
                raise RuntimeError(f'Проблемы соединения: {req_err}') from req_err
            except KeyError as key_err:
                raise ValueError(f'Отсутствие ожидаемых ключей в ответе: {key_err}') from key_err
            except Exception as error:
                raise RuntimeError(f'Необработанная ошибка в `ReminderGPT.reminder_conversion_request()`: {error}') from error
            finally:
                self.event.set()

    async def create_reminder_history_ai(self):
        """Создаём запись истории в БД."""
        self.request_massage = ReminderAI(
            user=self.user,
            question=self.text,
            question_tokens=self.message_tokens,
            answer=self.answer_text,
            answer_tokens=self.answer_tokens
        )
        await self.request_massage.save()

    @database_sync_to_async
    def get_default_model(self) -> None:
        self.model = GptModels.objects.filter(default=True).first()

    @database_sync_to_async
    def init_prompt(self) -> None:
        prompt_content = """
        ЧатGPT, я прошу Вас преобразовать следующий текст в формат:
        «дата {числовой формат} время {числовой формат}
        | количество минут за сколько оповестить до наступления дата+время {по умолчанию: 120}
        | повтор напоминания {по умолчанию: N, каждый день: D, каждую неделю: W, каждый месяц: M, каждый год: Y}
        | тело напоминания {исправить ошибки}».
        Ответ для примера: «20.11.2025 17:35|30|N|Запись к врачу»
        """
        self.prompt = [
            {'role': 'system', 'content': prompt_content},
            {'role': 'user', 'content': self.text}
        ]

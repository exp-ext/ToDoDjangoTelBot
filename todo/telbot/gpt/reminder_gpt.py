import asyncio
import json
import traceback

import httpx
from channels.db import database_sync_to_async
from django.conf import settings
from httpx_socks import AsyncProxyTransport
from telbot.models import GptModels, ReminderAI
from telbot.service_message import send_message_to_chat

ADMIN_ID = settings.TELEGRAM_ADMIN_ID


class ReminderGPT():
    MAX_TYPING_TIME = 3

    def __init__(self, text, user) -> None:
        self.user = user
        self.text = text
        self.model = None
        self.prompt = None

    async def transform(self) -> None:
        try:
            await asyncio.gather(
                self.get_default_model(),
                self.init_prompt()
            )
            await self.reminder_conversion_request()
            await self.create_reminder_history_ai()
        except Exception as err:
            await self.handle_user_error()
            traceback_str = traceback.format_exc()
            text = f'{str(err)[:1024]}\n\nТрассировка:\n{traceback_str[-1024:]}'
            await self.handle_error(text)
        return self.answer_text

    async def handle_error(self, err):
        """Логирование ошибок."""
        error_message = f"Ошибка в блоке ReminderGPT:\n{err}"
        send_message_to_chat(tg_id=ADMIN_ID, message=error_message)

    async def handle_user_error(self):
        """Логирование ошибок."""
        error_message = "Произошла ошибка, попробуйте позже."
        send_message_to_chat(tg_id=self.user.tg_id, message=error_message)

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
            completion = json.loads(response.content)
            try:
                self.answer_text = completion.get('choices')[0]['message']['content']
                self.answer_tokens = completion.get('usage')['completion_tokens']
                self.message_tokens = completion.get('usage')['prompt_tokens']
            except Exception as error:
                self.answer_text = 'Я отказываюсь отвечать на этот вопрос!'
                raise error

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

    async def init_prompt(self) -> None:
        self.prompt = [
            {
                'role': 'system',
                'content':
                    """
                    ЧатGPT, я прошу вас преобразовать следующий текст в формат
                    «дата время тело напоминания | количество минут за сколько оповестить до события {'по умолчанию': 120} & повтор напоминания
                    {по умолчанию': 'N', 'каждый день': 'D', 'каждую неделю': 'W', 'каждый месяц': 'M', 'каждый год': 'Y'}»,
                    используя язык на котором пришёл текст запроса.
                    Ответ для примера: «20.11.2025 17:35 Запись к врачу | 30 & N»
                    """
            },
            {'role': 'user', 'content': self.text}
        ]

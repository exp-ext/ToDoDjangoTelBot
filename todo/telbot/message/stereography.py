import asyncio
import json
import traceback
from datetime import datetime, timedelta, timezone

import httpx
from asgiref.sync import sync_to_async
from channels.db import database_sync_to_async
from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import HttpResponseBadRequest
from telbot.external_api.chat_gpt import GetAnswerGPT
from telegram import ChatAction, Update
from telegram.ext import CallbackContext

from ..checking import check_registration
from ..models import HistoryWhisper

User = get_user_model()
ADMIN_ID = settings.TELEGRAM_ADMIN_ID
redis_client = settings.REDIS_CLIENT


class AudioTranscription():
    """
    Отправляет в чат ответом на сообщение транскрибацию речи,
    порученную от АПИ openai-whisper-asr-webservice.
    """
    ERROR_TEXT = 'Что-то пошло не так 🤷🏼'
    STORY_WINDOWS_TIME = 11
    MAX_TYPING_TIME = 10
    url = 'http://127.0.0.1:9009/asr' if settings.DEBUG else 'http://whisper:9000/asr'
    params = {
        'task': 'transcribe',
        'language': 'ru',
        'output': 'json',
    }
    headers = {'accept': 'application/json'}

    def __init__(self, update: Update, context: CallbackContext, user: User) -> None:
        self.update = update
        self.context = context
        self.file_id = update.message.voice.file_id
        self.user = user
        self.current_time = None
        self.time_start = None
        self.transcription_text = None
        self.event = asyncio.Event()
        self.set_windows_time()

    async def get_audio_transcription(self) -> dict:
        """Основная логика."""
        if await self.check_in_works():
            return {'code': 423}

        try:
            asyncio.create_task(self.send_typing_periodically())
            await self.request_to_whisper()
            asyncio.create_task(self.create_history_whisper())

        except Exception as err:
            traceback_str = traceback.format_exc()
            self.context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f'Ошибка в Whisper: {str(err)[:1024]}\n\nТрассировка:\n{traceback_str[-1024:]}',
            )
            self.transcription_text = AudioTranscription.ERROR_TEXT
        finally:
            if any(word in self.transcription_text.lower() for word in ['вопрос', '?']):
                self.transcription_text = f'Ищю ответ на: {self.transcription_text}'
                self.update.effective_message.text = self.transcription_text
                asyncio.create_task(self.send_reply())
                get_answer = GetAnswerGPT(self.update, self.context, self.user)
                await get_answer.get_answer_davinci()
            else:
                await self.send_reply()

    async def send_reply(self) -> None:
        """Отправляет транскрипцию пользователю."""
        self.context.bot.send_message(
            chat_id=self.update.effective_chat.id,
            text=self.transcription_text,
            reply_to_message_id=self.update.message.message_id
        )

    async def send_typing_periodically(self) -> None:
        """"
        Передаёт TYPING в чат Телеграм откуда пришёл запрос.
        """
        time_stop = datetime.now() + timedelta(minutes=AudioTranscription.MAX_TYPING_TIME)
        while not self.event.is_set():
            self.context.bot.send_chat_action(
                chat_id=self.update.effective_chat.id,
                action=ChatAction.TYPING
            )
            await asyncio.sleep(3)
            if datetime.now() > time_stop:
                break

    async def request_to_whisper(self) -> None:
        """ Делает запрос в API whisper и выключает typing."""
        audio = self.context.bot.get_file(self.file_id)

        async with httpx.AsyncClient() as client:
            response = await client.get(audio.file_path)

            if response.status_code != 200:
                raise HttpResponseBadRequest("Bad Request")

            files = [('audio_file', ('audio.ogg', response.content, 'audio/ogg'))]
            response = await client.post(
                url=self.url,
                headers=self.headers,
                params=self.params,
                files=files
            )
            self.transcription_text = json.loads(response.content)['text']
            self.event.set()

    @database_sync_to_async
    def create_history_whisper(self):
        """Создаём запись в БД."""
        HistoryWhisper.objects.update(
            user=self.user,
            file_id=self.file_id,
            transcription=self.transcription_text
        )

    @sync_to_async
    def check_in_works(self) -> bool:
        """Проверяет нет ли уже в работе этого запроса в Redis."""
        queries = redis_client.lrange(f'whisper_user:{self.user.id}', 0, -1)
        if self.file_id.encode('utf-8') in queries:
            return True
        redis_client.lpush(f'whisper_user:{self.user.id}', self.file_id)
        return False

    def set_windows_time(self) -> None:
        """Определяем и назначаем атрибуты current_time и time_start."""
        self.current_time = datetime.now(timezone.utc)
        self.time_start = self.current_time - timedelta(minutes=AudioTranscription.STORY_WINDOWS_TIME)


def send_audio_transcription(update: Update, context: CallbackContext):
    answers_for_check = {'': f'Сделаю транскрибацию, если [зарегистрируетесь]({context.bot.link}).'}
    allow_unregistered = True
    return_user = True
    user = check_registration(update, context, answers_for_check, allow_unregistered, return_user)
    if not user:
        return {'code': 401}
    instance = AudioTranscription(update, context, user)
    asyncio.run(instance.get_audio_transcription())

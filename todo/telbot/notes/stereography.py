import asyncio
import json
import traceback
from datetime import datetime, timedelta

import httpx
from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import HttpResponseBadRequest
from telbot.gpt.chat_distributor import check_request_in_distributor
from telbot.service_message import send_message_to_chat, send_service_message
from telegram import ChatAction, Update
from telegram.ext import CallbackContext

User = get_user_model()
ADMIN_ID = settings.TELEGRAM_ADMIN_ID


class AudioTranscription():
    """
    Отправляет в чат ответом на сообщение транскрибацию речи,
    порученную от АПИ openai-whisper-asr-webservice.
    """
    MAX_TYPING_TIME = 10
    url = 'http://127.0.0.1:9009/asr' if settings.DEBUG else 'http://whisper:9000/asr'
    params = {
        'task': 'transcribe',
        'language': 'ru',
        'output': 'json',
    }
    headers = {'accept': 'application/json'}

    def __init__(self, update: Update, context: CallbackContext) -> None:
        self.update = update
        self.context = context
        self.file_id = update.message.voice.file_id
        self.transcription_text = None
        self.event = asyncio.Event()

    async def get_audio_transcription(self) -> dict:
        """Основная логика."""
        try:
            asyncio.create_task(self.send_typing_periodically())
            await self.request_to_whisper()

            if self.transcription_text:
                self.update.effective_message.text = self.transcription_text
                await check_request_in_distributor(self.update, self.context)

        except Exception as err:
            traceback_str = traceback.format_exc()
            text = f'Ошибка в Whisper: {str(err)[:1024]}\n\nТрассировка:\n{traceback_str[-1024:]}'
            send_message_to_chat(ADMIN_ID, text)
            text = 'Не получилось разобрать, что Вы сказали. Попробуйте более четко и медленнее.'
            send_service_message(self.update.effective_chat.id, text)

    async def send_typing_periodically(self) -> None:
        """"
        Передаёт TYPING в чат Телеграм откуда пришёл запрос.
        """
        time_stop = datetime.now() + timedelta(minutes=self.MAX_TYPING_TIME)
        while not self.event.is_set():
            self.context.bot.send_chat_action(
                chat_id=self.update.effective_chat.id,
                action=ChatAction.UPLOAD_VOICE
            )
            await asyncio.sleep(3)
            if datetime.now() > time_stop:
                break

    async def request_to_whisper(self) -> None:
        """ Делает запрос в API whisper и выключает typing."""
        audio = self.context.bot.get_file(self.file_id)
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(audio.file_path)

                if response.status_code != 200:
                    raise HttpResponseBadRequest("Bad Request to Wisper")

                files = [('audio_file', ('audio.ogg', response.content, 'audio/ogg'))]
                response = await client.post(
                    url=self.url,
                    headers=self.headers,
                    params=self.params,
                    files=files
                )
            self.transcription_text = json.loads(response.content)['text']
            if self.transcription_text == '':
                raise 'Текст после транскрибации пуст!'
        except Exception as error:
            raise error
        finally:
            self.event.set()


def send_audio_transcription(update: Update, context: CallbackContext):
    instance = AudioTranscription(update, context)
    asyncio.run(instance.get_audio_transcription())

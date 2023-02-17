import io
import json
from urllib.request import urlopen

import requests
import soundfile as sf
from django.conf import settings
from django.http import HttpResponseBadRequest
from telegram import Update
from telegram.ext import CallbackContext


def convert_ogg_to_wav(file_path: str) -> bytes:
    """
    На входе получает :obj:`str` ссылку на аудиофайл.

    Возвращает :obj:`bytes` конвертированный в WAV формат.

    НЕ ИСПОЛЬЗУЕТСЯ!
    """
    data, samplerate = sf.read(io.BytesIO(urlopen(file_path).read()))
    buffer = io.BytesIO()
    sf.write(buffer, data, samplerate, format='WAV')
    return buffer.getvalue()


def send_audio_transcription(update: Update, context: CallbackContext) -> str:
    """
    Отправляет в чат ответом на сообщение аудиотранскрипцию речи,
    порученную от АПИ openai-whisper-asr-webservice.

    Для работы в режиме DEBAG необходимо запустить АПИ в контейнере:

    docker run -d -p 9000:9000 -e ASR_MODEL=small \
        onerahmet/openai-whisper-asr-webservice:latest
    """
    chat = update.effective_chat

    file_id = update.message.voice.file_id
    audio = context.bot.get_file(file_id)
    file_path = audio.file_path

    try:
        response = requests.get(file_path)
        if response.status_code != 200:
            return HttpResponseBadRequest("Bad Request")

        files = [
            ('audio_file', ('audio.ogg', response.content, 'audio/ogg'))
        ]

        # files = [
        #     (
        #         'audio_file',
        #         ('audio.wav', convert_ogg_to_wav(file_path), 'audio/wav')
        #     )
        # ]

        url = (
            'http://localhost:9000/asr'
            if settings.DEBUG else 'http://todo_whisper:9000/asr'
        )
        params = {
            'task': 'transcribe',
            'language': 'ru',
            'output': 'json',
        }
        headers = {
            'accept': 'application/json',
        }
        response = requests.post(
            url=url,
            headers=headers,
            params=params,
            files=files
        )
        response_dict = json.loads(response.content)
        context.bot.send_message(
            chat_id=chat.id,
            reply_to_message_id=update.message.message_id,
            text=response_dict['text']
        )
        return 'Send: Done'
    except Exception as error:
        raise ValueError("An error occurred: {}".format(str(error)))

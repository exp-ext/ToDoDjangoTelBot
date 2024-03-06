import asyncio
import os
from datetime import datetime, timedelta, timezone

import requests
from asgiref.sync import sync_to_async
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from dotenv import load_dotenv
from langdetect import detect
from telegram import ChatAction, Update
from telegram.ext import CallbackContext

from ..checking import check_registration
from ..models import HistoryTranslation

load_dotenv()

X_RAPID_API_KEY = os.getenv('X_RAPID_API_KEY')

TOKEN_TRANSLATION_API = os.getenv('TOKEN_TRANSLATION_API')

User = get_user_model()

ADMIN_ID = os.getenv('ADMIN_ID')


class GetTranslation():
    """
    Проверяет регистрацию.
    Делает запрос и в чат Telegram возвращает перевод сообщения.
    """
    ERROR_TEXT = (
        'Что-то пошло не так 🤷🏼\n'
        'Возможно большой наплыв запросов, '
        'которые я не успеваю обрабатывать 🤯'
    )
    STORY_WINDOWS_TIME = 11
    MAX_TYPING_TIME = 10

    def __init__(self,
                 update: Update,
                 context: CallbackContext) -> None:
        self.update = update
        self.context = context
        self.user = None
        self.message_text = None
        self.desired_language = None
        self.message_language = None
        self.current_time = None
        self.time_start = None
        self.answer_text = None
        self.event = asyncio.Event()
        self.set_user()
        self.set_message_text()
        self.set_windows_time()

    def get_translation(self) -> dict:
        """Основная логика."""
        if self.check_in_works():
            return {'code': 423}

        try:
            asyncio.run(self.get_answer())

            HistoryTranslation.objects.update(
                user=self.user,
                message=self.message_text,
                translation=self.answer_text.lstrip('\n')
            )
        except Exception as err:
            self.context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f'Ошибка в ChatGPT: {err}',
            )
            self.answer_text = GetTranslation.ERROR_TEXT
        finally:
            self.context.bot.send_message(
                chat_id=self.update.effective_chat.id,
                text=self.answer_text,
                reply_to_message_id=self.update.message.message_id
            )

    async def get_answer(self) -> None:
        """
        Асинхронно запускает 2 функции.
        """
        asyncio.create_task(self.send_typing_periodically())
        await sync_to_async(self.request_to)()

    async def send_typing_periodically(self) -> None:
        """"
        Передаёт TYPING в чат Телеграм откуда пришёл запрос.
        """
        time_stop = datetime.now() + timedelta(minutes=GetTranslation.MAX_TYPING_TIME)
        while not self.event.is_set():
            self.context.bot.send_chat_action(
                chat_id=self.update.effective_chat.id,
                action=ChatAction.TYPING
            )
            await asyncio.sleep(2)
            if datetime.now() > time_stop:
                break

    def request_to(self) -> None:
        """
        Делает запрос и выключает typing.
        """
        try:
            self.translate_translator()
        except Exception:
            self.deepl_translator()
        self.event.set()

    def translate_translator(self):
        """
        Возвращает перевод с API www.translate.com.
        """
        url = 'https://api.translate.com/translate/v1/mt'
        headers = {
            'Authorization': f'Bearer {TOKEN_TRANSLATION_API}',
        }
        payload = {
            'text': self.message_text,
            'source_language': self.message_language,
            'translation_language': self.desired_language
        }
        response = requests.post(
            url=url,
            headers=headers,
            json=payload
        )  # TODO переделать на HTTPX для сокращения библиотек
        self.answer_text = response.json().get('data').get('translation')

    def deepl_translator(self):
        """
        Возвращает перевод с API DeepL Translator.
        """
        url = 'https://deepl-translator1.p.rapidapi.com/translate'
        querystring = {
            'text': self.message_text,
            'target_lang': self.desired_language
        }
        headers = {
            'X-RapidAPI-Key': X_RAPID_API_KEY,
            'X-RapidAPI-Host': 'deepl-translator1.p.rapidapi.com'
        }
        response = requests.get(
            url=url,
            headers=headers,
            params=querystring
        )
        self.answer_text = response.json().get('translations')[0].get('text')

    def check_in_works(self) -> bool:
        """Проверяет нет ли уже в работе этого запроса."""
        if self.user.history_translation.filter(created_at__range=[self.time_start, self.current_time], message=self.message_text).exists():
            return True
        HistoryTranslation.objects.create(
            user=self.user,
            message=self.message_text,
            translation=self.answer_text
        )
        return False

    def set_user(self) -> None:
        """Определяем и назначаем  атрибут user."""
        self.user = get_object_or_404(
            User,
            username=self.update.effective_user.username
        )

    def set_message_text(self) -> str:
        """
        Определяем и назначаем атрибуты:
        message_text, desired_language, message_language.
        """
        text = tuple(
            x.strip() for x in self.update.message.text.split('->')
        )
        if len(text[1]) == 2:
            self.message_text = text[0]
            self.desired_language = text[1]
            self.message_language = detect(text[0])
            self.answer_text = GetTranslation.ERROR_TEXT
        else:
            self.answer_text = 'Не смог найти язык для перевода 🙃'

    def set_windows_time(self) -> None:
        """Определяем и назначаем атрибуты current_time и time_start."""
        self.current_time = datetime.now(timezone.utc)
        self.time_start = (
            self.current_time
            - timedelta(minutes=GetTranslation.STORY_WINDOWS_TIME)
        )


def send_translation(update: Update, context: CallbackContext):
    answers_for_check = {
        '': (f'К сожалению перевод доступен только для [зарегистрированных пользователей]({context.bot.link}).'),
    }
    if check_registration(update, context, answers_for_check) is False:
        return {'code': 401}
    GetTranslation(update, context).get_translation()

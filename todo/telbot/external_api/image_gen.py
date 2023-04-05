import asyncio
import os
from datetime import datetime, timedelta, timezone

import openai
from asgiref.sync import sync_to_async
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from dotenv import load_dotenv
from telegram import ChatAction, InputMediaPhoto, ParseMode, Update
from telegram.ext import CallbackContext, ConversationHandler

from ..checking import check_registration
from ..cleaner import remove_keyboard
from ..models import HistoryDALLE

load_dotenv()

APY_KEY = os.getenv('CHAT_GP_TOKEN')
openai.api_key = APY_KEY

ADMIN_ID = os.getenv('ADMIN_ID')

User = get_user_model()


class GetAnswerDallE():
    """
    Проверяет регистрацию.
    Делает запрос и в чат Telegram возвращает результат ответа
    от API ИИ Dall-E.
    """

    ERROR_TEXT = (
        'Что-то пошло не так 🤷🏼\n'
        'Возможно большой наплыв запросов, '
        'которые я не успеваю обрабатывать 🤯'
    )
    MAX_TYPING_TIME = 10
    STORY_WINDOWS_TIME = 15

    def __init__(self,
                 update: Update,
                 context: CallbackContext) -> None:
        self.update = update
        self.context = context
        self.current_time = None
        self.time_start = None
        self.chat_id = None
        self.message_text = None
        self.media_group = []
        self.event = asyncio.Event()
        self.set_message_text()
        self.set_chat_id()
        self.set_user()
        self.set_windows_time()

    def get_image_dall_e(self):
        """
        Возвращает серию картинок от АПИ Dall-e 2.
        Предварительно вызвав функцию проверки регистрации.
        """
        if self.check_in_works():
            return {'code': 423}

        answers = {
            '': ('К сожалению данная функция доступна только для '
                 '[зарегистрированных пользователей]'
                 f'({self.context.bot.link})'),
        }

        if check_registration(self.update, self.context, answers) is False:
            return {'code': 401}

        try:
            asyncio.run(self.get_answer())

            media_group_dict = [
                {'media': item.media, 'caption': item.caption}
                for item in self.media_group
            ]
            HistoryDALLE.objects.update(
                user=self.user,
                question=self.message_text,
                answer=media_group_dict
            )

        except Exception as err:
            self.context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f'Ошибка в Dall-E: {err}',
            )
        finally:
            self.context.bot.send_media_group(
                chat_id=self.chat_id,
                media=self.media_group,
                reply_to_message_id=self.update.message.message_id
            )

    async def get_answer(self) -> list:
        """
        Асинхронно запускает 2 функции.
        """
        asyncio.create_task(self.send_typing_periodically())
        await sync_to_async(self.request_to_openai)()

    async def send_typing_periodically(self) -> None:
        """"
        Передаёт TYPING в чат Телеграм откуда пришёл запрос.
        """
        time_stop = (
            datetime.now()
            + timedelta(minutes=GetAnswerDallE.MAX_TYPING_TIME)
        )
        while not self.event.is_set():
            self.context.bot.send_chat_action(
                chat_id=self.chat_id,
                action=ChatAction.UPLOAD_PHOTO
            )
            await asyncio.sleep(2)
            if datetime.now() > time_stop:
                break

    def request_to_openai(self) -> list:
        """
        Делает запрос в OpenAI.
        """
        response = openai.Image.create(
            prompt=self.message_text,
            n=5,
            size='1024x1024'
        )
        for number, url in enumerate(response['data']):
            self.media_group.append(
                InputMediaPhoto(media=url['url'], caption=f'Gen № {number}')
            )
        self.event.set()

    def set_message_text(self) -> str:
        """Определяем и назначаем атрибут message_text."""
        self.message_text = (
            self.update.effective_message.text
        )

    def set_chat_id(self) -> str:
        """Определяем и назначаем атрибут chat_id."""
        self.chat_id = (
            self.update.effective_chat.id
        )

    def set_user(self) -> None:
        """Определяем и назначаем  атрибут user."""
        self.user = get_object_or_404(
            User,
            username=self.update.effective_user.id
        )

    def set_windows_time(self) -> None:
        """Определяем и назначаем атрибуты current_time и time_start."""
        self.current_time = datetime.now(timezone.utc)
        self.time_start = (
            self.current_time
            - timedelta(minutes=GetAnswerDallE.STORY_WINDOWS_TIME)
        )

    def check_in_works(self) -> bool:
        """Проверяет нет ли уже в работе этого запроса."""
        if (self.user.history_dalle.filter(
                created_at__range=[self.time_start, self.current_time],
                question=self.message_text).exists()):
            return True
        HistoryDALLE.objects.create(
            user=self.user,
            question=self.message_text,
            answer=[GetAnswerDallE.ERROR_TEXT]
        )
        return False


def first_step_get_image(update: Update, context: CallbackContext):
    chat = update.effective_chat
    req_text = (
        f'*{update.effective_user.first_name}*, '
        'введите текст для генерации картинки на английском языке'
    )
    message_id = context.bot.send_message(
        chat.id,
        req_text,
        parse_mode=ParseMode.MARKDOWN
    ).message_id
    context.user_data['image_gen'] = message_id
    remove_keyboard(update, context)
    return 'image_gen'


def get_image_dall_e(update: Update, context: CallbackContext):
    """
    Удаление и проверка сообщения от first_step_get_image.
    Вход в класс GetAnswerDallE и в случае возврата любого
    значения кроме с кодом 423, возврат ConversationHandler.
    """
    del_id = context.user_data.pop('image_gen', None)
    if del_id:
        context.bot.delete_message(update.effective_chat.id, del_id)

    result = GetAnswerDallE(update, context).get_image_dall_e()
    if not result or result.get('code') != 423:
        return ConversationHandler.END

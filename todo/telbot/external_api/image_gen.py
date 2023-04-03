import os
import threading
import time
from datetime import datetime, timedelta

import openai
from django.contrib.auth import get_user_model
from dotenv import load_dotenv
from telegram import ChatAction, InputMediaPhoto, ParseMode, Update
from telegram.ext import CallbackContext, ConversationHandler

from ..checking import check_registration
from ..cleaner import remove_keyboard

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

    def __init__(self,
                 update: Update,
                 context: CallbackContext) -> None:
        self.update = update
        self.context = context
        self.chat_id = None
        self.message_text = None
        self.set_message_text()
        self.set_chat_id()

    def get_image_dall_e(self):
        """
        Возвращает серию картинок от АПИ Dall-e 2.
        Предварительно вызвав функцию проверки регистрации.
        """
        answers = {
            '': ('К сожалению данная функция доступна только для '
                 '[зарегистрированных пользователей]'
                 f'({self.context.bot.link})'),
        }

        del_id = self.context.user_data['image_gen']
        self.context.bot.delete_message(self.chat_id, del_id)

        if check_registration(self.update, self.context, answers) is False:
            return {'code': 401}
        try:

            media_group = self.get_answer()

        except Exception as err:
            self.send_message(
                text=f'Ошибка в ChatGPT: {err}',
                is_admin=True
            )
        finally:
            self.send_message(
                media_group=media_group,
                is_reply=True
            )
            return ConversationHandler.END

    def get_answer(self) -> list:
        """
        Асинхронно запускает 2 функции и при выполнении запроса в openai
        """
        stop_event = threading.Event()
        typing = threading.Thread(
            target=self.send_typing_periodically,
            args=(stop_event,)
        )
        typing.start()
        answer = self.request_to_openai()
        stop_event.set()
        typing.join()
        return answer

    def send_typing_periodically(self, stop_event: threading.Event) -> None:
        """"
        Передаёт TYPING в чат Телеграм откуда пришёл запрос.
        """
        time_stop = (
            datetime.now()
            + timedelta(minutes=GetAnswerDallE.MAX_TYPING_TIME)
        )
        while not stop_event.is_set():
            self.context.bot.send_chat_action(
                chat_id=self.chat_id,
                action=ChatAction.UPLOAD_PHOTO
            )
            time.sleep(2)
            if datetime.now() > time_stop:
                break

    def request_to_openai(self) -> list:
        """
        Делает запрос в OpenAI.
        """
        media_group = []
        response = openai.Image.create(
            prompt=self.message_text,
            n=5,
            size='1024x1024'
        )
        for number, url in enumerate(response['data']):
            media_group.append(
                InputMediaPhoto(media=url['url'], caption=f'Gen № {number}')
            )
        return media_group

    def send_message(self,
                     media_group: list = None,
                     text: str = None,
                     is_admin: bool = False,
                     is_reply: bool = False) -> None:
        """
        Отправка сообщения в чат Telegram.
        args:
            text(:obj:`str`): текст сообщения
            media_group(:obj:`list`): ссылки на картинки
            is_admin(:obj:`bool`): отправка только админу
            is_reply(:obj:`bool`): отправлять ответом на сообщение
        """
        params = {
            'chat_id': ADMIN_ID if is_admin else self.chat_id,
        }

        if is_reply:
            params['reply_to_message_id'] = self.update.message.message_id

        if text:
            params['text'] = text
            self.context.bot.send_message(**params)
            return None

        if media_group:
            params['media'] = media_group
            self.context.bot.send_media_group(**params)
            return None

        params['text'] = GetAnswerDallE.ERROR_TEXT
        self.context.bot.send_message(**params)

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
    GetAnswerDallE(update, context).get_image_dall_e()

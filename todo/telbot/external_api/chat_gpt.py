import os
import threading
import time
from datetime import datetime, timedelta, timezone

import openai
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from dotenv import load_dotenv
from telegram import ChatAction, Update
from telegram.ext import CallbackContext

from ..checking import check_registration
from ..models import HistoryAI

load_dotenv()

openai.api_key = os.getenv('CHAT_GP_TOKEN')

User = get_user_model()
ADMIN_ID = os.getenv('ADMIN_ID')


class GetAnswerDavinci():
    """
    Проверяет регистрацию.
    Делает запрос и в чат Telegram возвращает результат ответа
    от API ИИ ChatGPT.
    """
    ERROR_TEXT = (
        'Что-то пошло не так 🤷🏼\n'
        'Возможно большой наплыв запросов, '
        'которые я не успеваю обрабатывать 🤯'
    )

    def __init__(self,
                 update: Update,
                 context: CallbackContext) -> None:
        self.update = update
        self.context = context

    def get_answer_davinci(self):
        answers = {
            '?': ('Я мог бы ответить Вам, если '
                  f'[зарегистрируетесь]({self.context.bot.link}) 🧐'),
            '!': ('Я обязательно поддержу Вашу дискуссию, если '
                  f'[зарегистрируетесь]({self.context.bot.link}) 🙃'),
            '': ('Какая интересная беседа, [зарегистрируетесь]'
                 f'({self.context.bot.link}) и я подключусь к ней 😇'),
        }
        if check_registration(self.update, self.context, answers) is False:
            return {'code': 401}

        try:
            answer = self.get_answer().lstrip('\n')
            answer_text = answer if answer else GetAnswerDavinci.ERROR_TEXT
            HistoryAI.objects.create(
                user=self.user,
                question=self.message_text,
                answer=answer_text
            )
        except Exception as err:
            self.send_message(
                text=f'Ошибка в ChatGPT: {err}',
                is_admin=True
            )
            answer_text = GetAnswerDavinci.ERROR_TEXT
        finally:
            self.send_message(
                text=answer_text,
                is_reply=True
            )
        return {'code': 200}

    def get_prompt(self):
        """Возвращает prompt для запроса в OpenAI."""
        this_datetime = datetime.now(timezone.utc)
        start_datetime = this_datetime - timedelta(minutes=5)
        history = (
            self.user.history_ai
            .filter(created_at__range=[start_datetime, this_datetime])
            .exclude(answer__in=[None, GetAnswerDavinci.ERROR_TEXT])
        )
        prompt = []
        if history:
            for item in history:
                prompt.append({'role': 'user', 'content': item.question})
                prompt.append({'role': 'assistant', 'content': item.answer})

        prompt.append({'role': 'user', 'content': self.message_text})
        return prompt

    def send_typing_periodically(self, stop_event: threading.Event) -> None:
        """"
        Передаёт TYPING в чат Телеграм откуда пришёл запрос.
        Args:
            (:obj:`int`) id чата
            (:CallbackContext:`int`) context
        Return:
            None
        """
        while not stop_event.is_set():
            self.context.bot.send_chat_action(
                chat_id=self.update.effective_chat.id,
                action=ChatAction.TYPING
            )
            time.sleep(6)

    def request_to_openai(self) -> str:
        """
        Делает запрос в OpenAI.

        Args:
            (:obj:`str`) текст для запроса

        Return:
            (:obj:`str`) ответ ИИ
        # """
        prompt = self.get_prompt()
        answer = openai.ChatCompletion.create(
            model='gpt-3.5-turbo',
            messages=prompt
        )
        answer_text = answer.choices[0].message.get('content')
        # для теста
        # time.sleep(10)
        # answer_text = '\n'.join([w.get('content') for w in prompt])
        return answer_text

    def get_answer(self):
        """
        Асинхронно запускает 2 функции и при выполнении запроса в openai

        Args:
            (:obj:`str`) текст для запроса
            (:obj:`int`) ID чата откуда пришёл вызов
            (:obj:`CallbackContext`) CallbackContext
        Return
            (:obj:`str`): answer
        """
        stop_event = threading.Event()
        task = threading.Thread(
            target=self.send_typing_periodically,
            args=(stop_event,)
        )
        task.start()
        answer = self.request_to_openai()

        stop_event.set()
        task.join()

        return answer

    def send_message(self,
                     text,
                     is_admin: bool = False,
                     is_reply: bool = False):
        """Отправка сообщения в чат Telegram."""
        params = {
            'chat_id': ADMIN_ID if is_admin else self.update.effective_chat.id,
            'text': text,
        }
        if is_reply:
            params['reply_to_message_id'] = self.update.message.message_id

        self.context.bot.send_message(**params)

    @property
    def user(self):
        user = get_object_or_404(
            User,
            username=self.update.effective_user.id
        )
        return user

    @property
    def message_text(self):
        return self.update.effective_message.text.replace('#', '', 1)


def get_answer_davinci(update: Update, context: CallbackContext):
    GetAnswerDavinci(update, context).get_answer_davinci()

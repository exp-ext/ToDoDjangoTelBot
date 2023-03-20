import os
import threading
import time
from datetime import datetime, timedelta, timezone

import openai
from django.contrib.auth import get_user_model
from django.db.models.query import QuerySet
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
    MAX_LONG_MESSAGE = 600
    MAX_LONG_REQUEST = 2049

    def __init__(self,
                 update: Update,
                 context: CallbackContext) -> None:
        self.update = update
        self.context = context
        self.user = None
        self.message_text = None

    def get_answer_davinci(self) -> dict:
        """Основная логика класса."""
        if check_registration(self.update,
                              self.context,
                              self.answers_for_check) is False:
            return {'code': 401}

        self.set_user()
        self.set_message_text()

        if self.check_long_query:
            answer_text = (
                f'{self.user.first_name}, у Вас слишком большой текст запроса.'
                ' Попробуйте сформулировать его короче.'
            )
            self.send_message(
                text=answer_text,
                is_reply=True
            )
            return {'code': 400}
        try:
            answer = self.get_answer()
            answer_text = answer if answer else GetAnswerDavinci.ERROR_TEXT
            HistoryAI.objects.create(
                user=self.user,
                question=self.message_text,
                answer=answer_text.lstrip('\n')
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

    def get_answer(self) -> str:
        """
        Асинхронно запускает 2 функции и при выполнении запроса в openai
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

    def send_typing_periodically(self, stop_event: threading.Event) -> None:
        """"
        Передаёт TYPING в чат Телеграм откуда пришёл запрос.
        """
        while not stop_event.is_set():
            self.context.bot.send_chat_action(
                chat_id=self.update.effective_chat.id,
                action=ChatAction.TYPING
            )
            time.sleep(6)

    def request_to_openai(self) -> str | QuerySet:
        """
        Делает запрос в OpenAI.
        """
        prompt = self.get_prompt()
        answer = openai.ChatCompletion.create(
            model='gpt-3.5-turbo',
            messages=prompt
        )
        answer_text = answer.choices[0].message.get('content')
        return answer_text

    def get_prompt(self) -> str | QuerySet:
        """
        Возвращает prompt для запроса в OpenAI и модель user.
        """
        this_datetime = datetime.now(timezone.utc)
        start_datetime = this_datetime - timedelta(minutes=5)
        history = (
            self.user.history_ai
            .filter(created_at__range=[start_datetime, this_datetime])
            .exclude(answer__in=[None, GetAnswerDavinci.ERROR_TEXT])
            .values('question', 'answer')
        )
        prompt = []
        count_value = 0
        for item in history:
            count_value += len(item['question']) + len(item['answer'])
            if (count_value + len(self.message_text)
                    >= GetAnswerDavinci.MAX_LONG_REQUEST):
                break
            prompt.extend([
                {'role': 'user', 'content': item['question']},
                {'role': 'assistant', 'content': item['answer']}
            ])
        prompt.append({'role': 'user', 'content': self.message_text})
        return prompt

    def send_message(self,
                     text,
                     is_admin: bool = False,
                     is_reply: bool = False):
        """
        Отправка сообщения в чат Telegram.
        args:
            text(:obj:`str`): текст сообщения
            is_admin(:obj:`bool`): отправка только админу
            is_reply(:obj:`bool`): отправлять ответом на сообщение
        """
        params = {
            'chat_id': ADMIN_ID if is_admin else self.update.effective_chat.id,
            'text': text,
        }
        if is_reply:
            params['reply_to_message_id'] = self.update.message.message_id

        self.context.bot.send_message(**params)

    def set_user(self) -> None:
        """Определяем и назначаем юзера."""
        self.user = get_object_or_404(
            User,
            username=self.update.effective_user.id
        )

    def set_message_text(self) -> str:
        """Определяем и назначаем текст сообщения."""
        self.message_text = (
            self.update.effective_message.text.replace('#', '', 1)
        )

    @property
    def check_long_query(self) -> bool:
        return len(self.message_text) > GetAnswerDavinci.MAX_LONG_MESSAGE

    @property
    def answers_for_check(self):
        return {
            '?': ('Я мог бы ответить Вам, если '
                  f'[зарегистрируетесь]({self.context.bot.link}) 🧐'),
            '!': ('Я обязательно поддержу Вашу дискуссию, если '
                  f'[зарегистрируетесь]({self.context.bot.link}) 🙃'),
            '': ('Какая интересная беседа, [зарегистрируетесь]'
                 f'({self.context.bot.link}) и я подключусь к ней 😇'),
        }


def get_answer_davinci(update: Update, context: CallbackContext):
    GetAnswerDavinci(update, context).get_answer_davinci()

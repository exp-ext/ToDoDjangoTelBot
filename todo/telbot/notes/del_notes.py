import asyncio
from datetime import datetime

from django.contrib.auth import get_user_model
from django.db.models import DateTimeField
from django.db.models.functions import Trunc
from django.shortcuts import get_object_or_404
from telegram import Update
from telegram.ext import CallbackContext, ConversationHandler

from ..cleaner import remove_keyboard
from ..service_message import send_service_message
from .parse_note import TaskParse

User = get_user_model()


class TaskDeleter:
    def __init__(self, update: Update, context: CallbackContext):
        self.update = update
        self.context = context
        self.chat = update.effective_chat
        self.message_thread_id = update.effective_message.message_thread_id
        self.tg_username = update.message.from_user.username
        self.text = " ".join(update.message.text.split()).replace('- ', '')
        self.user = None
        self.user_locally = None
        self.pars = None

    def get_user(self):
        """Получение пользователя и его локации."""
        self.user = get_object_or_404(User.objects.prefetch_related('locations'), username=self.tg_username)
        self.user_locally = self.user.locations.first() if self.user.locations.exists() else 'UTC'

    def parse_message(self):
        """Парсинг сообщения и даты."""
        self.pars = TaskParse(self.text, self.user_locally.timezone, self.user, self.chat.id, True)
        asyncio.run(self.pars.parse_message())

    def delete_messages(self):
        """Удаление сообщений."""
        del_id = (self.context.user_data.get('del_message'), self.update.message.message_id)
        for id in filter(None, del_id):
            self.context.bot.delete_message(self.chat.id, id)

    def delete_tasks(self):
        """Логика удаления задач."""
        reply_text = f'*{self.update.message.from_user.first_name}*, не удалось разобрать дату 🧐. Попробуйте снова 🙄.'
        if self.pars.server_datetime:
            tasks = self.user.tasks.filter(text__icontains=self.pars.only_message)
            tasks = self.filter_tasks(tasks)
            count = tasks.count()
            if count > 0:
                tasks.delete()
                single = count == 1
                reply_text = self.format_success_reply(count, single)
            else:
                reply_text = f'Не удалось найти напоминание *<{self.pars.only_message}>* на дату: *{self.pars.user_datetime.strftime("%d.%m.%Y")}*. Попробуйте снова.'
        self.send_service_message(reply_text)

    def filter_tasks(self, tasks):
        """Фильтрация задач по дате."""
        if self.pars.user_datetime.hour == 0 and self.pars.user_datetime.minute == 0:
            start_of_day = datetime.combine(self.pars.user_datetime, datetime.min.time())
            end_of_day = datetime.combine(self.pars.user_datetime, datetime.max.time())
            return tasks.filter(server_datetime__range=(start_of_day, end_of_day))
        return tasks.annotate(
            server_datetime_hour=Trunc('server_datetime', 'hour', output_field=DateTimeField())
        ).filter(server_datetime_hour=self.pars.server_datetime.replace(minute=0, second=0, microsecond=0))

    def format_success_reply(self, count, single):
        """Форматирование ответа об успешном удалении."""
        return (
            f'Напоминани{"е" if single else "я"} с текстом *<{self.pars.only_message}>* на дату *{self.pars.user_datetime.strftime("%d.%m.%Y")}*, '
            f'удален{"о" if single else "ы"} безвозвратно{"." if single else f" в количестве {count}шт."}'
        )

    def send_service_message(self, text):
        """Отправка служебного сообщения."""
        send_service_message(self.chat.id, text, 'Markdown', self.message_thread_id)

    def run(self):
        """Основной метод для запуска процесса удаления."""
        try:
            self.get_user()
            self.parse_message()
            self.delete_messages()
            self.delete_tasks()
        except Exception as error:
            raise KeyError(error)
        finally:
            return ConversationHandler.END


def first_step_dell(update: Update, context: CallbackContext):
    chat = update.effective_chat
    message_thread_id = update.effective_message.message_thread_id
    req_text = (
        f'*{update.effective_user.first_name}*, '
        'введите дату и часть текста заметки которую планируете удалить 🖍'
    )
    message_id = context.bot.send_message(
        chat.id,
        req_text,
        parse_mode='Markdown',
        message_thread_id=message_thread_id
    ).message_id
    context.user_data['del_message'] = message_id
    remove_keyboard(update, context)
    return 'del_note'


def del_notes(update: Update, context: CallbackContext):
    deleter = TaskDeleter(update, context)
    return deleter.run()

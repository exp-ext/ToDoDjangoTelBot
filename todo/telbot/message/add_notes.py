import traceback
from datetime import timedelta

from core.views import similarity
from django.conf import settings
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from tasks.models import Task
from telegram import Update
from telegram.ext import CallbackContext, ConversationHandler
from users.models import Group

from ..cleaner import remove_keyboard
from ..service_message import send_service_message
from .parse_message import TaskParse

User = get_user_model()
ADMIN_ID = settings.TELEGRAM_ADMIN_ID


class NoteManager:
    def __init__(self, update, context):
        self.update = update
        self.context = context
        self.chat = update.effective_chat
        self.message_thread_id = update.effective_message.message_thread_id
        self.user_text = update.message.text.strip()
        self.user = get_object_or_404(User.objects.prefetch_related('groups_connections', 'locations'), username=update.effective_user.username)
        self.user_locally = self.user.locations.first()
        self.delta_time_min = 120

    def add_notes(self):
        """Добавление записи в модель Task."""
        try:
            pars = TaskParse(self.user_text, self.user_locally.timezone if self.user_locally else 'UTC')
            pars.parse_message()

            group = None if self.chat.type == 'private' else get_object_or_404(Group, chat_id=self.chat.id)

            self.delete_messages()

            if not pars.server_date:
                self.send_failure_message()
                return ConversationHandler.END

            if self.is_similar_task_exists(group, pars):
                self.send_similarity_message()
                return ConversationHandler.END

            task = self.create_task(group, pars)
            self.send_success_message(pars, task)

        except Exception as err:
            traceback_str = traceback.format_exc()
            self.context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f'Ошибка при добавлении напоминания: {str(err)[:1024]}\n\nТрассировка:\n{traceback_str[-1024:]}',
            )
        finally:
            return ConversationHandler.END

    def delete_messages(self):
        del_id = (self.context.user_data.get('del_message'), self.update.message.message_id)
        for id in filter(None, del_id):
            self.context.bot.delete_message(self.chat.id, id)

    def is_similar_task_exists(self, group, pars):
        start_datetime = pars.server_date - timedelta(minutes=60)
        end_datetime = pars.server_date + timedelta(minutes=60)
        tasks = self.user.tasks.filter(server_datetime__range=[start_datetime, end_datetime], user=self.user, group=group)
        return any(similarity(task.text, pars.only_message) > 0.62 for task in tasks)

    def create_task(self, group, pars):
        remind_min = 480 if pars.user_date.hour == 0 and pars.user_date.minute == 0 else self.delta_time_min
        return Task.objects.create(
            user=self.user,
            group=group,
            server_datetime=pars.server_date,
            text=pars.only_message,
            remind_min=remind_min,
            reminder_period='Y' if pars.birthday else pars.period_repeat,
            it_birthday=pars.birthday
        )

    def send_failure_message(self):
        reply_text = f'*{self.update.message.from_user.first_name}*, не удалось разобрать дату 🧐. Попробуйте снова 🙄.'
        send_service_message(self.chat.id, reply_text, 'Markdown', self.message_thread_id)

    def send_similarity_message(self):
        reply_text = 'Очень похожее напоминание присутствует в задачах.\nЗапись отклонена.'
        send_service_message(self.chat.id, reply_text, self.message_thread_id)

    def send_success_message(self, pars, task):
        reply_text = f'Напоминание: *{pars.only_message}*\nСоздано\nна дату: *{pars.user_date.strftime("%d.%m.%Y")}*\n'
        if not task.it_birthday:
            new_date = pars.user_date - timedelta(minutes=self.delta_time_min)
            reply_text += f'с оповещением в *{new_date.strftime("%H:%M")}*\n'
        send_service_message(self.chat.id, reply_text, 'Markdown', self.message_thread_id)


def first_step_add(update: Update, context: CallbackContext):
    chat = update.effective_chat
    message_thread_id = update.effective_message.message_thread_id
    req_text = f'*{update.effective_user.first_name}*, введите текст заметки с датой и временем 🖌'
    message_id = context.bot.send_message(
        chat.id,
        req_text,
        parse_mode='Markdown',
        message_thread_id=message_thread_id
    ).message_id
    context.user_data['del_message'] = message_id
    remove_keyboard(update, context)
    return 'add_note'


def add_notes(update: Update, context: CallbackContext) -> None:
    note_manager = NoteManager(update, context)
    return note_manager.add_notes()

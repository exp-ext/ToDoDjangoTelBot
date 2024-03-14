import asyncio
import traceback
from datetime import timedelta

from asgiref.sync import sync_to_async
from channels.db import database_sync_to_async
from core.views import similarity
from django.conf import settings
from django.contrib.auth import get_user_model
from tasks.models import Task
from telbot.checking import check_registration
from telbot.cleaner import remove_keyboard
from telbot.service_message import send_message_to_chat, send_service_message
from telegram import Update
from telegram.ext import CallbackContext, ConversationHandler
from users.models import Group

from .parse_note import TaskParse

User = get_user_model()
ADMIN_ID = settings.TELEGRAM_ADMIN_ID


class NoteManager:
    """
    Менеджер для добавления записей.

    ### Args:
    - update: Обновление Telegram.
    - context: Контекст.
    - user: Пользователь.

    """
    def __init__(self, update, context, user):
        """
        Инициализация объекта NoteManager.

        """
        self.update = update
        self.context = context
        self.chat = update.effective_chat
        self.message_thread_id = update.effective_message.message_thread_id
        self.user_text = update.effective_message.text.strip()
        self.user = user
        self.delta_time_min = 120
        self.pars_params = None

    async def add_notes(self):
        """Добавление записи в модель Task."""
        try:
            asyncio.create_task(self.delete_messages())

            self.user_locally = await self.get_locations()
            timezone = self.user_locally.timezone if self.user_locally else 'UTC'
            self.pars_params = TaskParse(self.user_text, timezone, self.user, self.chat.id)
            await self.pars_params.parse_message()

            group = None if self.chat.type == 'private' else await self.get_group()

            if not self.pars_params.server_datetime:
                await self.send_failure_message()
                return None

            if await self.is_similar_task_exists(group):
                await self.send_similarity_message()
                return None

            task = await self.create_task(group)
            await self.send_success_message(task)

        except Exception as err:
            await self.send_failure_message()
            traceback_str = traceback.format_exc()
            text = f'Ошибка при добавлении напоминания в `NoteManager`:\n{str(err)[:1024]}\n\nТрассировка:\n{traceback_str[-1024:]}'
            send_message_to_chat(ADMIN_ID, text)

    async def delete_messages(self):
        """Удаление сообщений."""
        del_id = (self.context.user_data.get('del_message'), self.update.message.message_id)
        for id in filter(None, del_id):
            self.context.bot.delete_message(self.chat.id, id)

    @sync_to_async
    def send_failure_message(self):
        """Отправка сообщения при ошибке."""
        reply_text = f'*{self.update.message.from_user.first_name}*, не удалось разобрать дату 🧐. Попробуйте снова 🙄.'
        send_service_message(self.chat.id, reply_text, 'Markdown', self.message_thread_id)

    @sync_to_async
    def send_similarity_message(self):
        """Отправка сообщения о схожем напоминании."""
        reply_text = 'Очень похожее напоминание присутствует в задачах.\nЗапись отклонена.'
        send_service_message(self.chat.id, reply_text, self.message_thread_id)

    @sync_to_async
    def send_success_message(self, task):
        """Отправка сообщения об успешном добавлении записи."""
        reply_text = (
            f'Напоминание: *{self.pars_params.only_message}*\n'
            f'Создано на *{self.pars_params.user_datetime.strftime("%d.%m.%Y %H:%M")}*\n'
        )
        if not task.it_birthday:
            new_date = self.pars_params.user_datetime - timedelta(minutes=self.delta_time_min)
            reply_text += f'с оповещением в *{new_date.strftime("%H:%M")}*\n'
        send_service_message(self.chat.id, reply_text, 'Markdown', self.message_thread_id)

    @database_sync_to_async
    def is_similar_task_exists(self, group):
        """Проверка наличия схожего напоминания."""
        start_datetime = self.pars_params.server_datetime - timedelta(minutes=60)
        end_datetime = self.pars_params.server_datetime + timedelta(minutes=60)
        tasks = self.user.tasks.filter(server_datetime__range=[start_datetime, end_datetime], user=self.user, group=group)
        return any(similarity(task.text, self.pars_params.only_message) > 0.62 for task in tasks)

    @database_sync_to_async
    def create_task(self, group):
        """Создание заметки."""
        self.delta_time_min = self.pars_params.delta_time_min or self.delta_time_min
        return Task.objects.create(
            user=self.user,
            group=group,
            server_datetime=self.pars_params.server_datetime,
            text=self.pars_params.only_message,
            remind_min=self.delta_time_min,
            reminder_period=self.pars_params.period_repeat,
            it_birthday=False
        )

    @database_sync_to_async
    def get_group(self):
        """Получение группы."""
        return Group.objects.filter(chat_id=self.chat.id).first()

    @database_sync_to_async
    def get_locations(self):
        """Получение локации."""
        return self.user.locations.first()


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
    answers = {
        '': 'Для начала необходимо пройти регистрацию. Для этого отправьте ему команду /start 🔆'
    }
    user = check_registration(update, context, answers, return_user=True, prefetch_related=['tasks', 'locations', 'groups_connections__group'])
    note_manager = NoteManager(update, context, user)
    try:
        asyncio.run(note_manager.add_notes())
    except Exception:
        pass
    finally:
        return ConversationHandler.END

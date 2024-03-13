from datetime import datetime

import pytz
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.shortcuts import get_object_or_404
from tasks.models import Task
from telegram import ParseMode, Update
from telegram.ext import CallbackContext, ConversationHandler
from users.models import Group

from ..cleaner import remove_keyboard
from .parse_note import TaskParse

User = get_user_model()


def first_step_show(update: Update, context: CallbackContext):
    chat = update.effective_chat
    message_thread_id = update.effective_message.message_thread_id
    req_text = f'*{update.effective_user.first_name}*, введите дату, на которую хотите вывести заметки 📆'
    message_id = context.bot.send_message(
        chat.id,
        req_text,
        parse_mode='Markdown',
        message_thread_id=message_thread_id
    ).message_id
    context.user_data['del_message'] = message_id
    remove_keyboard(update, context)
    return 'show_note'


class ShowEvents:
    def __init__(self, update: Update, context: CallbackContext, at_date: datetime = None, it_birthday: bool = False):
        self.update = update
        self.context = context
        self.at_date = at_date
        self.it_birthday = it_birthday
        self.chat = update.effective_chat
        self.message_thread_id = update.effective_message.message_thread_id
        self.tg_user = update.effective_user
        self.user = None
        self.user_locally = None
        self.user_tz = None
        self.group = None
        self.tasks = []

    def get_user(self):
        """Получение пользователя и его локации."""
        self.user = get_object_or_404(
            User.objects.prefetch_related('groups_connections', 'locations'),
            username=self.tg_user.username
        )
        self.user_locally = self.user.locations.first()
        self.user_tz = pytz.timezone(self.user_locally.timezone) if self.user_locally else None

    def select_tasks(self):
        """Выбор задач на определённую дату или для дней рождения."""
        if self.chat.type == 'private':
            if self.at_date:
                self.tasks = self.user.tasks.filter(
                    server_datetime__day=self.at_date.day,
                    server_datetime__month=self.at_date.month
                )
            else:
                groups_id = self.user.groups_connections.values_list('group_id', flat=True)
                self.tasks = (
                    Task.objects
                    .filter(Q(user=self.user) | Q(group_id__in=groups_id))
                    .exclude(~Q(it_birthday=self.it_birthday))
                    .order_by('server_datetime__month', 'server_datetime__day')
                )
        else:
            self.group = get_object_or_404(Group, chat_id=self.chat.id)
            self.tasks = (
                self.group.tasks.filter(server_datetime__day=self.at_date.day, server_datetime__month=self.at_date.month)
                if self.at_date else self.group.tasks.filter(it_birthday=self.it_birthday)
            )

    def format_notes(self):
        """Формирование списка событий."""
        notes = []
        for item in self.tasks:
            utc_date = item.server_datetime
            user_date = utc_date.astimezone(self.user_tz) if self.user_tz else utc_date

            note = self.format_note(item, user_date)
            notes.append(note)

        note_sort = self.format_header(notes)
        return note_sort

    def format_note(self, item, user_date):
        """Форматирование заметки."""
        note = f'<b>{user_date.strftime("%d.%m.%Y")}{" в " + user_date.strftime("%H:%M") if not item.it_birthday else ""} - {item.text}</b>'
        if not self.group and item.user.username != self.tg_user.username:
            note += f'\n- <i>автор {item.user.get_full_name()}</i>'
        if not self.group and item.group:
            note += f'\nвывод в группе "{item.group.title}"'
        if item.remind_at and not item.it_birthday:
            remind_time = item.remind_at.astimezone(self.user_tz) if self.user_tz else item.remind_at
            note += f'<b><i>\n- напомню в {remind_time.strftime("%H:%M")}ч</i></b>'
        note += '\n'
        return note

    def format_header(self, notes):
        """Формирование заголовка сообщения."""
        header = f'<strong>{self.tg_user.first_name}, {"найденные записи" if self.tasks else "не найдены записи"}{" Дней Рождений 🎉" if self.it_birthday else " у Вас в планах 📜"}</strong>:\n\n'
        return header + '\n'.join(notes)

    def send_message(self):
        """Отправка сообщения со списком событий."""
        note_sort = self.format_notes()
        self.context.bot.send_message(
            chat_id=self.chat.id,
            text=note_sort,
            parse_mode=ParseMode.HTML,
            message_thread_id=self.message_thread_id
        )

    def run(self):
        """Основной метод для выполнения всех шагов."""
        self.get_user()
        self.select_tasks()
        self.send_message()


def show_all_notes(update: Update, context: CallbackContext):
    """Выводит весь список записей в чат в зависимости от private или group."""
    remove_keyboard(update, context)
    show_events = ShowEvents(update, context)
    show_events.run()


def show_birthday(update: Update, context: CallbackContext):
    """Выводит весь список дней рождения в чат в зависимости от private или group."""
    remove_keyboard(update, context)
    show_events = ShowEvents(update, context, it_birthday=True)
    show_events.run()


def show_at_date(update: Update, context: CallbackContext):
    """Выводит список записей на конкретный день в чат в зависимости от private или group."""
    chat = update.effective_chat
    user = get_object_or_404(User, username=update.effective_user.username)
    user_locally = user.locations.first()

    pars = TaskParse(update.message.text, user_locally.timezone)
    pars.parse_message()

    try:
        del_id = (context.user_data['del_message'], update.message.message_id)
        for id in del_id:
            context.bot.delete_message(chat.id, id)
        show_events = ShowEvents(update, context, pars.user_date)
        show_events.run()
    except Exception as error:
        raise KeyError(error)
    finally:
        return ConversationHandler.END

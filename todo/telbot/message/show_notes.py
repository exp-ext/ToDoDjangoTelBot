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
from .parse_message import TaskParse

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


def show_at_date(update: Update, context: CallbackContext):
    """
    Выводит список записей на конкретный день в чат в зависимости от private или group.
    """
    chat = update.effective_chat
    user = get_object_or_404(
        User,
        username=update.effective_user.username
    )
    user_locally = user.locations.first()

    pars = TaskParse(update.message.text, user_locally.timezone)
    pars.parse_message()

    try:
        del_id = (context.user_data['del_message'], update.message.message_id)
        for id in del_id:
            context.bot.delete_message(chat.id, id)
        show(update, context, pars.user_date)
    except Exception as error:
        raise KeyError(error)
    finally:
        return ConversationHandler.END


def show_all_notes(update: Update, context: CallbackContext):
    """Выводит весь список записей в чат в зависимости от private или group."""
    remove_keyboard(update, context)
    show(update, context)


def show_birthday(update: Update, context: CallbackContext):
    """
    Выводит весь список дней рождения в чат в зависимости от private или group.
    """
    remove_keyboard(update, context)
    show(update, context, it_birthday=True)


def show(update: Update, context: CallbackContext,
         at_date: datetime = None, it_birthday: bool = False):
    """
    Общий модуль обработки и вывода данных.
        Принимает диспетчера бота:
        - update (`Update`)
        - context (`CallbackContext`)

    Именованные параметры:
        - at_date (`datetime`) = None, да на которую будет вывод списка
        - it_birthday (`bool`) = False, для вывода в списке дней рождения

    Отправляет в чат сообщение со списком событий.
    """
    chat = update.effective_chat
    message_thread_id = update.effective_message.message_thread_id
    tg_user = update.effective_user
    user = get_object_or_404(
        User.objects.prefetch_related('groups_connections', 'locations'),
        username=tg_user.username
    )
    user_locally = user.locations.first()
    user_tz = pytz.timezone(user_locally.timezone) if user_locally else None
    group = None

    if chat.type == 'private':
        if at_date:
            tasks = user.tasks.filter(
                server_datetime__day=at_date.day,
                server_datetime__month=at_date.month
            )
        else:
            groups_id = user.groups_connections.values_list('group_id', flat=True)
            tasks = (
                Task.objects
                .filter(Q(user=user) | Q(group_id__in=groups_id))
                .exclude(~Q(it_birthday=it_birthday))
                .order_by('server_datetime__month', 'server_datetime__day')
            )
    else:
        group = get_object_or_404(Group, chat_id=chat.id)
        tasks = (
            group.tasks.filter(server_datetime__day=at_date.day, server_datetime__month=at_date.month)
            if at_date else group.tasks.filter(it_birthday=it_birthday)
        )

    notes = []
    for item in tasks:
        utc_date = item.server_datetime
        user_date = utc_date.astimezone(user_tz) if user_tz else utc_date

        if item.it_birthday or (not at_date or item.server_datetime.year == at_date.year):
            note = f'<b>{user_date.strftime("%d.%m.%Y")}{" в " + user_date.strftime("%H:%M") if not item.it_birthday else ""} - {item.text}</b>'
            if not group and item.user.username != tg_user.username:
                note += f'\n- <i>автор {item.user.get_full_name()}</i>'
            if not group and item.group:
                note += f'\nвывод в группе "{item.group.title}"'
            if item.remind_at and not item.it_birthday:
                remind_time = item.remind_at.astimezone(user_tz) if user_tz else item.remind_at
                note += f'<b><i>\n- напомню в {remind_time.strftime("%H:%M")}ч</i></b>'
            note += '\n'
            notes.append(note)

    note_sort = f'<strong>{tg_user.first_name}, {"найденные записи" if tasks else "не найдены записи"}{" Дней Рождений 🎉" if it_birthday else " у Вас в планах 📜"}</strong>:\n\n'
    note_sort += '\n'.join(notes)

    context.bot.send_message(
        chat_id=chat.id,
        text=note_sort,
        parse_mode=ParseMode.HTML,
        message_thread_id=message_thread_id
    )

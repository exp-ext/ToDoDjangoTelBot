from datetime import datetime

import pytz
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from telegram import ParseMode, Update
from telegram.ext import CallbackContext, ConversationHandler
from users.models import Group

from ..cleaner import remove_keyboard
from .parse_message import TaskParse

User = get_user_model()


def first_step_show(update: Update, context: CallbackContext):
    chat = update.effective_chat
    req_text = (
            f'*{update.effective_user.first_name}*, '
            'введите дату, на которую хотите вывести заметки\n'
            'или *end* для отмены операции'
        )
    message_id = context.bot.send_message(
        chat.id,
        req_text,
        parse_mode='Markdown'
    ).message_id
    context.user_data['del_message'] = message_id
    remove_keyboard(update, context)
    return 'show_note'


def show_at_date(update: Update, context: CallbackContext):
    """
    Выводит список записей на конкретный день в чат
    в зависимости от private или group.
    """
    chat = update.effective_chat
    user_id = update.effective_user.id
    user = get_object_or_404(
        User,
        username=user_id
    )
    user_locally = user.locations.first()

    pars = TaskParse(update.message.text, user_locally.timezone)
    pars.parse_without_parameters()

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
    user_id = update.effective_user.id

    user = get_object_or_404(
            User,
            username=user_id
        )
    user_locally = user.locations.first()
    user_tz = pytz.timezone(user_locally.timezone)

    if chat.type == 'private':
        if at_date:
            tasks = user.tasks.filter(
                server_datetime__day=at_date.day,
                server_datetime__month=at_date.month
            )
        else:
            tasks = user.tasks.filter(it_birthday=it_birthday)
    else:
        group = get_object_or_404(
            Group,
            chat_id=chat.id
        )
        if at_date:
            tasks = group.tasks.filter(
                server_datetime__day=at_date.day,
                server_datetime__month=at_date.month
            )
        else:
            tasks = group.tasks.filter(it_birthday=it_birthday)

    notes = []

    for item in tasks:
        if item.it_birthday:
            utc_date = item.server_datetime
            user_date = utc_date.astimezone(user_tz)
            notes.append(
                f'{datetime.strftime(user_date, "%d.%m")} '
                f'- {item.text}'
            )
        else:
            if not at_date or item.server_datetime.year == at_date.year:
                utc_date = item.server_datetime
                user_date = utc_date.astimezone(user_tz)
                utc_remind = item.remind_at
                remind = utc_remind.astimezone(user_tz)
                user_time = datetime.strftime(user_date, "%H:%M")
                user_time = '' if user_time == '00:00' else f' в {user_time} '
                notes.append(
                    f'{datetime.strftime(user_date, "%d.%m.%Y")} {user_time}'
                    f'- {item.text}\n'
                    '<b><i>- напомню в '
                    f'{datetime.strftime(remind, "%H:%M")}ч</i></b>\n'
                )
    if tasks:
        if it_birthday:
            note_sort = (
                f'<strong>{update.effective_user.first_name}, '
                'найдены записи Дней Рождений 🎉:</strong>\n'
            )
        else:
            note_sort = (
                f'<strong>{update.effective_user.first_name}, '
                'в планах есть записи 📜:</strong>\n\n'
            )
    else:
        if it_birthday:
            note_sort = (
                f'<strong>{update.effective_user.first_name}, '
                'не найдены записи о Днях Рождений 🤷🏼</strong>\n'
            )
        else:
            note_sort = (
                f'<strong>{update.effective_user.first_name}, '
                'у нас нет никаких планов 🙅🏼‍♀️</strong>\n'
            )
    for n in notes:
        note_sort = note_sort + f'{n}\n'

    context.bot.send_message(
        chat_id=chat.id,
        text=note_sort,
        parse_mode=ParseMode.HTML
    )

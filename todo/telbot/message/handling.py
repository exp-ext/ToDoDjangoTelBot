from datetime import datetime
from difflib import SequenceMatcher

from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from tasks.models import Task
from telegram import Update
from telegram.ext import CallbackContext
from users.models import Group

from todo.celery import app

from ..start import bot
from .parse_mess import TaskParse

User = get_user_model()


def send_message(chat_id, reply_text):
    """
    Отправка сообщения в чат:
    chat_id - ID чата;
    reply_text - текс сообщения
    """
    bot.send_message(chat_id, reply_text)


def similarity(s1: str, s2: str) -> float:
    """
    Сравнение 2-х строк в модуле difflib
    [https://docs.python.org/3/library/difflib.html].
    """
    normalized = tuple((map(lambda x: x.lower(), [s1, s2])))
    matcher = SequenceMatcher(
        lambda x: x == " ",
        normalized[0],
        normalized[1]
    )
    return matcher.ratio()


@app.task(ignore_result=True)
def add_notes(update: Update, context: CallbackContext) -> str:
    """Добавление записи в БД."""
    chat = update.effective_chat
    user_id = update.message.from_user.id

    user = get_object_or_404(
        User,
        username=user_id
    )
    user_locally = user.locations.first()

    pars = TaskParse(update.message.text, user_locally.timezone)
    pars.parse_with_parameters()

    if chat.type == 'private':
        group = None
    else:
        group = get_object_or_404(
            Group,
            chat_id=chat.id
        )
    message = pars.only_message

    if pars.server_date:
        date_search = pars.server_date.date()
        tasks = user.tasks.filter(datetime__startswith=date_search)

        for task in tasks:
            simile = similarity(task.text, message)
            if simile > 0.62:
                reply_text = (
                    'Очень похожее напоминание присутствует в задачах.\n'
                    'Запись отклонена.'
                )
                send_message(chat.id, reply_text)
                return '!fault'

        Task.objects.create(
            user=user,
            group=group,
            datetime=pars.server_date,
            text=message,
            reminder_period=pars.period_repeat
        )

        reply_text = (
            f"дата: {datetime.strftime(pars.user_date, '%d.%m.%Y')}\n"
            f"время юзера: {datetime.strftime(pars.user_date, '%H:%M')}\n"
            f"время сервера: {datetime.strftime(pars.server_date, '%H:%M')}\n"
            f"повтор: {pars.period_repeat}\n"
            f"день рождения: {pars.it_birthday()}\n"
            f"{pars.only_message}\n"
            f"ID отправителя: {user_id}\n"
            f"timezone: {pars.time_zone}"
        )
    else:
        reply_text = ('Не найдена дата, попробуйте снова.')

    send_message(chat.id, reply_text)

    return '!done'

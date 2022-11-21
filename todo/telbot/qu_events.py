from datetime import datetime

import pytz
import requests
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from tasks.models import Task
from users.models import Group

from .loader import bot

User = get_user_model()

LAST_TIME: int = 1


def main_process_distributor(cur_time_tup: int):
    """Основной модуль оповещающий о событиях в чатах."""
    # проверка на пропуск минут
    global LAST_TIME
    last_time_to_check = LAST_TIME

    if cur_time_tup - 60 > last_time_to_check:
        hour_start = datetime.fromtimestamp(
            last_time_to_check
        ).strftime('%H:%M')
        hour_end = datetime.fromtimestamp(
            cur_time_tup
        ).strftime('%H:%M')

        bot.send_message(
            225429268,
            f"пропуск времени с {hour_start} до {hour_end}"
        )
    LAST_TIME = cur_time_tup

    # поиск в базе событий для вывода в текущую минуту
    this_time = datetime.utcnow().replace(second=0, microsecond=0)

    tasks = Task.objects.filter(
        remind_at__startswith=this_time
    ).select_related('user', 'group').order_by('user', 'group')

    id_users = (
        Task.objects.filter(
            remind_at__startswith=this_time
        ).order_by().values('user', 'group').distinct()
    )

    for id_user in id_users:
        reply_text = 'Напоминаю, о предстоящих событиях:\n'

        user = get_object_or_404(User, pk=id_user['user'])
        user_locally = user.locations.first()
        user_tz = pytz.timezone(user_locally.timezone)

        for task in tasks:
            group = task.group.pk if task.group else None
            if group == id_user['group'] and task.user.pk == id_user['user']:
                utc_date = task.server_datetime
                user_date = utc_date.astimezone(user_tz)
                time = datetime.strftime(user_date, "%H:%M")
                header = '' if time == '00:00' else f'В {time} - '
                reply_text += f'- {header}{task.text}\n'
                if task.reminder_period == 'N':
                    task.delete()

        target = task.group.chat_id if id_user['group'] else task.user.username

        bot.send_message(target, reply_text, parse_mode='Markdown')


def send_forismatic_quotes() -> None:
    """Рассылка цитат великих людей на русском языке от АПИ forismatic."""
    try:
        response = requests.get(
            'http://api.forismatic.com/api/1.0/',
            {
                'method': 'getQuote',
                'format': 'text',
                'lang': 'ru',
            }
        )
    except Exception as error:
        raise KeyError(error)

    msg = '*Цитата на злобу дня:*\n' + response.text
    groups = Group.objects.all()

    for id in groups:
        bot.send_message(id.chat_id, msg, parse_mode='Markdown')

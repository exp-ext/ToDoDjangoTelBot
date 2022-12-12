from datetime import datetime

import pytz
import requests
from celery import Celery
from django.apps import apps as django_apps
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404

from .loader import bot

User = get_user_model()
Group = django_apps.get_model(app_label='users', model_name='Group')
Task = django_apps.get_model(app_label='tasks', model_name='Task')

app = Celery()


@app.task
def main_process_distributor() -> str:
    """Основной модуль оповещающий о событиях в чатах."""
    this_datetime = datetime.utcnow().replace(second=0, microsecond=0)

    # поиск в базе событий для вывода в текущую минуту
    tasks = Task.objects.filter(
        remind_at__startswith=this_datetime
    ).select_related('user', 'group').order_by('user', 'group')

    id_users = (
        Task.objects.filter(
            remind_at__startswith=this_datetime
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
    return 'Done'


@app.task
def send_forismatic_quotes() -> str:
    """Рассылка цитат великих людей на русском языке от АПИ forismatic."""
    try:
        request = [
            'http://api.forismatic.com/api/1.0/',
            {
                'method': 'getQuote',
                'format': 'text',
                'lang': 'ru',
            }
        ]
        response = requests.get(*request)
    except Exception as error:
        raise KeyError(error)

    msg = '*Цитата на злобу дня:*\n' + response.text
    groups = Group.objects.all()

    for id in groups:
        bot.send_message(id.chat_id, msg, parse_mode='Markdown')
    return 'Done'

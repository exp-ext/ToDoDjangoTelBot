import time
from datetime import datetime

import pytz
import requests
from celery import Celery
from django.apps import apps as django_apps
from django.contrib.auth import get_user_model
from django.db.models.query import QuerySet
from django.shortcuts import get_object_or_404

from .loader import bot

User = get_user_model()
Group = django_apps.get_model(app_label='users', model_name='Group')
Task = django_apps.get_model(app_label='tasks', model_name='Task')

app = Celery()


def process_task_data(id_users: QuerySet[User],
                      tasks: QuerySet[Task],
                      event_text: str) -> str:
    """Общий блок перебора записей по юзерам."""
    for id_user in id_users:
        reply_text = event_text
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
def minute_by_minute_check() -> str:
    """Основной модуль оповещающий о событиях в чатах."""
    this_datetime = datetime.utcnow().replace(second=0, microsecond=0)

    tasks = Task.objects.filter(
        remind_at__startswith=this_datetime,
        it_birthday=False
    ).select_related('user', 'group').order_by('user', 'group')

    id_users = Task.objects.filter(
        remind_at__startswith=this_datetime,
        it_birthday=False
    ).order_by().values('user', 'group').distinct()
    reply_text = 'Напоминаю, о предстоящих событиях:\n'
    return process_task_data(id_users, tasks, reply_text)


@app.task
def check_birthdays() -> str:
    """Модуль оповещающий о Днях рождения."""
    this_date = datetime.today().date()

    tasks = Task.objects.filter(
       remind_at__day=this_date.day,
       remind_at__month=this_date.month,
       it_birthday=True
    ).select_related('user', 'group').order_by('user', 'group')

    id_users = Task.objects.filter(
        remind_at__day=this_date.day,
        remind_at__month=this_date.month,
        it_birthday=True
    ).order_by().values('user', 'group').distinct()

    reply_text = 'Напоминаю, что ежегодно в этот день:\n'
    return process_task_data(id_users, tasks, reply_text)


@app.task
def send_forismatic_quotes() -> str:
    """Рассылка цитат великих людей на русском языке от АПИ forismatic."""
    groups = Group.objects.all()
    request = [
        'http://api.forismatic.com/api/1.0/',
        {
            'method': 'getQuote',
            'format': 'text',
            'lang': 'ru',
        }
    ]

    for id in groups:
        try:
            response = requests.get(*request)
        except Exception as error:
            raise KeyError(error)

        msg = '*Цитата на злобу дня:*\n' + response.text
        bot.send_message(id.chat_id, msg, parse_mode='Markdown')
        time.sleep(60)
    return 'Done'

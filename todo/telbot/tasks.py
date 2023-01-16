import time
from datetime import datetime, timedelta, timezone

import pytz
import requests
from celery import Celery
from dateutil.relativedelta import relativedelta
from django.apps import apps as django_apps
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models.query import QuerySet

from .loader import bot

User = get_user_model()
Group = django_apps.get_model(app_label='users', model_name='Group')
Task = django_apps.get_model(app_label='tasks', model_name='Task')

app = Celery()

EXTEND = {
    'D': timedelta(days=1),
    'W': timedelta(days=7),
    'M': relativedelta(months=1),
    'Y': relativedelta(years=1),
}


def sending_messages(tasks: QuerySet[Task],
                     event_text: str,
                     cur_time: datetime) -> str:
    """Перебор записей и отправка их адресатам."""
    messages = dict()

    for task in tasks:
        recipient = task.group.chat_id if task.group else task.user.username
        if recipient not in messages:
            user_locally = task.user.locations.first()
            user_tz = pytz.timezone(user_locally.timezone)
            messages.update({
                recipient: {
                    'user_tz': user_tz,
                    'reply_text': '',
                }
            })
        if task.group:
            delta = task.server_datetime - cur_time
            delta_min = int(delta.total_seconds() // 60)
            if delta_min > 60:
                header = f'📝 через {delta_min // 60 }час {delta_min % 60 }мин'
            else:
                header = f'📝 через {delta_min % 60 }мин'
        else:
            utc_date = task.server_datetime
            user_date = utc_date.astimezone(messages[recipient]['user_tz'])
            header = f'В {datetime.strftime(user_date, "%H:%M")}'

        header = '' if task.it_birthday else f'- {header} -> \n'
        messages[recipient]['reply_text'] += f'- {header}{task.text}\n\n'

        if not task.it_birthday:
            if task.reminder_period == 'N':
                task.delete()
            else:
                task.server_datetime += EXTEND[task.reminder_period]
                task.save()

    for recipient, body in messages.items():
        reply_text = event_text + body['reply_text']
        bot.send_message(recipient, reply_text, parse_mode='Markdown')
    return f'Send {len(messages)} messages'


@app.task
def minute_by_minute_check() -> str:
    """Основной модуль оповещающий о событиях в чатах."""
    this_datetime = datetime.now(timezone.utc)
    start_datetime = this_datetime - timedelta(minutes=30)

    tasks = Task.objects.filter(
        remind_at__range=[start_datetime, this_datetime],
        it_birthday=False
    ).select_related('user', 'group')

    reply_text = f'[~~~~~~~]({bot.link})\n'
    return sending_messages(tasks, reply_text, this_datetime)


@app.task
def check_birthdays() -> str:
    """Модуль оповещающий о Днях рождения."""
    this_datetime = datetime.now(timezone.utc)

    tasks = Task.objects.filter(
       remind_at__day=this_datetime.day,
       remind_at__month=this_datetime.month,
       it_birthday=True
    ).select_related('user', 'group')

    reply_text = 'Не забудьте поздравить c Днём Рождения:\n'
    return sending_messages(tasks, reply_text, this_datetime)


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
    for group in groups:
        try:
            response = requests.get(*request)
            msg = (
                f'[Мысли великих людей:](https://{settings.DOMEN}/)\n'
                + response.text
            )
            bot.send_message(group.chat_id, msg, parse_mode='Markdown')
        except Exception as error:
            bot.send_message(225429268, error)
            raise KeyError(error)
        time.sleep(60)
    return f'Quotes were sent to {len(groups)} groups'

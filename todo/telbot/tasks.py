import time
from datetime import datetime, timedelta, timezone

import pytz
import requests
from celery import Celery
from dateutil.relativedelta import relativedelta
from django.apps import apps as django_apps
from django.contrib.auth import get_user_model
from django.db.models.query import QuerySet
from telegram import ParseMode

from .loader import bot

User = get_user_model()
Group = django_apps.get_model(app_label='users', model_name='Group')
Task = django_apps.get_model(app_label='tasks', model_name='Task')
GroupConnections = django_apps.get_model(
    app_label='users', model_name='GroupConnections'
)

app = Celery()

EXTEND = {
    'D': timedelta(days=1),
    'W': timedelta(days=7),
    'M': relativedelta(months=1),
    'Y': relativedelta(years=1),
}


def sending_messages(tasks: QuerySet[Task],
                     this_datetime: datetime,
                     event_text: str = '') -> str:
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
            delta = task.server_datetime - this_datetime
            delta_min = int(delta.total_seconds() / 60 + 1)
            if delta_min > 60:
                header = f'📝 через {delta_min // 60 }час {delta_min % 60 }мин'
            elif delta_min <= 0:
                header = 'Время начала:'
            else:
                header = f'📝 через {delta_min % 60 }мин'
        else:
            utc_date = task.server_datetime
            user_date = utc_date.astimezone(messages[recipient]['user_tz'])
            header = f'В {datetime.strftime(user_date, "%H:%M")}'

        header = '' if task.it_birthday else f'<b>-- {header} -></b>\n'
        picture = (
            '<a href='
            f'"{task.picture_link}">​​​​​​</a> ' if task.picture_link else ''
        )
        messages[recipient]['reply_text'] += (
            f'{header}{task.text}{picture}\n\n'
        )

        if not task.it_birthday:
            if task.reminder_period == 'N':
                task.delete()
            else:
                task.server_datetime += EXTEND[task.reminder_period]
                task.save()

    for recipient, body in messages.items():
        reply_text = event_text + body['reply_text']
        try:
            bot.send_message(
                chat_id=recipient,
                text=reply_text,
                parse_mode=ParseMode.HTML
            )
        except Exception:
            continue
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

    return sending_messages(tasks, this_datetime)


@app.task
def check_birthdays() -> str:
    """Модуль оповещающий о Днях рождения."""
    this_datetime = datetime.now(timezone.utc)

    tasks = Task.objects.filter(
       remind_at__day=this_datetime.day,
       remind_at__month=this_datetime.month,
       it_birthday=True
    ).select_related('user', 'group')

    reply_text = '<b>Сегодня не забудьте поздравить с праздником:</b>\n'
    return sending_messages(tasks, this_datetime, reply_text)


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
                '*Мысли великих людей:*\n'
                + response.text
            )
            bot.send_message(
                chat_id=group.chat_id,
                text=msg,
                parse_mode=ParseMode.MARKDOWN
            )
            time.sleep(5)
        except Exception:
            continue
    return f'Quotes were sent to {len(groups)} groups'


@app.task
def check_members() -> str:
    """
    Сверяет людей в группе с моделью GroupConnections,
    удаляет связи, если кто-то вышел из группы.
    """
    count = 0
    entries = GroupConnections.objects.prefetch_related('user', 'group')
    exit_status = ['kicked', 'left']
    for entry in entries:
        time.sleep(5)
        try:
            result = bot.getChatMember(
                entry.group.chat_id,
                entry.user.username
            )
            if result.status in exit_status:
                entry.delete()
                count += 1
        except Exception:
            continue
    return f'Delete {count} members.'

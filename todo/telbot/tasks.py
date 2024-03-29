import time
from datetime import datetime, timedelta, timezone

import pytz
import requests
from celery import Celery
from dateutil.relativedelta import relativedelta
from django.apps import apps as django_apps
from django.contrib.auth import get_user_model
from django.db.models.query import QuerySet
from telbot.loader import bot
from telbot.service_message import send_message_to_chat
from telegram import ParseMode

User = get_user_model()
Group = django_apps.get_model(app_label='users', model_name='Group')
GroupMailing = django_apps.get_model(app_label='users', model_name='GroupMailing')
Task = django_apps.get_model(app_label='tasks', model_name='Task')
GroupConnections = django_apps.get_model(app_label='users', model_name='GroupConnections')
TelegramMailing = django_apps.get_model(app_label='advertising', model_name='TelegramMailing')

app = Celery()

EXTEND = {
    'D': timedelta(days=1),
    'W': timedelta(days=7),
    'M': relativedelta(months=1),
    'Y': relativedelta(years=1),
}

STYLING_HTML = {
    '<p>': '',
    '</p>': '\n',
    '</blockquote>': '</blockquote>\n',
    '&nbsp;': '',
}


def sending_messages(tasks: QuerySet, this_datetime: datetime, event_text: str = '') -> str:
    """Перебор записей и отправка их адресатам."""
    messages = dict()
    delete_tasks = []
    for task in tasks:
        recipient = task.group.chat_id if task.group else task.user.tg_id
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
            if delta_min >= 60:
                header = f'📝 через {delta_min // 60 }час {delta_min % 60 }мин'
            elif delta_min <= 0:
                header = 'Время начала:'
            else:
                header = f'📝 через {delta_min % 60 }мин'
        else:
            user_date = task.server_datetime.astimezone(messages[recipient]['user_tz'])
            header = f'В {datetime.strftime(user_date, "%H:%M")}'

        header = '' if task.it_birthday else f'<b>-- {header} -></b>'
        picture = f'<a href="{ task.image.url if task.image else task.picture_link }">​​​​​​</a>'
        messages[recipient]['reply_text'] += f'{header}{picture}\n\n{task.text}\n\n'

        if not task.it_birthday:
            if task.reminder_period == 'N':
                delete_tasks.append(task.id)
            else:
                task.server_datetime += EXTEND[task.reminder_period]
                task.save()

    for recipient, body in messages.items():
        reply_text = event_text + body['reply_text']
        for old, new in STYLING_HTML.items():
            reply_text = reply_text.replace(old, new)
        send_message_to_chat(tg_id=recipient, message=reply_text, parse_mode=ParseMode.HTML)

    if len(delete_tasks):
        Task.objects.filter(id__in=delete_tasks).delete()

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
        server_datetime__day=this_datetime.day,
        server_datetime__month=this_datetime.month,
        it_birthday=True
    ).select_related('user', 'group')

    reply_text = '<b>Сегодня не забудьте поздравить с праздником:</b>\n'
    return sending_messages(tasks, this_datetime, reply_text)


@app.task
def send_forismatic_quotes() -> str:
    """Рассылка цитат великих людей на русском языке от АПИ forismatic."""
    mailing_list = GroupMailing.objects.select_related('group')
    count = 0

    request = [
        'http://api.forismatic.com/api/1.0/',
        {
            'method': 'getQuote',
            'format': 'text',
            'lang': 'ru',
        }
    ]
    for mailing_groups in mailing_list:
        if mailing_groups.mailing_type == 'forismatic_quotes':
            try:
                response = requests.get(*request)  # TODO переделать на HTTPX для сокращения библиотек
                msg = '*Мысли великих людей:*\n' + response.text
                bot.send_message(
                    chat_id=mailing_groups.group.chat_id,
                    text=msg,
                    parse_mode=ParseMode.MARKDOWN
                )
                count += 1
                time.sleep(5)
            except Exception:
                continue
    return f'Quotes were sent to {count} groups'


@app.task
def send_telegram_mailing() -> str:
    """Рассылка Телеграмм спама. Проверка каждый час."""
    current_time = datetime.now(timezone.utc)
    start_time = current_time - timedelta(minutes=10)
    mailing_list = TelegramMailing.objects.filter(remind_at__range=[start_time, current_time])
    count = 0

    for item in mailing_list:
        if item.target == 'u':
            recipients = User.objects.all().exclude(tg_id=None)
        else:
            recipients = Group.objects.all()

        link = item.reference if item.reference else item.image.url
        message_text = f'<a href="{link}">​​​​​​</a>\n{item.text}'
        for old, new in STYLING_HTML.items():
            message_text = message_text.replace(old, new)

        for recipient in recipients:
            send_message_to_chat(
                tg_id=recipient.tg_id if item.target == 'u' else recipient.chat_id,
                message=message_text,
                parse_mode=ParseMode.HTML
            )
            count += 1
    return f'Telegram Mailing sent to {count} objects'

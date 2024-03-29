from __future__ import absolute_import, unicode_literals

import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'todo.settings')

app = Celery('todo')

app.conf.enable_utc = True

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()

# Celery Beat Settings
app.conf.beat_schedule = {
    'check-db-every-minute': {
        'task': 'telbot.tasks.minute_by_minute_check',
        'schedule': crontab(),
    },
    'send-birthdays': {
        'task': 'telbot.tasks.check_birthdays',
        'schedule': crontab(hour=4, minute=30),
    },
    'send-forismatic': {
        'task': 'telbot.tasks.send_forismatic_quotes',
        'schedule': crontab(hour=7, minute=0),
    },
    'backup': {
        'task': 'core.tasks.backup',
        'schedule': crontab(hour=1, minute=0),
    },
    'send_telegram_mailing': {
        'task': 'telbot.tasks.send_telegram_mailing',
        'schedule': crontab(minute='*/10'),
    },
    'load_stat_data_to_postgres': {
        'task': 'stats.tasks.load_to_database',
        'schedule': crontab(minute='*/60'),
    },
}

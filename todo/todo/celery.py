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
    'set_ip': {
        'task': 'core.tasks.set_ip_to_dns',
        'schedule': crontab(hour='*/2', minute=0),
    },
    'send-birthdays': {
        'task': 'telbot.tasks.check_birthdays',
        'schedule': crontab(hour=4, minute=30),
    },
    'send-forismatic': {
        'task': 'telbot.tasks.send_forismatic_quotes',
        'schedule': crontab(hour=7, minute=0),
    },
}

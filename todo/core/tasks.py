from celery import Celery
from django.core import management

app = Celery()


@app.task
def backup():
    """Дамп базы данных."""
    management.call_command('dbbackup')
    return 'Database backup has been created'

import os

from botocore.exceptions import ClientError
from celery import Celery, shared_task
from django.conf import settings
from django.core import management

app = Celery()
client = settings.S3_CLIENT
BUCKET_NAME = settings.MEDIA_BUCKET_NAME


@shared_task
def delete_image_in_bucket(url: str, bucket: str = BUCKET_NAME):
    """Удаление картинки из бакета в облаке."""
    key = '/'.join(url.split('/')[-2:])
    try:
        client.delete_object(Bucket=bucket, Key=key)
        return f"Картинка {key} удалена успешно."
    except ClientError as e:
        return f"Ошибка при удалении объекта из бакета: {e}"


@shared_task
def delete_image_in_local(path):
    try:
        os.remove(path)
    except OSError as e:
        return f"Ошибка при удалении объекта из локального каталога: {e}"


@app.task
def backup():
    """Дамп базы данных."""
    management.call_command('dbbackup')
    return 'Database backup has been created'

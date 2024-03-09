import os

from botocore.exceptions import ClientError
from celery import Celery, shared_task
from django.conf import settings
from django.core import management

app = Celery()
client = settings.S3_CLIENT
BUCKET_NAME = settings.MEDIA_BUCKET_NAME


@shared_task
def delete_image_in_bucket(url: str, bucket: str = BUCKET_NAME) -> str:
    """
    Задача на удаление картинки из бакета в облаке.

    ### Args:
    - url (`str`): Полный url к картинке на бакете.
    - bucket (`str`, optional): Имя бакета. По умолчанию `settings.MEDIA_BUCKET_NAME`.

    """
    key = '/'.join(url.split('/')[-2:])
    try:
        client.delete_object(Bucket=bucket, Key=key)
        return f"Картинка {key} удалена успешно."
    except ClientError as e:
        return f"Ошибка при удалении объекта из бакета: {e}"


@shared_task
def delete_image_in_local(path) -> str:
    """
    Задача на удаление картинки хранящейся локально.

    ### Args:
    - path (`str`): Полный путь к локальной картинке.

    """
    try:
        os.remove(path)
        return f"Картинка по адресу {path} удалена успешно."
    except OSError as e:
        return f"Ошибка при удалении объекта из локального каталога: {e}"


@app.task
def backup():
    """Дамп базы данных."""
    management.call_command('dbbackup')
    return 'Database backup has been created'

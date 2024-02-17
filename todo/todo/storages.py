import os
from datetime import datetime
from io import BytesIO

from django.conf import settings
from django.core.files.uploadedfile import InMemoryUploadedFile
from PIL import Image
from pytils.translit import slugify
from storages.backends.s3boto3 import S3Boto3Storage, S3StaticStorage


class StaticStorage(S3StaticStorage):
    bucket_name = settings.STATIC_BUCKET_NAME
    default_acl = 'public-read'
    file_overwrite = False


class MediaStorage(S3Boto3Storage):
    bucket_name = settings.MEDIA_BUCKET_NAME
    default_acl = 'public-read'
    file_overwrite = False


class DataBaseStorage(S3Boto3Storage):
    default_acl = 'private'
    bucket_name = settings.DATABASE_BUCKET_NAME
    file_overwrite = False


class CkeditorStorage(S3StaticStorage):
    bucket_name = settings.CKEDITOR_BUCKET_NAME
    default_acl = 'public-read'
    file_overwrite = False


class CkeditorCustomStorage(CkeditorStorage):
    """Custom storage for django_ckeditor_5 images."""

    def get_folder_name(self):
        """Получить имя папки основываясь на текущей дате."""
        return datetime.now().strftime('%Y/%m/%d')

    def get_name(self, name):
        """Получить имя файла и его расширение."""
        file_name, file_extension = os.path.splitext(name.lower())
        folder_name = self.get_folder_name()
        return os.path.join(folder_name, slugify(file_name)), file_extension

    def _save(self, name, content):
        """Сохранение файла в хранилище, конвертируя изображения в формат WEBP."""
        name, file_extension = self.get_name(name)

        if file_extension in ['.jpg', '.jpeg', '.png', '.gif']:
            img = Image.open(content)
            webp_name = name + ".webp"

            webp_buffer = BytesIO()
            img.save(webp_buffer, "WEBP")
            webp_buffer.seek(0)
            content = InMemoryUploadedFile(webp_buffer, None, webp_name, 'image/webp', webp_buffer.tell(), None)
            return super()._save(webp_name, content)

        return super()._save(name + file_extension, content)

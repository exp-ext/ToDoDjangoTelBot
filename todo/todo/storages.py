import os
from datetime import datetime

from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage, S3StaticStorage


class StaticStorage(S3Boto3Storage):
    bucket_name = settings.STATIC_BUCKET_NAME
    default_acl = 'private'


class MediaStorage(S3Boto3Storage):
    bucket_name = settings.MEDIA_BUCKET_NAME
    default_acl = 'private'


class DataBaseStorage(S3Boto3Storage):
    default_acl = 'private'
    bucket_name = settings.DATABASE_BUCKET_NAME


class CkeditorStorage(S3StaticStorage):
    bucket_name = settings.CKEDITOR_BUCKET_NAME
    default_acl = 'public'


class CkeditorCustomStorage(CkeditorStorage):
    """Custom storage for django_ckeditor_5 images."""

    def get_folder_name(self):
        return datetime.now().strftime('%Y/%m/%d')

    def _save(self, name, content):
        folder_name = self.get_folder_name()
        name = os.path.join(folder_name, name)
        return super()._save(name, content)

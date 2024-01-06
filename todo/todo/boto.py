from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage


class StaticStorage(S3Boto3Storage):
    bucket_name = settings.STATIC_BUCKET_NAME
    default_acl = 'private'


class MediaStorage(S3Boto3Storage):
    bucket_name = settings.MEDIA_BUCKET_NAME
    default_acl = 'private'


class DataBaseStorage(S3Boto3Storage):
    default_acl = 'private'
    bucket_name = settings.DATABASE_BUCKET_NAME

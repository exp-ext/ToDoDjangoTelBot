from storages.backends.s3boto3 import S3Boto3Storage
from django.conf import settings


class StaticStorage(S3Boto3Storage):
    location = settings.STATIC_BUCKET_NAME
    default_acl = 'public-read'


class MediaStorage(S3Boto3Storage):
    location = settings.MEDIA_BUCKET_NAME
    default_acl = 'public-read'


class DataBaseStorage(S3Boto3Storage):
    default_acl = 'private'
    bucket_name = settings.DATABASE_BUCKET_NAME

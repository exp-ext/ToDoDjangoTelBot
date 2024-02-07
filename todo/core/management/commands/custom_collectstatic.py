from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Custom collectstatic command to change STATIC_URL for Minio'

    def handle(self, *args, **options):
        original_static_url = settings.STATIC_URL
        settings.STATIC_URL = 'http://127.0.0.1:9000/todo-static/'
        original_endpoint_url = settings.AWS_S3_ENDPOINT_URL
        settings.AWS_S3_ENDPOINT_URL = 'http://127.0.0.1:9000'

        call_command('collectstatic', *args, **options)

        settings.STATIC_URL = original_static_url
        settings.AWS_S3_ENDPOINT_URL = original_endpoint_url

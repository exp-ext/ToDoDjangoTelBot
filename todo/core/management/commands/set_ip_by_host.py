from core.tasks import set_ip_to_dns
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Конвертор данных cvs to db.sqlite3'

    def handle(self, *args, **options):
        try:
            result = set_ip_to_dns()
        except Exception as error:
            raise CommandError(error)
        if result:
            self.stdout.write(self.style.SUCCESS(result))
        else:
            self.stdout.write(self.style.ERROR_OUTPUT(
                'Что-то пошло не так'
            ))

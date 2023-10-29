from django.core.management.base import BaseCommand, CommandError
from stats.tasks import load_to_database


class Command(BaseCommand):
    help = 'Выгрузка данных из Redis в Postgres'

    def handle(self, *args, **options):
        try:
            answer = load_to_database()
        except Exception as error:
            raise CommandError(error)

        self.stdout.write(self.style.SUCCESS(answer))

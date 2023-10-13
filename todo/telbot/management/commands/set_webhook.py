from django.core.management.base import BaseCommand, CommandError

from ._set_webhook import set_webhook


class Command(BaseCommand):
    help = 'Конвертор данных cvs to db.sqlite3'

    def handle(self, *args, **options):
        try:
            result = set_webhook()
        except Exception as error:
            raise CommandError(error)
        if result:
            self.stdout.write(self.style.SUCCESS(
                'Webhook успешно назначен'
            ))
        else:
            self.stdout.write(self.style.ERROR_OUTPUT(
                'Что-то пошло не так'
            ))

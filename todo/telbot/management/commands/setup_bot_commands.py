from django.core.management.base import BaseCommand, CommandError
from telbot.commands import set_up_commands


class Command(BaseCommand):
    help = 'Конвертор данных cvs to db.sqlite3'

    def handle(self, *args, **options):
        try:
            result = set_up_commands()
        except Exception as error:
            raise CommandError(error)
        if result:
            self.stdout.write(self.style.SUCCESS(
                'Команды меню успешно назначены'
            ))
        else:
            self.stdout.write(self.style.ERROR_OUTPUT(
                'Что-то пошло не так'
            ))

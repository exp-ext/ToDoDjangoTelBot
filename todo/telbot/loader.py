from django.conf import settings
from telegram import Bot

DOMAIN_URL = settings.DOMAIN
TOKEN = settings.TOKEN


def check_tokens():
    """Проверка доступности переменных среды.."""
    env_vars = {
        'TOKEN': TOKEN,
        'OW_API_ID': settings.OW_API_ID,
        'DOMAIN': DOMAIN_URL,
    }
    for key, value in env_vars.items():
        if not value or value == '':
            raise SystemExit(f'Нет значения для: {key}')
    return True


if check_tokens():
    bot = Bot(token=TOKEN)

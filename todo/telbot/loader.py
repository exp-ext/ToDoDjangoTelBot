from django.conf import settings
from telegram import Bot

DOMAIN_URL = settings.DOMAIN
TELEGRAM_TOKEN = settings.TELEGRAM_TOKEN


def check_tokens():
    """Проверка доступности переменных среды.."""
    env_vars = {
        'TELEGRAM_TOKEN': TELEGRAM_TOKEN,
        'DOMAIN': DOMAIN_URL,
    }
    for key, value in env_vars.items():
        if not value or value == '':
            raise SystemExit(f'Нет значения для: {key}')
    return True


if check_tokens():
    bot = Bot(token=TELEGRAM_TOKEN)

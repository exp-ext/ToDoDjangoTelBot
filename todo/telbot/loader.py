from typing import Any, Dict

import requests
from django.conf import settings
from telegram import Bot

DOMEN_URL = settings.DOMEN
TOKEN = settings.TOKEN
WEBHOOK_URL = f'{DOMEN_URL}/bot/{TOKEN}/webhooks/'


def check_tokens():
    """Проверка доступности переменных среды.."""
    env_vars = {
        'TOKEN': TOKEN,
        'OW_API_ID': settings.OW_API_ID,
        'DOMEN': DOMEN_URL,
        # 'DATABASE_URL': DATABASE_URL,
    }
    for key, value in env_vars.items():
        if not value or value == '':
            raise SystemExit(f'Нет значения для: {key}')
    return True


def set_webhook() -> Dict[str, Any]:
    """Назначение webhook для бота."""
    url = f'https://api.telegram.org/bot{TOKEN}/setWebhook'
    params = {
        "url": WEBHOOK_URL,
    }
    try:
        response = requests.get(url, params=params)
        return response.json()
    except Exception as error:
        SystemExit(f'Ошибка при назначении WEBHOOK: {error}')


# start bot
if check_tokens() and set_webhook().get('ok'):
    bot = Bot(token=TOKEN)

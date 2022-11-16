from typing import Any, Dict

import requests
from django.conf import settings
from telbot.processor import ScheduleProcess
from telegram import Bot


def check_tokens():
    """Проверка доступности переменных среды.."""
    env_vars = {
        'TOKEN': settings.TOKEN,
        'OW_API_ID': settings.OW_API_ID,
        'DOMEN': settings.DOMEN,
        # 'DATABASE_URL': DATABASE_URL,
    }
    for key, value in env_vars.items():
        if not value or value == '':
            raise SystemExit(f'Нет значения для: {key}')
    return True


def set_webhook() -> Dict[str, Any]:
    """Назначение webhook для бота."""
    url = f'https://api.telegram.org/bot{settings.TOKEN}/setWebhook'
    params = {
        "url": f'{settings.DOMEN}/bot/{settings.TOKEN}/webhooks/',
    }
    try:
        response = requests.get(url, params=params)
        return response.json()
    except Exception as error:
        SystemExit(f'Ошибка при назначении WEBHOOK: {error}')


# start bot
if check_tokens() and set_webhook().get('ok'):
    bot = Bot(token=settings.TOKEN)

# start another process
# ScheduleProcess.threading_process()

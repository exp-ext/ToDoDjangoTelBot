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
    }
    for key, value in env_vars.items():
        if not value or value == '':
            raise SystemExit(f'Нет значения для: {key}')
    return True


# start bot  and set_webhook().get('ok')
if check_tokens():
    bot = Bot(token=TOKEN)
    bot.delete_webhook()
    bot.set_webhook(url=WEBHOOK_URL)

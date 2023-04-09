from django.conf import settings
from telegram import Bot

from ...loader import check_tokens

DOMAIN_URL = settings.DOMAIN
TELEGRAM_TOKEN = settings.TELEGRAM_TOKEN
WEBHOOK_URL = f'www.{DOMAIN_URL}/bot/{TELEGRAM_TOKEN}/webhooks/'


def set_webhook() -> bool:
    if check_tokens():
        bot = Bot(token=TELEGRAM_TOKEN)
        bot.delete_webhook()
        return bot.set_webhook(url=WEBHOOK_URL)
    return False

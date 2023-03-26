from django.conf import settings
from telegram import Bot

from ...loader import check_tokens

DOMAIN_URL = settings.DOMAIN
TOKEN = settings.TOKEN
WEBHOOK_URL = f'www.{DOMAIN_URL}/bot/{TOKEN}/webhooks/'


def set_webhook() -> bool:
    if check_tokens():
        bot = Bot(token=TOKEN)
        bot.delete_webhook()
        return bot.set_webhook(url=WEBHOOK_URL)
    return False

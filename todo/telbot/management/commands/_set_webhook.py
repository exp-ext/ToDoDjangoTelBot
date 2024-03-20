import requests
from django.conf import settings
from telegram import Bot
from telegram.utils.request import Request

from ...loader import check_tokens

DOMAIN_URL = f'https://{settings.DOMAINPREFIX}.{settings.DOMAIN}'
TELEGRAM_TOKEN = settings.TELEGRAM_TOKEN
TELEGRAM_SECRET_KEY = settings.TELEGRAM_SECRET_KEY
WEBHOOK_URL = f'{DOMAIN_URL}/bot/{TELEGRAM_SECRET_KEY}/webhooks/'


def set_webhook() -> bool:
    if check_tokens():
        request = Request(con_pool_size=8)
        bot = Bot(token=TELEGRAM_TOKEN, request=request)
        bot.delete_webhook()
        return bot.set_webhook(url=WEBHOOK_URL)
    return False


def set_webhook_requests() -> bool:
    if check_tokens():
        return requests.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/setWebhook?url={WEBHOOK_URL}")
    return False

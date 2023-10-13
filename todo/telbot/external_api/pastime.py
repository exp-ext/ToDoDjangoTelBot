import requests
from telegram import Update
from telegram.ext import CallbackContext

from ..cleaner import remove_keyboard


def new_cat() -> str:
    """Возвращает случайную ссылку на картинку от АПИ thecatapi."""
    url = 'https://api.thecatapi.com/v1/images/search'
    new_url = 'https://api.thedogapi.com/v1/images/search'
    try:
        response = requests.get(url)
    except Exception:
        response = requests.get(new_url)
    response = response.json()
    return response[0].get('url')


def get_new_image(update: Update, context: CallbackContext):
    """Отправляет в час картинку с котиками или собачками."""
    chat = update.effective_chat
    context.bot.send_photo(chat.id, new_cat())
    remove_keyboard(update, context)

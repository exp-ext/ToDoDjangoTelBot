from random import choice

import requests
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import CallbackContext


def joke_parsing(all: bool = False) -> str:
    """Парсинг сайта с анекдотами."""
    try:
        resp = requests.get('https://anekdotbar.ru/')

        bs_data = BeautifulSoup(resp.text, "html.parser")
        an_text = bs_data.select('.tecst')
        response_list = []

        for x in an_text:
            joke = x.getText().strip().split('\n')[0]
            response_list.append(joke)

        return choice(response_list)

    except Exception as exc:
        return f'ошибочка вышла - {exc}'


def show_joke(update: Update, context: CallbackContext) -> None:
    """Отправляет анекдот в час вызвавший функцию."""
    chat = update.effective_chat

    context.bot.send_message(chat.id, joke_parsing())

    del_menu_id = update.effective_message.message_id
    context.bot.delete_message(chat.id, del_menu_id)

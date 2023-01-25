import os

import requests
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import CallbackContext

from ..checking import check_registration

load_dotenv()

X_RAPID_API_KEY = os.getenv('X_RAPID_API_KEY')


def translate(text: str, to_language: str) -> str:
    """
    Принимает:
    - text (:obj:`str`) - текст для перевода
    - to_language (:obj:`str`) - язык на который нужен перевод

    Возвращает перевод с API Microsoft Translator Text.
    """

    url = 'https://microsoft-translator-text.p.rapidapi.com/translate'

    querystring = {
        'to': to_language,
        'api-version': '3.0',
        'profanityAction': 'NoAction',
        'textType': 'plain',
        'suggestedFrom': 'ru'
    }

    payload = [{'Text': text}]
    headers = {
        'content-type': 'application/json',
        'X-RapidAPI-Key': X_RAPID_API_KEY,
        'X-RapidAPI-Host': 'microsoft-translator-text.p.rapidapi.com'
    }

    try:
        response = requests.post(
            url=url,
            json=payload,
            headers=headers,
            params=querystring
        )
        answer = response.json()[0].get('translations')[0].get('text')
    except Exception as error:
        raise KeyError(error)
    return answer


def send_translation(update: Update, context: CallbackContext):
    """
    Описание.
    """
    answers = {
        '':  ('К сожалению перевод доступен только для  '
              '[зарегистрированных пользователей]'
              f'({context.bot.link}).'),
    }
    if check_registration(update, context, answers) is False:
        return 'Bad register'

    chat = update.effective_chat
    mes = tuple(x.strip() for x in update.message.text.split('->'))

    if len(mes[0]) == 2 or len(mes[1]) == 2:
        param = (
            (mes[0], mes[1]) if len(mes[1]) == 2 else (mes[1], mes[0])
        )
        try:
            answer = translate(*param)
        except Exception:
            answer = 'Интересный случай возник 🤪, скоро разберёмся.'
    else:
        answer = 'Не смог найти язык для перевода 🙃'

    context.bot.send_message(
        chat_id=chat.id,
        reply_to_message_id=update.message.message_id,
        text=answer
    )
    return 'Done'

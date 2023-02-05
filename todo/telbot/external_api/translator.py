import os

import requests
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import CallbackContext

from ..checking import check_registration

load_dotenv()

X_RAPID_API_KEY = os.getenv('X_RAPID_API_KEY')

TOKEN_TRANSLATION_API = os.getenv('TOKEN_TRANSLATION_API')


def libre_translator(text: str, to_language: str) -> str:
    url = 'https://libretranslate.com/translate'
    headers = {
        'Content-Type': 'application/json',
    }
    payload = {
        'q': text,
        'source': 'auto',
        'target': to_language
    }
    try:
        response = requests.post(
                url=url,
                headers=headers,
                json=payload
            )
        answer = response.json().get('data').get('translation')
    except Exception as error:
        raise KeyError(error)
    return answer


def translate_translator(text: str, to_language: str) -> str:
    """
    Принимает:
    - text (:obj:`str`) - текст для перевода
    - to_language (:obj:`str`) - язык на который нужен перевод

    Возвращает перевод с API www.translate.com.
    """
    url = 'https://api.translate.com/translate/v1/mt'
    headers = {
        'Authorization': f'Bearer {TOKEN_TRANSLATION_API}',
    }

    payload = {
        'text': text,
        'source_language': 'ru',
        'translation_language': to_language
    }

    try:
        response = requests.post(
                url=url,
                headers=headers,
                json=payload
            )
        answer = response.json().get('data').get('translation')
    except Exception as error:
        raise KeyError(error)
    return answer


def deepl_translator(text: str, to_language: str) -> str:
    """
    Принимает:
    - text (:obj:`str`) - текст для перевода
    - to_language (:obj:`str`) - язык на который нужен перевод

    Возвращает перевод с API DeepL Translator.
    """

    url = 'https://deepl-translator1.p.rapidapi.com/translate'

    querystring = {
        'text': text,
        'target_lang': to_language
    }

    headers = {
        'X-RapidAPI-Key': X_RAPID_API_KEY,
        'X-RapidAPI-Host': 'deepl-translator1.p.rapidapi.com'
    }

    try:
        response = requests.get(
            url=url,
            headers=headers,
            params=querystring
        )
        answer = response.json().get('translations')[0].get('text')
    except Exception as error:
        raise KeyError(error)
    return answer


def microsoft_translator(text: str, to_language: str) -> str:
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
            answer = deepl_translator(*param)
        except Exception as error:
            context.bot.send_message(225429268, error)
            answer = 'Интересный случай возник 🤪, скоро разберёмся.'
    else:
        answer = 'Не смог найти язык для перевода 🙃'

    context.bot.send_message(
        chat_id=chat.id,
        reply_to_message_id=update.message.message_id,
        text=answer
    )
    return 'Done'

import os

import openai
import requests
from django.contrib.auth import get_user_model
from dotenv import load_dotenv
from telegram import InputMediaPhoto, ParseMode, Update
from telegram.ext import CallbackContext, ConversationHandler

from ..checking import check_registration
from ..cleaner import remove_keyboard

load_dotenv()

APY_KEY = os.getenv('CHAT_GP_TOKEN')
openai.api_key = APY_KEY

User = get_user_model()


def first_step_get_image(update: Update, context: CallbackContext):
    chat = update.effective_chat
    req_text = (
        f'*{update.effective_user.first_name}*, '
        'введите текст для генерации картинки на английском языке'
    )
    message_id = context.bot.send_message(
        chat.id,
        req_text,
        parse_mode=ParseMode.MARKDOWN
    ).message_id
    context.user_data['image_gen'] = message_id
    remove_keyboard(update, context)
    return 'image_gen'


def get_image_dall_e(update: Update, context: CallbackContext):
    """
    Возвращает серию картинок от АПИ Dall-e 2.
    Предварительно вызвав функцию проверки регистрации.
    """
    answers = {
        '': ('К сожалению данная функция доступна только для '
             '[зарегистрированных пользователей]'
             f'({context.bot.link})'),
    }
    if check_registration(update, context, answers) is False:
        return 'Bad register'

    chat = update.effective_chat
    prompt = update.message.text

    del_id = context.user_data['image_gen']
    context.bot.delete_message(chat.id, del_id)

    prompt = update.message.text

    model_engine = 'image-alpha-001'

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {APY_KEY}'
    }
    payload = {
        'prompt': prompt,
        'model': model_engine,
        'n': 5,
        'size': '1024x1024',
        'response_format': 'url'
    }
    openai_api_url = 'https://api.openai.com/v1/images/generations'

    media_group = []

    try:
        response = requests.post(openai_api_url, json=payload, headers=headers)

        for number, url in enumerate(response.json()['data']):
            media_group.append(
                InputMediaPhoto(media=url['url'], caption=f'Gen № {number}')
            )

        context.bot.send_media_group(
            chat_id=chat.id,
            reply_to_message_id=update.message.message_id,
            media=media_group
        )
    except Exception:
        response = openai.Image.create(
            prompt=prompt,
            n=5,
            size='1024x1024'
        )
        for number, url in enumerate(response['data']):
            media_group.append(
                InputMediaPhoto(media=url['url'], caption=f'Gen № {number}')
            )
        context.bot.send_media_group(
            chat_id=chat.id,
            reply_to_message_id=update.message.message_id,
            media=media_group
        )
    finally:
        return ConversationHandler.END

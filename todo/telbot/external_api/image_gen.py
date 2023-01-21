import os

import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from dotenv import load_dotenv
from telegram import ParseMode, Update
from telegram.ext import CallbackContext, ConversationHandler

from ..cleaner import process_to_delete_message, remove_keyboard
from ..menus import assign_group

load_dotenv()

APY_KEY = os.getenv('CHAT_GP_TOKEN')

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
    chat = update.effective_chat
    user_tel = update.effective_user
    user = User.objects.filter(username=user_tel.id)
    text = None
    prompt = update.message.text

    del_id = context.user_data['image_gen']
    context.bot.delete_message(chat.id, del_id)

    if not user[0].first_name:
        text = (
            'Я мог бы ответить, но не знаю как к Вам обращаться?\n'
            'Есть 2 варианта решения.\n'
            '1 - добавить имя в личном кабинете '
            f'[WEB версии](https://{settings.DOMEN}/\n'
            '2 - в настройках Телеграмма и заново пройти регистрацию'
        )
    if text:
        message_id = context.bot.send_message(
            chat_id=chat.id,
            reply_to_message_id=update.message.message_id,
            text=text,
            parse_mode=ParseMode.MARKDOWN
        ).message_id
        *params, = chat.id, message_id, 20
        process_to_delete_message(params)
        return 'Bad user model'

    assign_group(update)

    prompt = update.message.text

    model_engine = 'image-alpha-001'

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {APY_KEY}'
    }
    payload = {
        'prompt': prompt,
        'model': model_engine,
        'size': '1024x1024',
        'response_format': 'url'
    }
    openai_api_url = 'https://api.openai.com/v1/images/generations'

    try:
        response = requests.post(openai_api_url, json=payload, headers=headers)

        context.bot.send_photo(
            chat_id=chat.id,
            reply_to_message_id=update.message.message_id,
            photo=response.json()['data'][0]['url']
        )
    except Exception as error:
        raise KeyError(error)
    finally:
        return ConversationHandler.END

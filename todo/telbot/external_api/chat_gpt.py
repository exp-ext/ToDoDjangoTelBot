import os

import openai
from django.conf import settings
from django.contrib.auth import get_user_model
from dotenv import load_dotenv
from telegram import ParseMode, Update
from telegram.ext import CallbackContext

from ..cleaner import process_to_delete_message
from ..menus import assign_group

load_dotenv()

openai.api_key = os.getenv('CHAT_GP_TOKEN')

User = get_user_model()


def get_answer_davinci(update: Update, context: CallbackContext):
    chat = update.effective_chat
    user_tel = update.effective_user
    user = User.objects.filter(username=user_tel.id)
    text = None
    prompt = update.message.text.replace('#', '')
    answers = {
        '?': ('Я мог бы ответить Вам, если '
              f'[зарегистрируетесь]({context.bot.link}) 🧐'),
        '!': ('Я обязательно поддержу Вашу дискуссию, если '
              f'[зарегистрируетесь]({context.bot.link}) 🙃'),
        '':  ('Какая интересная беседа, [зарегистрируетесь]'
              f'({context.bot.link}) и я подключусь к ней 😇'),
    }
    if not user:
        for key, _ in answers.items():
            if key in prompt:
                text = answers[key]
                break
    elif not user[0].first_name:
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

    model_engine = 'text-davinci-003'

    try:
        answer = openai.Completion.create(
            engine=model_engine,
            prompt=prompt,
            max_tokens=2048,
            temperature=0.3,
            top_p=0,
            frequency_penalty=0,
            presence_penalty=0,
        )

        context.bot.send_message(
            chat_id=chat.id,
            reply_to_message_id=update.message.message_id,
            text=answer.choices[0].text
        )
    except Exception as error:
        context.bot.send_message(225429268, error)
        raise KeyError(error)
    return 'Done'

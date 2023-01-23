import os

import openai
from django.contrib.auth import get_user_model
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import CallbackContext

from ..checking import check_registration

load_dotenv()

openai.api_key = os.getenv('CHAT_GP_TOKEN')

User = get_user_model()


def get_answer_davinci(update: Update, context: CallbackContext):
    """
    Возвращает ответ от API ИИ ChatGPT.
    Предварительно вызвав функцию проверки регистрации.
    """
    answers = {
        '?': ('Я мог бы ответить Вам, если '
              f'[зарегистрируетесь]({context.bot.link}) 🧐'),
        '!': ('Я обязательно поддержу Вашу дискуссию, если '
              f'[зарегистрируетесь]({context.bot.link}) 🙃'),
        '':  ('Какая интересная беседа, [зарегистрируетесь]'
              f'({context.bot.link}) и я подключусь к ней 😇'),
    }

    if check_registration(update, context, answers) is False:
        return 'Bad register'

    chat = update.effective_chat
    prompt = update.message.text.replace('#', '')
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

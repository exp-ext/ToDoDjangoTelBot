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
ADMIN_ID = os.getenv('ADMIN_ID')


def request_to_openai(prompt: str) -> str:
    """
    Делает запрос в OpenAI.

    На входе принимает текст для запроса (:obj:`str`)

    Возвращает результат в виде текста или исключение.
    """
    try:
        answer = openai.Completion.create(
            engine='text-davinci-003',
            prompt=prompt,
            max_tokens=2048,
            temperature=0.3,
            top_p=0,
            frequency_penalty=0,
            presence_penalty=0,
        )
        answer_text = answer.choices[0].text
    except Exception:
        answer = openai.Completion.create(
            engine='text-davinci-002',
            prompt=prompt,
            max_tokens=2048,
            temperature=0.5,
            top_p=0,
            frequency_penalty=0,
            presence_penalty=0,
        )
        answer_text = answer.choices[0].text
    return answer_text


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

    try:
        text = request_to_openai(prompt)

    except Exception as error:
        text = (
            'Что-то пошло не так 🤷🏼\n'
            'Возможно большой наплыв запросов, '
            'которые я не успеваю обрабатывать 🤯'
        )
        context.bot.send_message(chat_id=ADMIN_ID, text=error)
    finally:
        context.bot.send_message(
            chat_id=chat.id,
            reply_to_message_id=update.message.message_id,
            text=text
        )
    return 'Done'

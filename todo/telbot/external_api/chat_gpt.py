import os
from datetime import datetime, timedelta, timezone

import openai
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import CallbackContext

from ..checking import check_registration
from ..models import HistoryAI

load_dotenv()

openai.api_key = os.getenv('CHAT_GP_TOKEN')

User = get_user_model()
ADMIN_ID = os.getenv('ADMIN_ID')

ERROR_TEXT = (
    'Что-то пошло не так 🤷🏼\n'
    'Возможно большой наплыв запросов, '
    'которые я не успеваю обрабатывать 🤯'
)


def add_history(history, len_initial_text):
    """Возвращает форматированную историю."""
    prompt = ''
    count = 0
    for item in history:
        if not item.answer or item.answer == ERROR_TEXT:
            continue
        dialog = f'- {item.question}\n- {item.answer}\n\n'
        if len(prompt) + len(dialog) + len_initial_text >= 2049:
            break
        prompt += dialog
        count += 1
    return prompt


def request_to_openai(prompt: str) -> str:
    """
    Делает запрос в OpenAI.

    На входе принимает:
    - текст для запроса (:obj:`str`)

    Возвращает результат в виде текста или исключение.
    """
    answer_text = ''
    try:
        answer = openai.Completion.create(
            engine='text-davinci-003',
            prompt=prompt,
            max_tokens=2048,
            temperature=0.3,
            frequency_penalty=0,
            presence_penalty=0
        )
        answer_text = answer.choices[0].text
        if not answer_text:
            raise ValueError("not text")
    except Exception:
        answer = openai.Completion.create(
            engine='text-davinci-003',
            prompt=prompt,
            max_tokens=2048,
            temperature=0.7,
            frequency_penalty=0,
            presence_penalty=0
        )
        answer_text = answer.choices[0].text
    finally:
        if not answer_text:
            raise ValueError("not text")
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
        '': ('Какая интересная беседа, [зарегистрируетесь]'
             f'({context.bot.link}) и я подключусь к ней 😇'),
    }

    if check_registration(update, context, answers) is False:
        return 'Bad register'

    chat = update.effective_chat
    user = get_object_or_404(
        User,
        username=update.effective_user.id
    )
    message_text = update.message.text.replace('#', '', 1)

    this_datetime = datetime.now(timezone.utc)
    start_datetime = this_datetime - timedelta(minutes=10)
    history = user.history_ai.filter(
        created_at__range=[start_datetime, this_datetime]
    )
    prompt = ''
    answer = ''

    if history:
        prompt = add_history(history, len(message_text))
    prompt += f'- {message_text}'

    try:
        answer = request_to_openai(prompt)

        HistoryAI.objects.create(
            user=user,
            question=message_text,
            answer=answer.lstrip('\n')
        )
    except Exception as error:
        context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f'Ошибка в ChatGPT: {str(error)}'
        )
    finally:
        answer_text = answer if answer else ERROR_TEXT
        context.bot.send_message(
            chat_id=chat.id,
            reply_to_message_id=update.message.message_id,
            text=answer_text
        )
    return 'Done'

import asyncio
import os
from datetime import datetime, timedelta, timezone

import openai
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from dotenv import load_dotenv
from telegram import ChatAction, Update
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


def add_history(history):
    """Возвращает форматированную историю."""
    prompt = []
    for item in history.exclude(answer__in=[None, ERROR_TEXT]):
        prompt.append({'role': 'user', 'content': item.question})
        prompt.append({'role': 'assistant', 'content': item.answer})
    return prompt


def get_answer_davinci(update: Update, context: CallbackContext):
    """
    Возвращает ответ от API ИИ ChatGPT.
    Предварительно вызвав функцию проверки регистрации.
    """
    async def send_typing_periodically(chat_id: str,
                                       context: CallbackContext) -> None:
        """"
        TYPING в чат Телеграм откуда пришёл запрос.
        Args:
            (:obj:`str`) текст для запроса
        Return:
            None
        """
        while True:
            try:
                context.bot.send_chat_action(
                    chat_id=chat_id,
                    action=ChatAction.TYPING
                )
                await asyncio.sleep(6)
            except asyncio.CancelledError:
                break

    async def request_to_openai(prompt: str) -> str:
        """
        Делает запрос в OpenAI.

        Args:
            (:obj:`str`) текст для запроса

        Return:
            (:obj:`str`) ответ ИИ
        """
        # answer = openai.ChatCompletion.create(
        #     model='gpt-3.5-turbo',
        #     messages=prompt
        # )
        # answer_text = answer.choices[0].message.get('content')
        # для теста
        await asyncio.sleep(10)
        answer_text = '\n'.join([w.get('content') for w in prompt])
        return answer_text

    async def get_answer(prompt: list, chat_id: int, context: CallbackContext):
        """
        Асинхронно запускает 2 функции и при выполнении запроса в openai

        Args:
            (:obj:`str`) текст для запроса
            (:obj:`int`) ID чата откуда пришёл вызов
            (:obj:`CallbackContext`) CallbackContext
        Return
            (:obj:`str`): answer
        """
        task = asyncio.create_task(send_typing_periodically(chat_id, context))
        answer = await request_to_openai(prompt)
        task.cancel()
        return answer

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

    chat_id = update.effective_chat.id
    user = get_object_or_404(
        User,
        username=update.effective_user.id
    )
    message_text = update.effective_message.text.replace('#', '', 1)

    this_datetime = datetime.now(timezone.utc)
    start_datetime = this_datetime - timedelta(minutes=5)
    history = user.history_ai.filter(
        created_at__range=[start_datetime, this_datetime]
    )
    answer_text = ''
    prompt = add_history(history) if history else []
    prompt.append({'role': 'user', 'content': message_text})

    try:
        answer = asyncio.run(get_answer(prompt, chat_id, context))

        if isinstance(answer, str):
            answer_text = answer if answer else ERROR_TEXT
            HistoryAI.objects.create(
                user=user,
                question=message_text,
                answer=answer.lstrip('\n')
            )
        else:
            answer_text = ERROR_TEXT

    except Exception as err:
        context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f'Ошибка в ChatGPT: {err}'
        )
    finally:
        context.bot.send_message(
            chat_id=chat_id,
            reply_to_message_id=update.message.message_id,
            text=answer_text
        )
    return 'Done'

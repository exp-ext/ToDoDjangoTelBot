import asyncio

from telegram import Update
from telegram.ext import CallbackContext

from ..checking import check_registration
from .chat_gpt import GetAnswerGPT


def for_check(update: Update, context: CallbackContext):
    answers_for_check = {
        '?': (f'Я мог бы ответить Вам, если [зарегистрируетесь]({context.bot.link}) 🧐'),
        '!': (f'Я обязательно поддержу Вашу дискуссию, если [зарегистрируетесь]({context.bot.link}) 🙃'),
        '': (f'Какая интересная беседа, [зарегистрируетесь]({context.bot.link}) и я подключусь к ней 😇'),
    }
    allow_unregistered = True
    return check_registration(update, context, answers_for_check, allow_unregistered, return_user=True)


def get_answer_davinci_public(update: Update, context: CallbackContext):
    user = for_check(update, context)
    if user:
        get_answer = GetAnswerGPT(update, context, user)
        asyncio.run(get_answer.get_answer_chat_gpt())


def get_answer_davinci_person(update: Update, context: CallbackContext):
    user = for_check(update, context)
    if update.effective_chat.type == 'private' and user:
        get_answer = GetAnswerGPT(update, context, user)
        asyncio.run(get_answer.get_answer_chat_gpt())

import asyncio
import json
from functools import partial

import httpx
from django.conf import settings
from telbot.notes.add_notes import NoteManager
from telegram import Update
from telegram.ext import CallbackContext

from ..checking import check_registration
from .chat_gpt import GetAnswerGPT


async def async_check_registration(update, context):
    answers_for_check = {}
    allow_unregistered = True
    return_user = True
    loop = asyncio.get_running_loop()
    select_related = ['approved_models']
    prefetch_related = ['tasks', 'locations', 'groups_connections__group', 'history_ai']
    return await loop.run_in_executor(
        None,
        partial(check_registration, update, context, answers_for_check, allow_unregistered, return_user, select_related, prefetch_related)
    )


async def check_request_in_distributor(update, context):
    url = 'http://127.0.0.1:8100/tasks/check/' if settings.DEBUG else 'http://predict:8100/tasks/check/'
    text = update.effective_message.text
    data = {'text': text}

    async with httpx.AsyncClient() as client:
        user_task = asyncio.create_task(async_check_registration(update, context))
        post_task = asyncio.create_task(client.post(url, json=data))
        user, response = await asyncio.gather(user_task, post_task)

    completion = json.loads(response.content)

    if completion['predicted_class'] == 'task':
        note_manager = NoteManager(update, context, user)
        await note_manager.add_notes()
    else:
        get_answer = GetAnswerGPT(update, context, user)
        await get_answer.get_answer_chat_gpt()


def get_answer_chat_gpt_public(update: Update, context: CallbackContext):
    asyncio.run(check_request_in_distributor(update, context))


def get_answer_chat_gpt_person(update: Update, context: CallbackContext):
    asyncio.run(check_request_in_distributor(update, context))

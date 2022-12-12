from datetime import datetime

from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from telegram import Update
from telegram.ext import CallbackContext, ConversationHandler

from ..cleaner import remove_keyboard
from ..service_message import send_service_message
from .parse_message import TaskParse

User = get_user_model()


def first_step_dell(update: Update, context: CallbackContext):
    chat = update.effective_chat
    req_text = (
            f'*{update.effective_user.first_name}*, '
            'введите дату и часть текста заметки,\n'
            'или del для отмены операции'
        )
    message_id = context.bot.send_message(
        chat.id,
        req_text,
        parse_mode='Markdown'
    ).message_id
    context.user_data['del_message'] = message_id
    remove_keyboard(update, context)
    return 'del_note'


def del_notes(update: Update, context: CallbackContext):
    """Удаление записи в модели Task."""
    chat = update.effective_chat

    user_id = update.message.from_user.id
    user = get_object_or_404(
        User,
        username=user_id
    )
    user_locally = user.locations.first()

    pars = TaskParse(update.message.text, user_locally.timezone)
    pars.parse_with_parameters()

    del_id = (context.user_data['del_message'], update.message.message_id)
    for id in del_id:
        context.bot.delete_message(chat.id, id)

    if pars.server_date:
        date_search = pars.user_date.date()
        tasks = user.tasks.filter(
            user_date=date_search,
            text__contains=pars.only_message[1:]
        )
        count = len(tasks)

        if count > 0:
            tasks.delete()
            reply_text = (
                f'Напоминани{"е" if count == 1 else "я"} с текстом '
                f'*<{pars.only_message}>*\n'
                'на дату: '
                f'*{datetime.strftime(pars.user_date, "%d.%m.%Y")}*\n'
                f'Удален{"о" if count == 1 else "ы"} безвозвратно'
                f'{"." if count==1 else "в количестве "+str(count)+"шт."}'
            )
        else:
            reply_text = (
                f'Не удалось найти напоминание *<{pars.only_message}>*\n'
                'на дату: '
                f'*{datetime.strftime(pars.user_date, "%d.%m.%Y")}*\n'
                'Попробуйте снова.'
            )
    else:
        reply_text = (
            f'*{update.message.from_user.first_name}*, '
            'не удалось разобрать что это за дата 🧐. Попробуйте снова 🙄.'
        )

    send_service_message(chat.id, reply_text, 'Markdown')
    return ConversationHandler.END

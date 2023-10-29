from datetime import datetime, timedelta

from core.views import similarity
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from tasks.models import Task
from telegram import Update
from telegram.ext import CallbackContext, ConversationHandler
from users.models import Group

from ..cleaner import remove_keyboard
from ..service_message import send_service_message
from .parse_message import TaskParse

User = get_user_model()


def first_step_add(update: Update, context: CallbackContext):
    chat = update.effective_chat
    message_thread_id = update.effective_message.message_thread_id
    req_text = (
        f'*{update.effective_user.first_name}*, '
        'введите текст заметки с датой и временем 🖌'
    )
    message_id = context.bot.send_message(
        chat.id,
        req_text,
        parse_mode='Markdown',
        message_thread_id=message_thread_id
    ).message_id
    context.user_data['del_message'] = message_id
    remove_keyboard(update, context)
    return 'add_note'


def add_notes(update: Update, context: CallbackContext):
    """Добавление записи в модель Task."""
    chat = update.effective_chat
    message_thread_id = update.effective_message.message_thread_id
    user = get_object_or_404(
        User,
        username=update.message.from_user.username
    )
    user_locally = user.locations.first()

    try:
        pars = TaskParse(update.message.text, user_locally.timezone)
        pars.parse_message()

        if chat.type == 'private':
            group = None
        else:
            group = get_object_or_404(
                Group,
                chat_id=chat.id
            )
        message = pars.only_message

        del_id = (context.user_data['del_message'], update.message.message_id)
        for id in del_id:
            context.bot.delete_message(chat.id, id)

        if pars.server_date:
            start_datetime = pars.server_date - timedelta(minutes=60)
            end_datetime = pars.server_date + timedelta(minutes=60)
            if group:
                tasks = group.tasks.filter(
                    server_datetime__range=[start_datetime, end_datetime],
                    group=group)
            else:
                tasks = user.tasks.filter(
                    server_datetime__range=[start_datetime, end_datetime]
                )
            for task in tasks:
                simile = similarity(task.text, message)
                if simile > 0.62:
                    reply_text = (
                        'Очень похожее напоминание присутствует в задачах.\n'
                        'Запись отклонена.'
                    )
                    send_service_message(chat.id, reply_text, message_thread_id)
                    return ConversationHandler.END

            birthday = pars.birthday
            repeat = 'Y' if birthday else pars.period_repeat

            if pars.user_date.hour == 0 and pars.user_date.minute == 0:
                text = ''
                remind_at = pars.user_date + timedelta(hours=8)
            else:
                text = (
                    'на время: '
                    f'*{datetime.strftime(pars.user_date, "%H:%M")}*\n'
                )
                remind_at = None

            Task.objects.create(
                user=user,
                group=group,
                server_datetime=pars.server_date,
                text=message,
                remind_at=remind_at,
                reminder_period=repeat,
                it_birthday=birthday
            )

            reply_text = (
                f'Напоминание: *{pars.only_message}*\n'
                'Создано на дату: '
                f'*{datetime.strftime(pars.user_date, "%d.%m.%Y")}*\n'
                f'{text}'
            )
        else:
            reply_text = (
                f'*{update.message.from_user.first_name}*, '
                'не удалось разобрать что это за дата 🧐. Попробуйте снова 🙄.'
            )

        send_service_message(chat.id, reply_text, 'Markdown', message_thread_id)
    except Exception as error:
        raise KeyError(error)
    finally:
        return ConversationHandler.END

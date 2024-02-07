from datetime import datetime

from django.contrib.auth import get_user_model
from django.db.models import DateTimeField
from django.db.models.functions import Trunc
from django.shortcuts import get_object_or_404
from telegram import Update
from telegram.ext import CallbackContext, ConversationHandler

from ..cleaner import remove_keyboard
from ..service_message import send_service_message
from .parse_message import TaskParse

User = get_user_model()


def first_step_dell(update: Update, context: CallbackContext):
    chat = update.effective_chat
    message_thread_id = update.effective_message.message_thread_id
    req_text = (
        f'*{update.effective_user.first_name}*, '
        'введите дату и часть текста заметки которую планируете удалить 🖍'
    )
    message_id = context.bot.send_message(
        chat.id,
        req_text,
        parse_mode='Markdown',
        message_thread_id=message_thread_id
    ).message_id
    context.user_data['del_message'] = message_id
    remove_keyboard(update, context)
    return 'del_note'


def del_notes(update: Update, context: CallbackContext):
    """Удаление записи в модели Task."""
    chat = update.effective_chat
    message_thread_id = update.effective_message.message_thread_id
    tg_username = update.message.from_user.username
    text = " ".join(update.message.text.split()).replace('- ', '')

    user = get_object_or_404(User.objects.prefetch_related('locations'), username=tg_username)
    user_locally = user.locations.first() if user.locations.exists() else 'UTC'

    try:
        pars = TaskParse(text, user_locally.timezone)
        pars.parse_message()

        del_id = (context.user_data.get('del_message'), update.message.message_id)
        for id in filter(None, del_id):
            context.bot.delete_message(chat.id, id)

        reply_text = f'*{update.message.from_user.first_name}*, не удалось разобрать дату 🧐. Попробуйте снова 🙄.'

        if pars.server_date:
            tasks = user.tasks.filter(text__icontains=pars.only_message)

            if pars.user_date.hour == 0 and pars.user_date.minute == 0:
                start_of_day = datetime.combine(pars.user_date, datetime.min.time())
                end_of_day = datetime.combine(pars.user_date, datetime.max.time())
                tasks = tasks.filter(server_datetime__range=(start_of_day, end_of_day))
            else:
                tasks = tasks.annotate(
                    server_datetime_hour=Trunc('server_datetime', 'hour', output_field=DateTimeField())
                ).filter(server_datetime_hour=pars.server_date.replace(minute=0, second=0, microsecond=0))

            count = tasks.count()
            if count > 0:
                tasks.delete()
                single = count == 1
                reply_text = (
                    f'Напоминани{"е" if single else "я"} с текстом *<{pars.only_message}>* на дату *{pars.user_date.strftime("%d.%m.%Y")}*, '
                    f'удален{"о" if single else "ы"} безвозвратно{"." if single else f" в количестве {count}шт."}'
                )
            else:
                reply_text = f'Не удалось найти напоминание *<{pars.only_message}>* на дату: *{pars.user_date.strftime("%d.%m.%Y")}*. Попробуйте снова.'

        send_service_message(chat.id, reply_text, 'Markdown', message_thread_id)
    except Exception as error:
        raise KeyError(error)
    finally:
        return ConversationHandler.END

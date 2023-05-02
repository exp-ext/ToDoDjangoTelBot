from django.conf import settings
from django.contrib.auth import get_user_model
from telegram import ParseMode, Update
from telegram.ext import CallbackContext

from .cleaner import delete_messages_by_time
from .menus import assign_group

User = get_user_model()


def check_registration(update: Update,
                       context: CallbackContext,
                       answers: dict) -> bool:
    """Проверка регистрации пользователя перед ответом."""
    chat = update.effective_chat
    user_tel = update.effective_user
    user = User.objects.filter(username=user_tel.id)
    text = None
    message_text = update.effective_message.text or ''
    if not user:
        for key, _ in answers.items():
            if key in message_text:
                text = answers[key]
                break
    elif not user[0].first_name:
        text = (
            'Я мог бы ответить, но не знаю как к Вам обращаться?\n'
            'Есть 2 варианта решения.\n'
            '1 - добавить имя в личном кабинете '
            f'[WEB версии](https://www.{settings.DOMAIN}/\n'
            '2 - в настройках Телеграмма и заново пройти регистрацию'
        )
    if text:
        message_id = context.bot.send_message(
            chat_id=chat.id,
            reply_to_message_id=update.message.message_id,
            text=text,
            parse_mode=ParseMode.MARKDOWN
        ).message_id
        delete_messages_by_time.apply_async(
            args=[chat.id, message_id],
            countdown=20
        )
        return False
    assign_group(update)
    return True

import redis
from django.conf import settings
from django.contrib.auth import get_user_model
from telegram import ParseMode, Update
from telegram.ext import CallbackContext
from users.models import Group, GroupConnections

from .cleaner import delete_messages_by_time

User = get_user_model()
redis_client = redis.StrictRedis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=0)


def get_or_create_user(tg_user):
    """Возвращает User. Метод нужен для перехода на новую модель."""
    user = User.objects.filter(username=tg_user.username).first()
    if not user:
        user = User.objects.filter(username=tg_user.id).first()
        if user:
            user.tg_id = tg_user.id
            user.username = tg_user.username
            user.save()
    return user


def check_registration(update: Update, context: CallbackContext, answers: dict) -> bool:
    """Проверка регистрации пользователя и назначение группы."""
    chat = update.effective_chat
    tg_user = update.effective_user
    user = get_or_create_user(tg_user)
    text = None

    message_text = update.effective_message.text or ''
    if not user:
        text = next((answers[key] for key in answers if key in message_text), None)
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

    if chat.type != 'private':
        group, created = Group.objects.get_or_create(
            chat_id=chat.id
        )
        if created or group.title != chat.title:
            group.title = chat.title
            group.save()

        if not user.favorite_group:
            user.favorite_group = group
            user.save()

        GroupConnections.objects.get_or_create(
            user=user,
            group=group
        )
    return True

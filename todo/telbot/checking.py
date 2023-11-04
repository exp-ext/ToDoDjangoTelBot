import json

from django.conf import settings
from django.contrib.auth import get_user_model
from telegram import ParseMode, Update
from telegram.ext import CallbackContext
from users.models import Group, GroupConnections

from .cleaner import delete_messages_by_time

User = get_user_model()
redis_client = settings.REDIS_CLIENT


def set_user_in_redis(tg_user: Update.effective_user, user: User):
    """Обновляет запись в Redis db."""
    red_user = {
        'user_id': user.id,
        'tg_user_id': tg_user.id,
        'tg_user_username': tg_user.username,
        'favorite_group': user.favorite_group.id if user.favorite_group else None,
        'groups_connections': list(user.groups_connections.values_list('group__id', flat=True)),
    }
    redis_client.set(f"user:{tg_user.id}", json.dumps(red_user))
    return red_user


def get_or_create_user(tg_user):
    """Возвращает User."""
    redis_key = f"user:{tg_user.id}"
    red_user = redis_client.get(redis_key)
    if red_user:
        return json.loads(red_user.decode('utf-8'))

    user = User.objects.filter(tg_id=tg_user.id).select_related('favorite_group').first()
    if user:
        red_user = set_user_in_redis(tg_user, user)
    return red_user


def check_registration(update: Update, context: CallbackContext, answers: dict) -> bool:
    """Проверка регистрации пользователя и назначение группы."""
    chat = update.effective_chat
    tg_user = update.effective_user
    red_user = get_or_create_user(tg_user)
    text = None

    message_text = update.effective_message.text or ''
    if not red_user:
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
        group, _ = Group.objects.get_or_create(chat_id=chat.id)

        update_group = False
        update_user = False

        if group.link != chat.link:
            group.link = chat.link
            update_group = True

        if group.title != chat.title:
            group.title = chat.title
            update_group = True

        if not red_user.get('favorite_group') or group.id not in red_user.get('groups_connections'):
            user = User.objects.filter(tg_id=tg_user.id).first()

        if not red_user.get('favorite_group'):
            user.favorite_group = group
            update_user = True

        if group.id not in red_user.get('groups_connections'):
            GroupConnections.objects.get_or_create(user=user, group=group)
            update_user = True

        if update_group:
            group.save()

        if update_user:
            user.save()
            set_user_in_redis(tg_user, user)

    return True

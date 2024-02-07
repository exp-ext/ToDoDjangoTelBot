import json
from typing import Optional, Tuple

from django.conf import settings
from django.contrib.auth import get_user_model
from telegram import ParseMode, Update
from telegram.ext import CallbackContext
from users.models import Group, GroupConnections

from .cleaner import delete_messages_by_time

User = get_user_model()
redis_client = settings.REDIS_CLIENT


class UserRedisManager:

    def set_user_in_redis(self, tg_user, user: User) -> dict:
        """Обновляет запись в Redis db."""
        red_user = {
            'user_id': user.id,
            'tg_user_id': tg_user.id,
            'tg_user_username': tg_user.username,
            'favorite_group': user.favorite_group.id if user.favorite_group else None,
            'groups_connections': list(user.groups_connections.values_list('group__id', flat=True)),
            'is_blocked_bot': user.is_blocked_bot,
        }
        redis_client.set(f"user:{tg_user.id}", json.dumps(red_user))
        return red_user

    def get_or_create_user(self, tg_user, return_user) -> Tuple[dict, Optional[User]]:
        """Возвращает User."""
        redis_key = f"user:{tg_user.id}"
        red_user = redis_client.get(redis_key)
        red_user = json.loads(red_user.decode('utf-8')) if red_user else None

        if red_user and not red_user.get('is_blocked_bot') and not return_user:
            return red_user, None

        user, created = User.objects.get_or_create(tg_id=tg_user.id)
        if created:
            self._update_new_user(user, tg_user)

        red_user = self.set_user_in_redis(tg_user, user)
        return red_user, user

    def _update_new_user(self, user, tg_user):
        """Обновляет нового пользователя."""
        user.username = tg_user.username or f'n-{str(1010101 + user.id)[::-1]}'
        user.first_name = tg_user.first_name or tg_user.username
        user.last_name = tg_user.last_name
        user.save()


def check_registration(update: Update,
                       context: CallbackContext,
                       answers: dict,
                       allow_unregistered: bool = False,
                       return_user: bool = False) -> bool or User:
    """Проверяет регистрацию пользователя. Регистрирует пользователя если он не был зарегистрирован, но с ограничениями.
    Если чат не является приватным, функция также обновляет информацию о связанных группах.

    ## Args:
    - update ('Update'): Объект Update от Telegram Bot API, содержащий информацию о сообщении.
    - context ('CallbackContext'): Контекст выполнения, предоставляемый Python-telegram-bot.
    - answers ('dict'): Словарь с возможными ответами для пользователя.
    - allow_unregistered ('bool', optional): Флаг, указывающий, разрешено ли не зарегистрированным пользователям использовать вызвавшую функцию. По умолчанию False.
    - return_user ('bool', optional): Флаг, указывающий, следует ли возвращать объект пользователя. По умолчанию False, и возвращает None.

    ## Returns:
    - 'bool': Если регистрация проверена успешно возвращает или user('User') если return_user=True или None, иначе False.

    ## Raises:
    - Возможные исключения, которые могут быть вызваны внутренними методами.
    """
    chat = update.effective_chat
    tg_user = update.effective_user
    user_manager = UserRedisManager()
    red_user, user = user_manager.get_or_create_user(tg_user, return_user)
    text = None
    message_text = update.effective_message.text or ''
    if red_user.get('is_blocked_bot') and allow_unregistered is False:
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

        if (not red_user.get('favorite_group') or group.id not in red_user.get('groups_connections')) and not user:
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
            user_manager.set_user_in_redis(tg_user, user)

    return user

import secrets
import string
from typing import Any, Dict

from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.db.models.query import QuerySet
from django.http import HttpRequest, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from telbot.cleaner import process_to_delete_message
from telbot.commands import set_up_commands
from telegram import Update
from telegram.ext import CallbackContext
from timezonefinder import TimezoneFinder

from .models import Location

User = get_user_model()


class Signup:
    """Регистрация юзера."""

    def register(self,
                 update: Update,
                 context: CallbackContext) -> Dict[str, Any]:
        """Регистрация или обновление пользователя."""
        chat = update.effective_chat
        tel_user = update.effective_user

        if chat.type != 'private':
            message_id = context.bot.send_message(
                chat.id,
                f'{tel_user.first_name}, '
                'эта функция доступна только в "private"'
            ).message_id
            *params, = tel_user.id, message_id, 20
            process_to_delete_message(params)
            return JsonResponse({"error": "Only in the private chat type."})

        password = self.get_password(length=15)

        user, _ = User.objects.get_or_create(username=tel_user.id)
        user.first_name = tel_user.first_name
        user.last_name = tel_user.last_name
        user.set_password(password)
        user.save()

        if not Location.objects.filter(user=user).exists():
            Location.objects.create(
                user=user,
                latitude=59.799,
                longitude=30.274
            )
        reply_text = (
            'Вы успешно зарегистрированы в проекте Your ToDo.\n'
            'Ссылка в личный кабинет для будущих посещений:\n'
            f'{settings.DOMEN}/auth/login/\n'
            'логин:\n'
            f'{tel_user.id}\n'
            'пароль:\n'
            f'{password}\n'
            'А сейчас, можно просто нажать на '
            f'[ВХОД🕋](https://{settings.DOMEN}'    #  /auth/login/{tel_user.id}/{password}/)'
            )
        update.message.reply_text(
                text=reply_text,
                parse_mode='Markdown'
            )
        set_up_commands(context.bot)
        return JsonResponse({"ok": "User created."})

    @staticmethod
    def get_password(length):
        """
        Password Generator:
        length - password length
        """
        character_set = string.digits + string.ascii_letters
        return ''.join(secrets.choice(character_set) for i in range(length))


def login(request: HttpRequest, user_id: int = None,
          password: str = None) -> HttpResponseRedirect:
    """Аутентификация пользователя через Телеграмм."""
    user = authenticate(request, username=user_id, password=password)
    if not user:
        return redirect('users:login')
    login(request, user)
    return redirect('index')


def get_coordinates(username: int) -> QuerySet[Location]:
    """
    Получение последних координат пользователя.

    Принимает username=user_id (:obj:`int`)

    Возвращает :obj:`QuerySet[Location]`:
    - latitude (:obj:`float`)
    - longitude (:obj:`float`)
    - timezone (:obj:`str`)
    """
    user = get_object_or_404(User, username=username)
    return user.locations.first()


def set_coordinates(update: Update, _: CallbackContext) -> None:
    """Получение часового пояса и запись в данных в БД."""
    chat = update.effective_chat
    user_id = chat.id
    latitude = update.message.location.latitude
    longitude = update.message.location.longitude
    user = get_object_or_404(User, username=user_id)

    tf = TimezoneFinder()
    timezone_str = tf.timezone_at(lng=longitude, lat=latitude)

    Location.objects.create(
        user=user,
        latitude=latitude,
        longitude=longitude,
        timezone=timezone_str
    )

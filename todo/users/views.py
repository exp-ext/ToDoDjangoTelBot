from multiprocessing import Process

from core.views import get_password
from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.db.models.query import QuerySet
from django.http import HttpRequest, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from telbot.cleaner import delete_messages_by_time
from telbot.system_commands import set_up_commands
from telegram import Update
from telegram.ext import CallbackContext
from tzwhere import tzwhere

from todo.celery import app

from .models import Location

User = get_user_model()


def register(update: Update, context: CallbackContext) -> None:
    """Регистрация или обновление пользователя."""
    chat = update.effective_chat
    user_id = chat.id
    first_name = update.message.from_user.first_name
    last_name = update.message.from_user.last_name
    if chat.type == 'private':
        domen = settings.DOMEN
        password = get_password(length=10)

        if User.objects.filter(username=user_id).exists():
            user = User.objects.get(username=user_id)
            user.first_name = first_name
            user.last_name = last_name
            user.set_password(password)
            user.save()
        else:
            User.objects.create_user(
                first_name=first_name,
                last_name=last_name,
                username=user_id,
                password=password
            )
        reply_text = (
            'Вы успешно зарегистрированы в проекте Your ToDo.\n'
            'Ссылка в личный кабинет для будущих посещений:\n'
            f'{domen}/auth/login/\n'
            'логин:\n'
            f'{user_id}\n'
            'пароль:\n'
            f'{password}\n'
            'Но сейчас, для входа, можно просто пройти по по адресу:'
            f'{domen}/auth/login/{user_id}/{password}/'
            )
        update.message.reply_text(
                text=reply_text,
            )
        set_up_commands(context.bot)
    else:
        message_id = context.bot.send_message(
            chat.id,
            f'{first_name}, эта функция доступна только в "private"'
        ).message_id
        *params, = user_id, message_id, 20
        p1 = Process(target=delete_messages_by_time, args=(params,))
        p1.start()


def login(request: HttpRequest, user_id: int = None,
          password: str = None) -> HttpResponseRedirect:
    """Аутентификация пользователя через Телеграмм."""
    user = authenticate(request, username=user_id, password=password)
    if not user:
        return redirect('users:login')
    login(request, user)
    return redirect('index')


def get_coordinates(username: int) -> QuerySet[Location]:
    """Получение последних координат пользователя."""
    user = get_object_or_404(User, username=username)
    return user.locations.first()


@app.task(ignore_result=True)
def set_coordinates(update: Update, context: CallbackContext) -> None:
    """Получение часового пояса и запись в данных в БД."""
    chat = update.effective_chat
    user_id = chat.id
    latitude = update.message.location.latitude
    longitude = update.message.location.longitude
    user = get_object_or_404(User, username=user_id)

    user_tz = tzwhere.tzwhere()
    timezone_str = user_tz.tzNameAt(latitude, longitude)

    Location.objects.create(
        user=user,
        latitude=latitude,
        longitude=longitude,
        timezone=timezone_str
    )

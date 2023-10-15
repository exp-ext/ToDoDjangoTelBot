import secrets
import string
import uuid
from datetime import timedelta
from typing import Any, Dict

import requests
from core.serializers import ModelDataSerializer
from django.conf import settings
from django.contrib.auth import authenticate, get_user_model, login
from django.contrib.auth.decorators import login_required
from django.core.files import File
from django.core.files.temp import NamedTemporaryFile
from django.db.models.query import QuerySet
from django.http import (HttpRequest, HttpResponse, HttpResponseRedirect,
                         JsonResponse)
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views import View
from telbot.cleaner import delete_messages_by_time
from telegram import Update
from telegram.ext import CallbackContext
from timezonefinder import TimezoneFinder
from users.validators import HashCheck

from todo.celery import app

from .forms import ProfileForm
from .models import Location

User = get_user_model()


class Authentication:
    valid_time: int = 5

    def __init__(self, update: Update, context: CallbackContext):
        self.update = update
        self.context = context
        self.chat = update.effective_chat
        self.tg_user = update.effective_user

    def register(self, ) -> Dict[str, Any]:
        """Регистрация или обновление пользователя."""
        if self.check_chat_type():
            return JsonResponse({"error": "Chat type not private."})

        validation_key = self.get_password(length=28)
        user, _ = User.objects.update_or_create(
            tg_id=self.tg_user.id,
            username=self.tg_user.username,
            defaults={
                'first_name': self.tg_user.first_name,
                'last_name': self.tg_user.last_name,
                'validation_key': validation_key,
                'validation_key_time': timezone.now().astimezone(timezone.utc),
            }
        )

        if not user.image:
            self.add_profile_picture.apply_async(
                args=(self.tg_user.id, ModelDataSerializer.serialize(user),)
            )

        password = self.get_password(length=15)
        user.set_password(password)
        reply_text = [
            'Вы успешно зарегистрированы в [проекте Your To-Do]'
            f'(https://www.{settings.DOMAIN}/).\n'
            'Ниже логин и пароль для входа в личный кабинет:\n'
            f'⤵️\n',
            f'{self.tg_user.username}\n',
            f'{password}\n',
            f'Для авторизации на [сайте](https://www.{settings.DOMAIN}) пройдите по ссылке'
            f'[https://www.{settings.DOMAIN}/auth/](https://www.{settings.DOMAIN}/auth/login/tg/{self.tg_user.id}/{validation_key}/)'
        ]
        message_id = self.send_messages(reply_text)
        user.validation_message_id = message_id
        user.save()
        if not user.locations.exists():
            Location.objects.create(
                user=user,
                latitude=59.799,
                longitude=30.274
            )
        return JsonResponse({"ok": "User created."})

    def authorization(self) -> Dict[str, Any]:
        """Получение ссылки для авторизации на сайте."""
        if self.check_chat_type():
            return JsonResponse({"error": "Chat type not private."})

        validation_key = self.get_password(length=28)

        user = User.objects.filter(
            tg_id=self.tg_user.id,
            username=self.tg_user.username
        ).first()

        if not user.image:
            self.add_profile_picture.apply_async(
                args=(self.tg_user.id, ModelDataSerializer.serialize(user),)
            )

        user.first_name = self.tg_user.first_name
        user.last_name = self.tg_user.last_name
        user.validation_key = validation_key
        user.validation_key_time = timezone.now().astimezone(timezone.utc)
        reply_text = [
            f'Для авторизации на [сайте](https://www.{settings.DOMAIN}) пройдите по ссылке'
            f'[https://www.{settings.DOMAIN}/auth/](https://www.{settings.DOMAIN}/auth/login/tg/{self.tg_user.id}/{validation_key}/)'
        ]
        message_id = self.send_messages(reply_text)
        user.validation_message_id = message_id
        user.save()
        return JsonResponse({"ok": "Link sent."})

    def send_messages(self, reply_text):
        """Отправка сообщений в чат"""
        for text in reply_text:
            message_id = self.update.message.reply_text(
                text=text,
                parse_mode='Markdown'
            ).message_id
        lifetime = 60 * self.valid_time
        delete_messages_by_time.apply_async(
            args=[self.chat.id, message_id],
            countdown=lifetime
        )
        return message_id

    def check_chat_type(self):
        """Проверка типа чата."""
        if self.chat.type != 'private':
            message_id = self.context.bot.send_message(
                self.chat.id,
                f'{self.tg_user.first_name}, '
                'эта функция доступна только в "private"'
            ).message_id
            delete_messages_by_time.apply_async(
                args=[self.chat.id, message_id],
                countdown=20
            )
            return True
        return False

    @staticmethod
    def get_password(length):
        """
        Password Generator:
        length - password length
        """
        character_set = string.digits + string.ascii_letters
        return ''.join(secrets.choice(character_set) for _ in range(length))

    @staticmethod
    @app.task(ignore_result=True)
    def add_profile_picture(tg_user_id, user):
        """Добавляет фотографию профиля юзера."""
        user = ModelDataSerializer.deserialize(user)
        url = f'https://api.telegram.org/bot{settings.TELEGRAM_TOKEN}/getUserProfilePhotos'
        params = {'user_id': tg_user_id}
        response = requests.get(url, params=params)
        data = response.json()

        if response.status_code == 200:
            file_id = data['result']['photos'][0][0]['file_id']
            url = f'https://api.telegram.org/bot{settings.TELEGRAM_TOKEN}/getFile'
            params = {
                'file_id': file_id
            }
            response = requests.get(url, params=params)
            data = response.json()
            if response.status_code == 200:
                file_path = data['result']['file_path']
                file_url = f'https://api.telegram.org/file/bot{settings.TELEGRAM_TOKEN}/{file_path}'
                response = requests.get(file_url)
                if response.status_code == 200:
                    temp_file = NamedTemporaryFile(delete=True)
                    temp_file.write(response.content)
                    temp_file.flush()
                    user.image.save(f'{uuid.uuid4}.jpg', File(temp_file))
                    temp_file.close()


class LoginTgView(View):

    def post(self,
             request: HttpRequest,
             *args: Any, **kwargs: Any
             ) -> HttpRequest:

        data = request.GET
        if not HashCheck(data).check_hash():
            return render(request, 'users/error.html', {
                'msg': 'Bad hash!'
            })

        photo_url = data.pop('photo_url')
        response = requests.GET.get(photo_url)

        if response.status_code == 200:
            temp_file = NamedTemporaryFile(delete=True)
            temp_file.write(response.content)
            temp_file.flush()

        user, status = User.objects.get_or_create(**data)
        if status:
            user.set_password(Authentication.get_password())
        user.image.save(f'{uuid.uuid4}.jpg', File(temp_file))
        user.save()
        temp_file.close()
        login(request, user)
        return redirect('index')


class LoginTgLinkView(View):
    valid_time: int = 10

    def get(self, request: HttpRequest, user_id: str, key: str, *args: Any, **kwargs: Any) -> HttpRequest:
        """Авторизует пользователя по ссылке из Телеграм."""
        user_id = int(user_id)
        key = str(key)
        user = User.objects.filter(tg_id=user_id).first()

        time_difference = timezone.now().astimezone(timezone.utc) - user.validation_key_time
        if user.validation_key == key and time_difference < timedelta(minutes=self.valid_time):
            login(request, user)
            user.validation_key = None
            user.save()
            delete_messages_by_time.apply_async(
                args=[user_id, user.validation_message_id],
                countdown=5
            )
        return redirect('index')


@login_required
def accounts_profile(request: HttpRequest, username: str) -> HttpResponse:
    """Профиль юзера."""
    user = get_object_or_404(User.objects, username=username)
    if user != request.user:
        redirect('index')

    form = ProfileForm(
        request.POST or None,
        files=request.FILES or None,
        instance=user
    )

    if request.method == "POST" and form.is_valid():
        user = form.save()
        return redirect('accounts_profile', username=username)

    context = {
        'user': user,
        'form': form,
    }
    template = 'users/accounts_profile.html'
    return render(request, template, context)


def login_token(request: HttpRequest, user_id: int = None,
                password: str = None) -> HttpResponseRedirect:
    """Аутентификация пользователя через Телеграмм."""
    user = authenticate(request, username=user_id, password=password)
    if not user:
        return redirect('users:login')
    login(request, user)
    return redirect('index')


def get_coordinates(tg_id: int) -> QuerySet[Location]:
    """
    Получение последних координат пользователя.

    Принимает username=user_id (:obj:`int`)

    Возвращает :obj:`QuerySet[Location]`:
    - latitude (:obj:`float`)
    - longitude (:obj:`float`)
    - timezone (:obj:`str`)
    """
    user = User.objects.filter(tg_id=tg_id).first()
    return user.locations.first() if user else None


def set_coordinates(update: Update, _: CallbackContext) -> None:
    """Получение часового пояса и запись в данных в БД."""
    chat = update.effective_chat
    user_id = chat.id
    latitude = update.message.location.latitude
    longitude = update.message.location.longitude
    user = User.objects.filter(tg_id=user_id).first()

    if user:
        tf = TimezoneFinder()
        timezone_str = tf.timezone_at(lng=longitude, lat=latitude)
        Location.objects.create(
            user=user,
            latitude=latitude,
            longitude=longitude,
            timezone=timezone_str
        )


def block(request: HttpRequest) -> HttpResponse:
    """Блокировка при серии ввода неправильных данных при авторизации."""
    text = (
        f'Вы заблокированы на {int(settings.DEFENDER_COOLOFF_TIME/60)} минут!'
    )
    context = {
        'text': text,
    }
    template = 'users/block.html'
    return render(request, template, context)

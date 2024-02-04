import secrets
import string
import uuid
from datetime import timedelta
from typing import Any, Dict, OrderedDict

import requests
from core.serializers import ModelDataSerializer
from django.conf import settings
from django.contrib.auth import get_user_model, login
from django.contrib.auth.decorators import login_required
from django.core.files import File
from django.core.files.temp import NamedTemporaryFile
from django.db.models.query import QuerySet
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views import View
from telbot.checking import UserRedisManager
from telbot.cleaner import delete_messages_by_time
from telegram import Update
from telegram.ext import CallbackContext
from timezonefinder import TimezoneFinder
from users.validators import HashCheck

from todo.celery import app

from .forms import ProfileForm
from .models import Location

User = get_user_model()
ADMIN_ID = settings.TELEGRAM_ADMIN_ID


class Authentication:
    """Класс для аутентификации пользователей и регистрации новых пользователей в системе.

    ### Attributes:
    - valid_time (`int`): Время в минутах, в течение которого действует ссылка для аутентификации.

    ### Methods:
    - __init__(self, update: Update, context: CallbackContext): Инициализация объекта класса.
    - register(self) -> Dict[str, Any]: Регистрация нового пользователя.
    - authorization(self) -> Dict[str, Any]: Аутентификация пользователя.
    - send_messages(self, reply_text): Отправка сообщений пользователю.
    - check_chat_type(self): Проверка типа чата пользователя.

    """
    valid_time: int = 5

    def __init__(self, update: Update, context: CallbackContext, user: User = None):
        """Инициализация объекта класса.

        ### Args:
            update (`Update`): Объект, представляющий Telegram Update.
            context (`CallbackContext`): Объект, представляющий контекст Callback Query.

        """
        self.update = update
        self.context = context
        self.chat = update.effective_chat
        self.tg_user = update.effective_user
        self.user = user

    def register(self) -> Dict[str, Any]:
        """Регистрация нового пользователя в системе.

        ### Returns:
        - Dict[str, Any]: Результат регистрации пользователя.

        """
        if self.check_chat_type():
            return JsonResponse({"error": "Chat type not private."})

        try:
            validation_key = self.get_password(length=28)
            self.user, _ = User.objects.get_or_create(tg_id=self.tg_user.id)
            self.user.username = self.tg_user.username or f'n-{str(1010101 + self.user.id)[::-1]}'
            self.user.first_name = self.tg_user.first_name or self.tg_user.username
            self.user.last_name = self.tg_user.last_name
            self.user.is_blocked_bot = False
            self.user.validation_key = validation_key
            self.user.validation_key_time = timezone.now().astimezone(timezone.utc)

            user_manager = UserRedisManager()
            user_manager.set_user_in_redis(self.tg_user, self.user)

            if not self.user.image:
                self.add_profile_picture.apply_async(args=(self.tg_user.id, ModelDataSerializer.serialize(self.user),))
            password = self.get_password(length=15)
            self.user.set_password(password)
            reply_text = [
                'Вы успешно зарегистрированы в проекте Your To-Do.\n'
                'Ниже логин и пароль для входа в личный кабинет:\n'
                '⤵️\n',
                f'{self.tg_user.username}\n',
                f'{password}\n',
                f'Для быстрой авторизации на [сайте](https://www.{settings.DOMAIN}) пройдите по ссылке:\n〰\n'
                f'✔️ [https://www.{settings.DOMAIN}/auth/](https://www.{settings.DOMAIN}/auth/login/tg/{self.tg_user.id}/{validation_key}/)\n〰'
            ]
            message_id = self.send_messages(reply_text)
            self.user.validation_message_id = message_id
            self.user.save()
        except Exception as err:
            user_error_message = 'Произошла непредвиденная ошибка. Разработчики уже занимаются её устранением 💡. Попробуйте позже.'
            self.context.bot.send_message(self.tg_user.id, user_error_message)
            error_message = f'Ошибка при регистрации пользователя c id-{self.tg_user.id} и username-{self.tg_user.username}:\n{err}'
            self.context.bot.send_message(ADMIN_ID, error_message)

        if not self.user.locations.exists():
            Location.objects.create(
                user=self.user,
                latitude=59.799,
                longitude=30.274
            )
        return JsonResponse({"ok": "User created."})

    def authorization(self) -> Dict[str, Any]:
        """Аутентификация пользователя.

        ### Returns:
        - Dict[str, Any]: Результат аутентификации пользователя.

        """
        if self.check_chat_type():
            return JsonResponse({"error": "Chat type not private."})

        validation_key = self.get_password(length=28)

        # if not self.user:
        #     self.user = User.objects.filter(
        #         tg_id=self.tg_user.id,
        #         username=self.tg_user.username
        #     ).first()

        if not self.user.image:
            self.add_profile_picture.apply_async(args=(self.tg_user.id, ModelDataSerializer.serialize(self.user),))

        self.user.first_name = self.tg_user.first_name
        self.user.last_name = self.tg_user.last_name

        if User.objects.filter(phone_number=self.update.message.contact.phone_number).exclude(id=self.user.id).exists():
            reply_text = (
                'Пользователь с таким номером телефона, уже существует.'
                'Напишите пожалуйста об этом инциденте разработчику - https://t.me/Borokin'
            )
            self.context.bot.send_message(self.chat.id, reply_text)
        else:
            self.user.phone_number = self.update.message.contact.phone_number

        self.user.validation_key = validation_key
        self.user.validation_key_time = timezone.now().astimezone(timezone.utc)
        reply_text = [
            f'Для быстрой авторизации на [сайте](https://www.{settings.DOMAIN}) пройдите по ссылке:\n〰\n'
            f'✔️ [https://www.{settings.DOMAIN}/auth/](https://www.{settings.DOMAIN}/auth/login/tg/{self.tg_user.id}/{validation_key}/)\n〰'
        ]
        message_id = self.send_messages(reply_text)
        self.user.validation_message_id = message_id
        try:
            self.user.save()
        except Exception as err:
            delete_messages_by_time.apply_async(
                args=[self.chat.id, message_id],
                countdown=0
            )
            reply_text = 'Произошла непредвиденная ошибка. Разработчики уже занимаются её устранением 💡.'
            self.context.bot.send_message(self.chat.id, reply_text)
            error_message = f'Ошибка при авторизации пользователя c id-{self.tg_user.id} и username-{self.tg_user.username}:\n{err}'
            self.context.bot.send_message(ADMIN_ID, error_message)

        return JsonResponse({"ok": "Link sent."})

    def send_messages(self, reply_text) -> None:
        """Отправка сообщений пользователю.

        ### Args:
        - reply_text (`List`): Список текстовых сообщений для отправки.

        ### Returns:
        - int: Идентификатор последнего отправленного сообщения.

        """
        for text in reply_text:
            try:
                message_id = self.update.message.reply_text(text=text, parse_mode='Markdown').message_id
            except Exception:
                message_id = self.update.message.reply_text(text=text).message_id

        lifetime = 60 * self.valid_time
        delete_messages_by_time.apply_async(
            args=[self.chat.id, message_id],
            countdown=lifetime
        )
        return message_id

    def check_chat_type(self):
        """Проверка типа чата пользователя.

        ### Returns:
            bool: True, если тип чата не является "private", иначе False.

        """
        if self.chat.type != 'private':
            message_id = self.context.bot.send_message(
                self.chat.id,
                f'{self.tg_user.first_name}, '
                'эта функция доступна только в "private"'
            ).message_id
            delete_messages_by_time.apply_async(args=[self.chat.id, message_id], countdown=20)
            return True
        return False

    @staticmethod
    def get_password(length):
        """
        Генератор паролей.

        ### Args:
        - length (`int`): Длина пароля.

        ### Returns:
        - `str`: Сгенерированный пароль.

        """
        character_set = string.digits + string.ascii_letters
        return ''.join(secrets.choice(character_set) for _ in range(length))

    @staticmethod
    @app.task(ignore_result=True)
    def add_profile_picture(tg_user_id: int, user: OrderedDict):
        """Добавляет фотографию профиля юзера.

        ### Args:
        - tg_user_id (`int`): Идентификатор пользователя в Telegram.
        - user (`OrderedDict`): Сериализованный объект пользователя.

        """
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
    """Класс для обработки аутентификации пользователя через Telegram виджет.

    ### Methods:
        post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpRequest: Обработка POST-запроса для аутентификации.

    """

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpRequest:
        """Обработка POST-запроса для аутентификации.

        ### Args:
        - request (`HttpRequest`): HTTP-запрос.
        - *args: Переменные позиционных аргументов.
        - **kwargs: Переменные ключевых аргументов.

        ### Returns:
        - HttpRequest: HTTP-ответ.

        """
        data = request.GET
        if not HashCheck(data).check_hash():
            return render(request, 'users/error.html', {'msg': 'Bad hash!'})

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
    """Класс для авторизации пользователя по ссылке из Телеграм.

    ### Attributes:
    - valid_time (`int`): Время действия ссылки в минутах.

    ### Methods:
    - get: Авторизует пользователя по ссылке из Телеграм.

    """
    valid_time: int = 10

    def get(self, request: HttpRequest, user_id: str, key: str, *args: Any, **kwargs: Any) -> HttpRequest:
        """Авторизует пользователя по ссылке из Телеграм.

        ### Args:
        - request (HttpRequest): HTTP-запрос.
        - user_id (str): Идентификатор пользователя в Телеграм.
        - key (str): Ключ для авторизации.
        - *args: Переменные позиционных аргументов.
        - **kwargs: Переменные ключевых аргументов.

        ### Returns:
        - HttpRequest: HTTP-ответ.

        """
        user_id = int(user_id)
        key = str(key)
        user = User.objects.filter(tg_id=user_id).first()
        if not user:
            return redirect('index')

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
    """Просмотр и редактирование профиля пользователя.

    ### Args:
    - request (`HttpRequest`): HTTP-запрос.
    - username (`str`): Имя пользователя.

    ### Returns:
    - HttpResponse: HTTP-ответ.

    """
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


def get_coordinates(tg_id: int) -> QuerySet[Location]:
    """Получение последних координат пользователя.

    ### Args:
    - tg_id (`int`) - Телеграмм id пользователя.

    ### Returns:
    - `QuerySet[Location]`:
        - latitude (:obj:`float`)
        - longitude (:obj:`float`)
        - timezone (:obj:`str`)
    """
    user = User.objects.filter(tg_id=tg_id).first()
    return user.locations.first() if user else None


def set_coordinates(update: Update, _: CallbackContext, user: User = None) -> None:
    """Получение часового пояса на основе координат пользователя и запись его в базу данных.

    ### Args:
    - update (`Update`): Объект обновления из Telegram.
    - context (`CallbackContext`): Контекст обработчика.

    ### Returns:
    - None
    """
    chat = update.effective_chat
    user_id = chat.id
    latitude = update.message.location.latitude
    longitude = update.message.location.longitude
    if not user:
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
    """Блокировка пользователя после нескольких неудачных попыток авторизации.

    ### Args:
    - request (`HttpRequest`): HTTP-запрос, который вызвал эту функцию.

    ### Returns:
    - HttpResponse: Страница с сообщением о блокировке.

    """
    text = f'Вы заблокированы на {int(settings.DEFENDER_COOLOFF_TIME/60)} минут!'
    context = {
        'text': text,
    }
    template = 'users/block.html'
    return render(request, template, context)

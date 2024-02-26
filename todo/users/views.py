import json
import secrets
import string
import uuid
from datetime import timedelta
from typing import Any, Dict, List, OrderedDict

import requests
from core.serializers import ModelDataSerializer
from django.conf import settings
from django.contrib.auth import get_user_model, login
from django.contrib.auth.decorators import login_required
from django.core.files import File
from django.core.files.base import ContentFile
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
redis_client = settings.REDIS_CLIENT


class Authentication:
    """Класс для аутентификации пользователей и регистрации новых пользователей в системе."""

    valid_time: int = 5

    def __init__(self, update, context, user=None):
        """Инициализация объекта класса."""
        self.update = update
        self.context = context
        self.chat = update.effective_chat
        self.tg_user = update.effective_user
        self.user = user

    def register(self) -> Dict[str, Any]:
        """Регистрация нового пользователя в системе."""
        try:
            self.user, created = self.get_user_by_telegram_id()

            delete_messages_by_time.apply_async(
                args=[self.chat.id, self.update.effective_message.message_id],
                countdown=0
            )

            if created or self.user.is_blocked_bot:
                self.user.set_password(self.get_password(length=15))
                self.save_user_location()

            validation_key = self.generate_validation_key()
            reply_text = self.compose_auth_link_message(validation_key, created)
            message_id = self.send_messages(reply_text)

            if self.context.args:
                self.send_url_by_user()

            self.user.is_blocked_bot = False

            self.user.validation_message_id = message_id
            self.user.save()

            user_manager = UserRedisManager()
            user_manager.set_user_in_redis(self.tg_user, self.user)

            if not self.user.image:
                self.add_profile_picture.apply_async(args=(self.tg_user.id, ModelDataSerializer.serialize(self.user),))

            return None
        except Exception as err:
            self.handle_registration_error(err)

    def authorization(self) -> Dict[str, Any]:
        """Аутентификация пользователя."""
        try:
            validation_key = self.generate_validation_key()
            reply_text = self.compose_auth_link_message(validation_key)
            message_id = self.send_messages(reply_text)
            self.user.validation_message_id = message_id
            self.user.save()

            if not self.user.image:
                self.add_profile_picture.apply_async(args=(self.tg_user.id, ModelDataSerializer.serialize(self.user),))

            return None
        except Exception as err:
            self.handle_authorization_error(err)

    def send_messages(self, reply_text: List[str]) -> int:
        """Отправка сообщений пользователю."""
        try:
            message_id = self.update.message.reply_text(text=reply_text, parse_mode='Markdown').message_id
        except Exception:
            message_id = self.update.message.reply_text(text=reply_text).message_id

        lifetime = 60 * self.valid_time
        delete_messages_by_time.apply_async(
            args=[self.chat.id, message_id],
            countdown=lifetime
        )
        return message_id

    def get_user_by_telegram_id(self):
        """Получает пользователя по его Telegram ID или создает нового."""
        user, created = User.objects.get_or_create(tg_id=self.tg_user.id, defaults={"username": self.tg_user.username})
        return user, created

    def send_url_by_user(self):
        user_uuid = self.context.args[0]
        redirect_url = redis_client.get(f'redirect_url_by_user_id:{user_uuid}')
        if redirect_url:
            redis_client.delete(f'redirect_url_by_user_id:{user_uuid}')
            redis_client.setex(f'redirect_url_by_user_id:{self.tg_user.id}', 600, redirect_url)

    def generate_validation_key(self) -> str:
        """Генерирует ключ для валидации пользователя."""
        validation_key = self.get_password(length=28)
        self.user.validation_key = validation_key
        self.user.validation_key_time = timezone.now().astimezone(timezone.utc)
        return validation_key

    def compose_auth_link_message(self, validation_key: str, is_new_user: bool = False) -> str:
        """Формирует сообщение со ссылкой для аутентификации на сайте."""
        if is_new_user:
            preview_text = (
                'Поздравляем с успешной регистрацией в проекте "Your To-Do"! \n\n🎉🎉🎉\n\n'
                'На нашем сайте Вы найдете захватывающий контент для всех, кто увлечен программированием.\n\n'
                'Также у Вас есть возможность пообщаться с нашим ботом Евой на любые интересующие вас темы.\n\n'
                'Создавайте напоминания, и они будут отправлены прямо в этот чат или в выбранную группу. 📅\n\n'
                'И это далеко не все... Откройте для себя множество других возможностей!\n\n'
            )
        else:
            preview_text = ""
        auth_link = (
            f'Для авторизации на [сайте](https://www.{settings.DOMAIN}) пройдите по ссылке:\n〰\n'
            f'✔️ [https://www.{settings.DOMAIN}/auth/](https://www.{settings.DOMAIN}/auth/login/tg/{self.tg_user.id}/{validation_key}/)\n〰'
        )
        return preview_text + auth_link

    def save_user_location(self):
        """Сохранение местоположения пользователя при регистрации."""
        if not self.user.locations.exists():
            Location.objects.create(user=self.user, latitude=59.799, longitude=30.274)

    def handle_registration_error(self, err):
        """Обработка ошибок при регистрации пользователя."""
        error_message = f"Ошибка при регистрации пользователя c id-{self.tg_user.id} и username-{self.tg_user.username}:\n{err}"
        self.context.bot.send_message(self.tg_user.id, "Произошла ошибка при регистрации. Попробуйте позже.")
        self.context.bot.send_message(ADMIN_ID, error_message)

    def handle_authorization_error(self, err):
        """Обработка ошибок при авторизации пользователя."""
        error_message = f"Ошибка при авторизации пользователя c id-{self.tg_user.id} и username-{self.tg_user.username}:\n{err}"
        self.context.bot.send_message(self.tg_user.id, "Произошла ошибка при авторизации. Попробуйте позже.")
        self.context.bot.send_message(ADMIN_ID, error_message)

    @staticmethod
    def get_password(length: int) -> str:
        """Генератор паролей."""
        characters = string.ascii_letters + string.digits
        return ''.join(secrets.choice(characters) for _ in range(length))

    @staticmethod
    @app.task(ignore_result=True)
    def add_profile_picture(tg_user_id: int, user: OrderedDict):
        """Добавляет фотографию профиля пользователя из Telegram."""
        user = ModelDataSerializer.deserialize(user)
        session = requests.Session()

        try:
            photos_url = f'https://api.telegram.org/bot{settings.TELEGRAM_TOKEN}/getUserProfilePhotos'
            photos_response = session.get(photos_url, params={'user_id': tg_user_id})
            photos_response.raise_for_status()
            photos_data = photos_response.json()
            if not photos_data['result']['photos']:
                return None

            file_id = photos_data['result']['photos'][0][0]['file_id']

            file_url = f'https://api.telegram.org/bot{settings.TELEGRAM_TOKEN}/getFile'
            file_response = session.get(file_url, params={'file_id': file_id})
            file_response.raise_for_status()
            file_path = file_response.json()['result']['file_path']

            photo_url = f'https://api.telegram.org/file/bot{settings.TELEGRAM_TOKEN}/{file_path}'
            photo_response = session.get(photo_url)
            photo_response.raise_for_status()

            file_name = f"{uuid.uuid4()}.jpg"
            user.image.save(file_name, ContentFile(photo_response.content))

        except requests.RequestException as e:
            print(f"Ошибка при загрузке или сохранении фотографии профиля c tg_id {tg_user_id}: {e}")

        finally:
            session.close()


class LoginTgLinkView(View):
    """Класс для авторизации пользователя по ссылке из Телеграм.

    ### Attributes:
    - valid_time (`int`): Время действия ссылки в минутах.

    ### Methods:
    - get: Авторизует пользователя по ссылке из Телеграм.

    """
    valid_time: int = 10

    def get(self, request: HttpRequest, user_id: str, key: str) -> HttpRequest:
        """Авторизует пользователя по ссылке из Телеграм.

        ### Args:
        - request (HttpRequest): HTTP-запрос.
        - user_id (str): Идентификатор пользователя в Телеграм.
        - key (str): Ключ для авторизации.

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

        url = self.get_url_from_redis(user_id) or 'index'
        return redirect(url)

    def get_url_from_redis(self, user_id):
        url = redis_client.get(f'redirect_url_by_user_id:{user_id}')
        if not url:
            return None
        redis_client.delete(f'redirect_url_by_user_id:{user_id}')
        return json.loads(url)


class LoginTgButtonView(View):

    def get(self, request: HttpRequest) -> HttpRequest:
        """Отправляет JSON с URL для авторизации через Телеграмм."""
        user_id = uuid.uuid4()
        telegram_url = f'https://t.me/{settings.TELEGRAM_BOT_NAME}?start={user_id}'
        referer_url = request.META.get('HTTP_REFERER')
        redis_client.setex(f'redirect_url_by_user_id:{str(user_id)}', 300, json.dumps(referer_url))
        return JsonResponse({'url': telegram_url})


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


def set_coordinates(update: Update, _: CallbackContext, user: QuerySet = None) -> None:
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


class LoginTgView(View):
    """
    Класс для обработки аутентификации пользователя через Telegram виджет.
    """

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpRequest:
        """В данный момент не работает из-за cookies"""
        data = request.GET
        if not HashCheck(data).check_hash():
            return render(request, 'users/error.html', {'msg': 'Bad hash!'})

        photo_url = data.get('photo_url', None)
        keys = {'tg_id': 'id', 'username': 'username', 'first_name': 'first_name', 'last_name': 'last_name'}
        user_info = {k: data.get(v) for k, v in keys.items() if data.get(v) is not None}

        response = requests.get(photo_url, timeout=5)
        if response.status_code == 200:
            temp_file = NamedTemporaryFile(delete=True)
            temp_file.write(response.content)
            temp_file.flush()

        user, status = User.objects.get_or_create(tg_id=user_info.pop('tg_id'))
        if status:
            user.set_password(Authentication.get_password())

        for key, value in user_info.items():
            setattr(user, key, value)
        user.image.save(f'{uuid.uuid4}.jpg', File(temp_file))
        user.save()
        temp_file.close()
        login(request, user)
        return redirect('index')

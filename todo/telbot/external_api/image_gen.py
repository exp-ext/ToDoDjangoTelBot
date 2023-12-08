import asyncio
import json
from datetime import datetime, timedelta, timezone
from io import BytesIO

import httpx
import requests
from asgiref.sync import sync_to_async
from django.conf import settings
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from dotenv import load_dotenv
from httpx_socks import AsyncProxyTransport
from PIL import Image
from requests.adapters import HTTPAdapter
from telegram import ChatAction, ParseMode, Update
from telegram.ext import CallbackContext, ConversationHandler
from urllib3 import Retry

from ..checking import check_registration
from ..cleaner import remove_keyboard
from ..models import HistoryDALLE

load_dotenv()

redis_client = settings.REDIS_CLIENT
User = get_user_model()


class GetAnswerDallE():
    """
    Проверяет регистрацию.
    Делает запрос и в чат Telegram возвращает результат ответа от API ИИ Dall-E.
    """

    ERROR_TEXT = (
        'Что-то пошло не так 🤷🏼\n'
        'Возможно большой наплыв запросов, которые я не успеваю обрабатывать 🤯'
    )
    MAX_TYPING_TIME = 5
    STORY_WINDOWS_TIME = 5
    MODEL = 'dall-e-3'
    IMAGE_COUNT = 1

    def __init__(self, update: Update, context: CallbackContext) -> None:
        self.update = update
        self.context = context
        self.current_time = None
        self.time_start = None
        self.telegram_file_id = None
        self.image_url = None
        self.media_group = {}
        self.chat_id = update.effective_chat.id
        self.message_text = update.effective_message.text
        self.event = asyncio.Event()
        self.set_user()
        self.set_windows_time()

    async def get_image_dall_e(self):
        """
        Возвращает серию картинок от АПИ Dall-e 3.
        Предварительно вызвав функцию проверки регистрации.
        """
        if await self.check_in_works():
            return {'code': 423}

        try:
            asyncio.create_task(self.send_typing_periodically())
            await self.request_to_openai()
            await self.reply_to_user_requests()
            self.event.set()
            await self.save_request()

        except Exception as err:
            self.context.bot.send_message(
                chat_id=settings.TELEGRAM_ADMIN_ID,
                text=f'Ошибка в Dall-E: {err}',
            )
        finally:
            await self.del_mess_in_redis()

    async def reply_to_user_httpx(self) -> None:
        """!!! Отправляет ответ пользователю. Не работает с Minio и OpenAI на текущий момент. !!!"""
        transport = AsyncProxyTransport.from_url(settings.SOCKS5)
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        }
        async with httpx.AsyncClient(transport=transport, http1=True) as client:
            response = await client.get(self.media_group['url'], timeout=60 * self.MAX_TYPING_TIME, headers=headers)
            if response.status_code == 200:
                caption = self.media_group['caption']
                image = Image.open(BytesIO(response.content))
                image = image.convert("RGBA")
                with BytesIO() as bio:
                    image.save(bio, "PNG")
                    bio.seek(0)
                    msg = self.context.bot.send_photo(
                        chat_id=self.chat_id,
                        photo=bio,
                        caption=caption,
                        reply_to_message_id=self.update.message.message_id
                    )
                self.telegram_file_id = msg.effective_attachment[4].file_id

    @sync_to_async
    def reply_to_user_requests(self) -> None:
        """Отправляет ответ пользователю."""
        retries = Retry(total=5, backoff_factor=1, status_forcelist=[502, 503, 504])
        adapter = HTTPAdapter(max_retries=retries)
        session = requests.Session()
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        }
        response = session.get(self.media_group['url'], headers=headers, timeout=60 * self.MAX_TYPING_TIME)
        if response.status_code == 200:
            image = Image.open(BytesIO(response.content))
            image = image.convert("RGBA")
            with BytesIO() as bio:
                image.save(bio, "PNG")
                bio.seek(0)
                msg = self.context.bot.send_photo(
                    chat_id=self.chat_id,
                    photo=bio,
                    caption=self.media_group['caption'],
                    reply_to_message_id=self.update.message.message_id
                )

            self.telegram_file_id = msg.effective_attachment[4].file_id
        session.close()

    async def save_request(self):
        """Сохраняет запрос в БД."""
        async with httpx.AsyncClient() as client:
            get_url = f'https://api.telegram.org/bot{settings.TELEGRAM_TOKEN}/getFile?file_id={self.telegram_file_id}'
            response = await client.get(get_url)

            if response.is_error:
                raise Exception(f"Ошибка при получении файла от Телеграмм: {response.text}")

            file_path = response.json().get('result', {}).get('file_path')
            if not file_path:
                raise Exception("File path не найден в ответе!")

            image_url = f'https://api.telegram.org/file/bot{settings.TELEGRAM_TOKEN}/{file_path}'
            instance = HistoryDALLE(
                user=self.user,
                question=self.message_text,
                answer={'media': image_url, 'caption': self.media_group['caption']}
            )
            await instance.save()

    async def send_typing_periodically(self) -> None:
        """"
        Передаёт TYPING в чат Телеграм откуда пришёл запрос.
        """
        time_stop = datetime.now() + timedelta(minutes=GetAnswerDallE.MAX_TYPING_TIME)

        while not self.event.is_set():
            self.context.bot.send_chat_action(
                chat_id=self.chat_id,
                action=ChatAction.UPLOAD_PHOTO
            )
            await asyncio.sleep(2)
            if datetime.now() > time_stop:
                break

    async def request_to_openai(self) -> list:
        """
        Делает запрос в OpenAI.
        """
        transport = AsyncProxyTransport.from_url(settings.SOCKS5)
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings.CHAT_GPT_TOKEN}"
        }
        data = {
            "model": self.MODEL,
            "prompt": self.message_text,
            "size": "1792x1024",
            "n": self.IMAGE_COUNT,
            "quality": "hd"
        }
        async with httpx.AsyncClient(transport=transport) as client:
            response = await client.post(
                "https://api.openai.com/v1/images/generations",
                headers=headers,
                json=data,
                timeout=60 * self.MAX_TYPING_TIME,
            )
        completion = json.loads(response.content)
        self.media_group.update({
            'url': completion['data'][0]['url'],
            'caption': completion['data'][0]['revised_prompt'],
        })

    def set_user(self) -> None:
        """Определяем и назначаем  атрибут user."""
        self.user = get_object_or_404(User, username=self.update.effective_user.username)

    def set_windows_time(self) -> None:
        """Определяем и назначаем атрибуты current_time и time_start."""
        self.current_time = datetime.now(timezone.utc)
        self.time_start = self.current_time - timedelta(minutes=GetAnswerDallE.STORY_WINDOWS_TIME)

    @sync_to_async
    def check_in_works(self) -> bool:
        """Проверяет нет ли уже в работе этого запроса в Redis."""
        queries = redis_client.lrange(f'dal_e_user:{self.user.id}', 0, -1)
        if self.message_text.encode('utf-8') in queries:
            return True
        redis_client.lpush(f'dal_e_user:{self.user.id}', self.message_text)
        return False

    @sync_to_async
    def del_mess_in_redis(self) -> bool:
        """Удаляет входящее сообщение из Redis."""
        redis_client.lrem(f'dal_e_user:{self.user.id}', 1, self.message_text.encode('utf-8'))


def for_check(update: Update, context: CallbackContext):
    answers_for_check = {
        '': (f'К сожалению данная функция доступна только для [зарегистрированных пользователей]({context.bot.link})'),
    }
    return check_registration(update, context, answers_for_check)


def first_step_get_image(update: Update, context: CallbackContext):
    if for_check(update, context):
        chat = update.effective_chat
        message_thread_id = update.effective_message.message_thread_id
        req_text = (
            f'*{update.effective_user.first_name}*, '
            'введите текст для генерации картинки на английском языке'
        )
        message_id = context.bot.send_message(
            chat.id,
            req_text,
            parse_mode=ParseMode.MARKDOWN,
            message_thread_id=message_thread_id
        ).message_id
        context.user_data['image_gen'] = message_id
        remove_keyboard(update, context)
        return 'image_gen'


def get_image_dall_e(update: Update, context: CallbackContext):
    """
    Удаление и проверка сообщения от first_step_get_image.
    Вход в класс GetAnswerDallE и в случае возврата любого
    значения кроме с кодом 423, возврат ConversationHandler.
    """
    del_id = context.user_data.pop('image_gen', None)
    if del_id:
        context.bot.delete_message(update.effective_chat.id, del_id)
    get_answer = GetAnswerDallE(update, context)
    asyncio.run(get_answer.get_image_dall_e())
    return ConversationHandler.END

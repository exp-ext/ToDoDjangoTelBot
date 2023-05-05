import asyncio
import os
from datetime import datetime, timedelta, timezone

import openai
import tiktoken
from asgiref.sync import sync_to_async
from django.contrib.auth import get_user_model
from dotenv import load_dotenv
from telegram import ChatAction, ParseMode, Update
from telegram.ext import CallbackContext

from ..checking import check_registration
from ..models import HistoryAI

load_dotenv()

openai.api_key = os.getenv('CHAT_GP_TOKEN')

User = get_user_model()
ADMIN_ID = os.getenv('ADMIN_ID')


class GetAnswerDavinci():
    """
    Проверяет регистрацию.
    Делает запрос и в чат Telegram возвращает результат ответа
    от API ИИ Dall-E.
    """
    ERROR_TEXT = (
        'Что-то пошло не так 🤷🏼\n'
        'Возможно большой наплыв запросов, '
        'которые я не успеваю обрабатывать 🤯'
    )
    MODEL = 'gpt-3.5-turbo-0301'
    MAX_LONG_MESSAGE = 1024
    MAX_LONG_REQUEST = 4096
    STORY_WINDOWS_TIME = 30
    MAX_TYPING_TIME = 10

    def __init__(self,
                 update: Update,
                 context: CallbackContext) -> None:
        self.update = update
        self.context = context
        self.user = None
        self.message_text = None
        self.message_tokens = None
        self.current_time = None
        self.time_start = None
        self.answer_text = GetAnswerDavinci.ERROR_TEXT
        self.answer_tokens = None
        self.event = asyncio.Event()
        self.prompt = [
            {
                'role': 'system',
                'content': (
                    'You are an experienced senior software developer with '
                    'extensive experience leading teams, mentoring junior '
                    'developers, and providing high-quality software '
                    'solutions to customers, giving answers only in '
                    'Markdown and preferably in plain Russian.'
                )
            }
        ]
        self.set_windows_time()
        self.set_message_text()
        self.set_user()

    @classmethod
    def num_tokens_from_message(cls, message):
        try:
            encoding = tiktoken.encoding_for_model(GetAnswerDavinci.MODEL)
        except KeyError:
            encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(message)) + 4

    async def get_answer_davinci(self) -> dict:
        """Основная логика."""
        if await self.check_in_works():
            return {'code': 423}

        if self.check_long_query:
            answer_text = (
                f'{self.user.first_name}, у Вас слишком большой текст запроса.'
                ' Попробуйте сформулировать его короче.'
            )
            self.context.bot.send_message(
                chat_id=self.update.effective_chat.id,
                text=answer_text,
                reply_to_message_id=self.update.message.message_id
            )
            return {'code': 400}

        try:
            asyncio.create_task(self.send_typing_periodically())
            await self.request_to_openai()
            asyncio.create_task(self.create_update_history_ai())

        except Exception as err:
            self.context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f'Ошибка в ChatGPT: {err.args[0]}',
            )
        finally:
            self.context.bot.send_message(
                chat_id=self.update.effective_chat.id,
                text=self.answer_text,
                reply_to_message_id=self.update.message.message_id,
                parse_mode=ParseMode.MARKDOWN
            )

    async def send_typing_periodically(self) -> None:
        """"
        Передаёт TYPING в чат Телеграм откуда пришёл запрос.
        """
        time_stop = (
            datetime.now()
            + timedelta(minutes=GetAnswerDavinci.MAX_TYPING_TIME)
        )
        while not self.event.is_set():
            self.context.bot.send_chat_action(
                chat_id=self.update.effective_chat.id,
                action=ChatAction.TYPING
            )
            await asyncio.sleep(2)
            if datetime.now() > time_stop:
                break

    @sync_to_async
    def request_to_openai(self) -> None:
        """
        Делает запрос в OpenAI и выключает typing.
        """
        self.get_prompt()
        answer = openai.ChatCompletion.create(
            model=GetAnswerDavinci.MODEL,
            messages=self.prompt,
            temperature=0.1,
        )
        self.answer_text = answer.choices[0].message.get('content')
        self.answer_tokens = self.num_tokens_from_message(self.answer_text)
        self.event.set()

    def get_prompt(self) -> None:
        """
        Prompt для запроса в OpenAI и модель user.
        """
        history = (
            self.user
            .history_ai
            .filter(
                created_at__range=[self.time_start, self.current_time]
            )
            .exclude(answer__in=[None, GetAnswerDavinci.ERROR_TEXT])
            .values('question', 'question_tokens', 'answer', 'answer_tokens')
        )
        max_tokens = self.message_tokens + 96
        for item in history:
            max_tokens += item['question_tokens'] + item['answer_tokens']
            if max_tokens >= GetAnswerDavinci.MAX_LONG_REQUEST:
                break
            self.prompt.extend([
                {
                    'role': 'system',
                    'name': self.user.username,
                    'content': item['question']
                },
                {
                    'role': 'system',
                    'name': 'Eva',
                    'content': item['answer']
                }
            ])
        self.prompt.append({'role': 'user', 'content': self.message_text})

    async def check_in_works(self) -> bool:
        """Проверяет нет ли уже в работе этого запроса."""
        exists = await sync_to_async(
            self.user.history_ai.filter(
                created_at__range=[self.time_start, self.current_time],
                question=self.message_text
            ).exists
        )()
        if exists:
            return True
        asyncio.create_task(self.create_update_history_ai())
        return False

    async def create_update_history_ai(self):
        """Создаём и обновляем запись в модели."""
        history_ai = HistoryAI(
            user=self.user,
            question=self.message_text,
            question_tokens=self.message_tokens,
            answer=self.answer_text,
            answer_tokens=self.answer_tokens
        )
        await history_ai.save()

    def set_user(self) -> None:
        """Определяем и назначаем  атрибут user."""
        self.user = (
            User.objects
            .prefetch_related('history_ai')
            .get(username=self.update.effective_user.id)
        )

    def set_message_text(self) -> str:
        """Определяем и назначаем атрибут message_text."""
        self.message_text = (
            self.update.effective_message.text.replace('#', '', 1)
        )
        self.message_tokens = self.num_tokens_from_message(self.message_text)

    def set_windows_time(self) -> None:
        """Определяем и назначаем атрибуты current_time и time_start."""
        self.current_time = datetime.now(timezone.utc)
        self.time_start = (
            self.current_time
            - timedelta(minutes=GetAnswerDavinci.STORY_WINDOWS_TIME)
        )

    @property
    def check_long_query(self) -> bool:
        return self.message_tokens > GetAnswerDavinci.MAX_LONG_MESSAGE


def for_check(update: Update, context: CallbackContext):
    answers_for_check = {
        '?': ('Я мог бы ответить Вам, если '
              f'[зарегистрируетесь]({context.bot.link}) 🧐'),
        '!': ('Я обязательно поддержу Вашу дискуссию, если '
              f'[зарегистрируетесь]({context.bot.link}) 🙃'),
        '': ('Какая интересная беседа, [зарегистрируетесь]'
             f'({context.bot.link}) и я подключусь к ней 😇'),
    }
    return check_registration(update, context, answers_for_check)


def get_answer_davinci_public(update: Update, context: CallbackContext):
    if for_check(update, context):
        get_answer = GetAnswerDavinci(update, context)
        asyncio.run(get_answer.get_answer_davinci())


def get_answer_davinci_person(update: Update, context: CallbackContext):
    if update.effective_chat.type == 'private' and for_check(update, context):
        get_answer = GetAnswerDavinci(update, context)
        asyncio.run(get_answer.get_answer_davinci())

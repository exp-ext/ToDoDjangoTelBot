import asyncio
from datetime import datetime, timedelta, timezone

import telegram
import tiktoken
from asgiref.sync import sync_to_async
from django.conf import settings
from django.contrib.auth import get_user_model
from openai import AsyncOpenAI
from telegram import ChatAction, ParseMode, Update
from telegram.ext import CallbackContext

from ..checking import check_registration
from ..models import HistoryAI

ADMIN_ID = settings.TELEGRAM_ADMIN_ID

User = get_user_model()
redis_client = settings.REDIS_CLIENT
client = AsyncOpenAI(api_key=settings.CHAT_GPT_TOKEN,)


class GetAnswerGPT():
    """
    Проверяет регистрацию.
    Делает запрос и в чат Telegram возвращает результат ответа
    от API ИИ Dall-E.
    """
    ERROR_TEXT = (
        'Что-то пошло не так 🤷🏼\n'
        'Возможно большой наплыв запросов, которые я не успеваю обрабатывать 🤯'
    )
    MODEL = 'gpt-3.5-turbo-1106'
    MAX_LONG_MESSAGE = 1024
    MAX_LONG_REQUEST = 4096
    STORY_WINDOWS_TIME = 30
    MAX_TYPING_TIME = 10

    def __init__(self, update: Update, context: CallbackContext) -> None:
        self.update = update
        self.context = context
        self.user = None
        self.message_text = None
        self.message_tokens = None
        self.current_time = None
        self.time_start = None
        self.answer_text = GetAnswerGPT.ERROR_TEXT
        self.answer_tokens = None
        self.event = asyncio.Event()
        self.request_massage = None
        self.prompt = [
            {
                'role': 'system',
                'content':
                    'Your name is Eva and you are an Russian experienced senior software developer with extensive experience leading '
                    'teams, mentoring all developers, and delivering high-quality software solutions to customers. You can '
                    'give answers in Markdown format using only:'
                    '*bold text* _italic text_'
                    '[inline URL](http://www.example.com/)'
                    '`inline fixed-width code`'
                    '``` pre-formatted fixed-width code block ```'
            }
        ]
        self.set_windows_time()
        self.set_message_text()
        self.set_user()
        self.get_prompt()

    @classmethod
    def num_tokens_from_message(cls, message):
        try:
            encoding = tiktoken.encoding_for_model(GetAnswerGPT.MODEL)
        except KeyError:
            encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(message)) + 4

    async def get_answer_davinci(self) -> dict:
        """Основная логика."""
        if await self.check_in_works():
            return {'code': 423}

        if self.check_long_query:
            answer_text = (
                f'{self.user.first_name}, у Вас слишком большой текст запроса. Попробуйте сформулировать его короче.'
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
            asyncio.create_task(self.create_history_ai())

        except Exception as err:
            self.context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f'Ошибка в получении ответа от ChatGPT: {err.args[0]}',
            )
        finally:
            await self.reply_to_user()
            await self.del_mess_in_redis()

    @sync_to_async
    def reply_to_user(self) -> None:
        """Отправляет ответ пользователю."""
        try:
            self.context.bot.send_message(
                chat_id=self.update.effective_chat.id,
                text=self.answer_text,
                reply_to_message_id=self.update.message.message_id,
                parse_mode=ParseMode.MARKDOWN
            )
        except telegram.error.BadRequest:
            self.context.bot.send_message(
                chat_id=self.update.effective_chat.id,
                text=GetAnswerGPT.ERROR_TEXT,
                reply_to_message_id=self.update.message.message_id,
            )
        except Exception as err:
            self.context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f'Ошибка при отправке ответа ChatGPT: {err.args[0]}',
            )

    async def send_typing_periodically(self) -> None:
        """"Передаёт TYPING в чат Телеграм откуда пришёл запрос."""
        time_stop = datetime.now() + timedelta(minutes=GetAnswerGPT.MAX_TYPING_TIME)

        while not self.event.is_set():
            self.context.bot.send_chat_action(
                chat_id=self.update.effective_chat.id,
                action=ChatAction.TYPING
            )
            await asyncio.sleep(2)
            if datetime.now() > time_stop:
                break

    async def request_to_openai(self) -> None:
        """Делает запрос в OpenAI и выключает typing."""

        completion = await client.chat.completions.create(
            model=GetAnswerGPT.MODEL,
            messages=self.prompt,
            temperature=0.1,
        )
        self.answer_text = completion.choices[0].message.content
        self.answer_tokens = completion.usage.completion_tokens
        self.message_tokens = completion.usage.prompt_tokens
        self.event.set()

    def get_prompt(self) -> None:
        """Prompt для запроса в OpenAI и модель user."""
        history = (
            self.user
            .history_ai
            .filter(created_at__range=[self.time_start, self.current_time])
            .exclude(answer__isnull=True)
            .values('question', 'question_tokens', 'answer', 'answer_tokens')
        )
        max_tokens = self.message_tokens + 120
        for item in history:
            max_tokens += item['question_tokens'] + item['answer_tokens']
            if max_tokens >= GetAnswerGPT.MAX_LONG_REQUEST:
                break
            self.prompt.extend([
                {
                    'role': 'user',
                    'name': self.user.username,
                    'content': item['question']
                },
                {
                    'role': 'assistant',
                    'name': 'Eva',
                    'content': item['answer']
                }
            ])
        self.prompt.append({'role': 'user', 'content': self.message_text})

    @sync_to_async
    def check_in_works(self) -> bool:
        """Проверяет нет ли уже в работе этого запроса в Redis."""
        queries = redis_client.lrange(f'gpt_user:{self.user.id}', 0, -1)
        if self.message_text.encode('utf-8') in queries:
            return True
        redis_client.lpush(f'gpt_user:{self.user.id}', self.message_text)
        return False

    @sync_to_async
    def del_mess_in_redis(self) -> bool:
        """Удаляет входящее сообщение из Redis."""
        redis_client.lrem(f'gpt_user:{self.user.id}', 1, self.message_text.encode('utf-8'))

    async def create_history_ai(self):
        """Создаём запись в БД."""
        self.request_massage = HistoryAI(
            user=self.user,
            question=self.message_text,
            question_tokens=self.message_tokens,
            answer=self.answer_text,
            answer_tokens=self.answer_tokens
        )
        await self.request_massage.save()

    @sync_to_async
    def get_request_massage(self) -> None:
        """Получает сообщение из БД, если оно там есть."""
        try:
            self.request_massage = self.user.history_ai.get(
                created_at__range=[self.time_start, self.current_time],
                question=self.message_text
            )
        except HistoryAI.DoesNotExist:
            pass

    def set_user(self) -> None:
        """Определяем и назначаем  атрибут user."""
        self.user = (
            User.objects
            .prefetch_related('history_ai')
            .get(username=self.update.effective_user.username)
        )

    def set_message_text(self) -> str:
        """Определяем и назначаем атрибут message_text."""
        self.message_text = self.update.effective_message.text
        self.message_tokens = self.num_tokens_from_message(self.message_text)

    def set_windows_time(self) -> None:
        """Определяем и назначаем атрибуты current_time и time_start."""
        self.current_time = datetime.now(timezone.utc)
        self.time_start = self.current_time - timedelta(minutes=GetAnswerGPT.STORY_WINDOWS_TIME)

    @property
    def check_long_query(self) -> bool:
        return self.message_tokens > GetAnswerGPT.MAX_LONG_MESSAGE


def for_check(update: Update, context: CallbackContext):
    answers_for_check = {
        '?': (f'Я мог бы ответить Вам, если [зарегистрируетесь]({context.bot.link}) 🧐'),
        '!': (f'Я обязательно поддержу Вашу дискуссию, если [зарегистрируетесь]({context.bot.link}) 🙃'),
        '': (f'Какая интересная беседа, [зарегистрируетесь]({context.bot.link}) и я подключусь к ней 😇'),
    }
    return check_registration(update, context, answers_for_check)


def get_answer_davinci_public(update: Update, context: CallbackContext):
    if for_check(update, context):
        get_answer = GetAnswerGPT(update, context)
        asyncio.run(get_answer.get_answer_davinci())


def get_answer_davinci_person(update: Update, context: CallbackContext):
    if update.effective_chat.type == 'private' and for_check(update, context):
        get_answer = GetAnswerGPT(update, context)
        asyncio.run(get_answer.get_answer_davinci())

from ai.gpt_exception import (LongQueryError, OpenAIJSONDecodeError,
                              OpenAIResponseError, UnhandledError)
from ai.gpt_query import GetAnswerGPT
from asgiref.sync import sync_to_async
from django.conf import settings
from django.db.models import Model
from openai import APIConnectionError
from telbot.models import HistoryAI
from telbot.service_message import send_message_to_chat
from telegram import ParseMode, Update
from telegram.ext import CallbackContext

ADMIN_ID = settings.TELEGRAM_ADMIN_ID


class TelegramAnswerGPT(GetAnswerGPT):

    def __init__(self, update: Update, _: CallbackContext, user: 'Model') -> None:
        query_text = update.effective_message.text
        assist_prompt = self.init_model_prompt
        history_model = HistoryAI
        self.chat_id = update.effective_chat.id
        self.message_id = update.message.message_id
        super().__init__(query_text, assist_prompt, user, history_model, self.chat_id, 0.3)

    async def answer_from_ai(self) -> dict:
        """Основная логика."""
        try:
            await self.get_answer_chat_gpt()
        except Exception as err:
            user_error_text = (
                'Что-то пошло не так 🤷🏼\n'
                'Возможно большой наплыв запросов, которые я не успеваю обрабатывать 🤯'
            )
            error_messages = {
                LongQueryError: lambda e: str(e),
                OpenAIResponseError: 'Проблема с получением ответа от ИИ. Возможно она устала.',
                APIConnectionError: 'Проблемы соединения. Вероятно ИИ вышла ненадолго.',
                OpenAIJSONDecodeError: user_error_text,
                UnhandledError: user_error_text,
            }
            self.return_text = str(error_messages.get(type(err)))

            await self.handle_error(f'Ошибка в `GetAnswerGPT.answer_from_ai()`: {str(err)}')
        finally:
            await self.reply_to_user()

    async def handle_error(self, err) -> None:
        """Логирование ошибок."""
        error_message = f"Ошибка в блоке Telegram-ChatGPT:\n{err}"
        send_message_to_chat(ADMIN_ID, error_message)

    @sync_to_async
    def reply_to_user(self) -> None:
        """Отправляет ответ пользователю."""
        send_message_to_chat(self.chat_id, self.return_text, self.message_id, ParseMode.MARKDOWN)

    @property
    def init_model_prompt(self) -> str:
        return """
            You are named Eva, an experienced senior software developer with a strong background in team leadership, mentoring all developers, and delivering high-quality software solutions to clients.
            Your primary language is Russian. When formatting the text, please only use this Markdown format:
            **bold text** _italic text_ [inline URL](http://www.example.com/) `inline fixed-width code` ```preformatted block code with fixed width```
            """

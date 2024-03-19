import markdown
from ai.gpt_exception import (LongQueryError, OpenAIConnectionError,
                              OpenAIJSONDecodeError, OpenAIResponseError,
                              UnhandledError)
from ai.gpt_query import GetAnswerGPT
from channels.generic.websocket import AsyncWebsocketConsumer
from django.conf import settings
from django.db.models import Model
from telbot.loader import bot
from telbot.models import HistoryAI

ADMIN_ID = settings.TELEGRAM_ADMIN_ID


class WSAnswerChatGPT(GetAnswerGPT):
    MAX_TYPING_TIME = 3

    def __init__(self, channel_layer: AsyncWebsocketConsumer, room_group_name: str, user: Model, query_text: str, message_count: int) -> None:
        assist_prompt = self.init_model_prompt()
        history_model = HistoryAI
        super().__init__(query_text, assist_prompt, user, history_model)
        self.channel_layer = channel_layer
        self.room_group_name = room_group_name
        self.message_count = message_count

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
                OpenAIConnectionError: 'Проблемы соединения. Вероятно ИИ вышла ненадолго.',
                OpenAIJSONDecodeError: user_error_text,
                UnhandledError: user_error_text,
            }
            self.return_text = str(error_messages.get(type(err)))

            await self.handle_error(f'Ошибка в `GetAnswerGPT.answer_from_ai()`: {str(err)}')
        finally:
            if self.user.is_anonymous and self.message_count == 1:
                welcome_text = (
                    'С большой радостью приветствуем тебя! 🌟\n'
                    'Завершив процесс регистрации и авторизации, ты получишь доступ к уникальной возможности: '
                    'вести диалог с ИИ Ева. Это гораздо больше, чем простые ответы на вопросы — это целый новый мир, '
                    'где ты можешь общаться, учиться и исследовать. Ваш диалог будет тщательно сохранён, '
                    'что позволит легко продолжить общение даже при переходе между страницами сайта. '
                )
                await self.send_chat_message(welcome_text)

            await self.send_chat_message(self.return_text)

    async def send_chat_message(self, message):
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat.message',
                'message': markdown.markdown(message, extensions=['fenced_code']),
                'username': 'Eva',
            }
        )

    async def handle_error(self, err):
        """Логирование ошибок."""
        error_message = f"Ошибка в блоке Сайт-ChatGPT:\n{err}"
        bot.send_message(ADMIN_ID, error_message)

    def init_model_prompt(self):
        return (
            'You are named Eva, an experienced senior software developer with a strong background in team leadership, '
            'mentoring all developers, and delivering high-quality software solutions to clients. Your primary language is Russian.'
        )

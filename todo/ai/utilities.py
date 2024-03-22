import httpx
from ai.gpt_exception import (OpenAIConnectionError, OpenAIResponseError,
                              UnhandledError, handle_exceptions)
from ai.gpt_query import GetAnswerGPT
from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.conf import settings
from django.db.models import Model
from httpx_socks import AsyncProxyTransport
from openai import AsyncOpenAI
from telbot.loader import bot
from telbot.models import HistoryAI

ADMIN_ID = settings.TELEGRAM_ADMIN_ID


class WSAnswerChatGPT(GetAnswerGPT):
    MAX_TYPING_TIME = 3

    def __init__(self, channel_layer: AsyncWebsocketConsumer, room_group_name: str, user: Model, query_text: str, message_count: int) -> None:
        assist_prompt = self.init_model_prompt()
        history_model = HistoryAI
        creativity_controls = {
            'temperature': 0.7,
            'top_p': 0.9,
            'frequency_penalty': 0,
            'presence_penalty': 0,
        }
        super().__init__(query_text, assist_prompt, user, history_model, creativity_controls=creativity_controls)
        self.channel_layer = channel_layer
        self.room_group_name = room_group_name
        self.message_count = message_count

    async def answer_from_ai(self) -> dict:
        """Основная логика."""
        try:
            await self.get_answer_chat_gpt()
        except Exception as err:
            self.return_text, *_ = await handle_exceptions(err, True)
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

    async def send_chat_message(self, message):
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat.message',
                'message': message,
                'username': 'Eva',
            }
        )

    async def httpx_request_to_openai(self) -> None:
        """Делает запрос в OpenAI и выключает typing."""
        try:
            proxy_transport = AsyncProxyTransport.from_url(settings.SOCKS5)
            async with httpx.AsyncClient(transport=proxy_transport) as transport:
                client = AsyncOpenAI(
                    api_key=self.model.token,
                    http_client=transport,
                )
                stream = await client.chat.completions.create(
                    model=self.model.title,
                    messages=self.all_prompt,
                    stream=True,
                    **self.creativity_controls
                )
                first_chunk = True
                async for chunk in stream:
                    self.return_text += chunk.choices[0].delta.content or ""
                    await self.send_chunk_to_websocket(self.return_text, is_start=first_chunk, is_end=False)
                    if first_chunk:
                        first_chunk = False
                await self.send_chunk_to_websocket("", is_end=True)
                self.return_text_tokens = await self.num_tokens(self.return_text, 0)

        except httpx.HTTPStatusError as http_err:
            raise OpenAIResponseError(f'`WSAnswerChatGPT`, ответ сервера был получен, но код состояния указывает на ошибку: {http_err}') from http_err
        except httpx.RequestError as req_err:
            raise OpenAIConnectionError(f'`WSAnswerChatGPT`, проблемы соединения: {req_err}') from req_err
        except Exception as error:
            raise UnhandledError(f'Необработанная ошибка в `WSAnswerChatGPT.httpx_request_to_openai()`: {error}') from error

    async def send_chunk_to_websocket(self, chunk, is_start=False, is_end=False):
        """Отправка части текста ответа через веб-сокет с указанием на статус части потока."""
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat.message',
                'message': chunk,
                'username': 'Eva',
                'is_stream': True,
                'is_start': is_start,
                'is_end': is_end,
            }
        )

    async def handle_error(self, err):
        """Логирование ошибок."""
        error_message = f"Ошибка в блоке Сайт-ChatGPT:\n{err}"
        bot.send_message(ADMIN_ID, error_message)

    async def create_history_ai(self):
        """Создаём запись в БД."""
        history_instance = self.history_model(
            user=self.user if self.user.is_authenticated else None,
            room_group_name=self.room_group_name,
            question=self.query_text,
            question_tokens=self.query_text_tokens,
            answer=self.return_text,
            answer_tokens=self.return_text_tokens
        )
        await sync_to_async(history_instance.save)()

    def init_model_prompt(self):
        return (
            """
            Your name is Eva and are an experienced senior software developer with a strong background in team leadership, mentoring all developers, and delivering high-quality software solutions to clients.
            Your primary language is Russian. When formatting the text, please use only Markdown format.
            """
        )

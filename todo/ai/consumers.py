import asyncio
import json

from channels.generic.websocket import AsyncWebsocketConsumer


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f"chat_{self.room_name}"
        self.message_count = 0

        # Подключение к комнате
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Отключение от комнаты
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        from ai.utils import AnswerChatGPT
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        user = self.scope['user']
        self.message_count += 1

        send_eva = {
            'channel_layer': self.channel_layer,
            'room_group_name': self.room_group_name,
            'user': user,
            'message': message,
            'message_count': self.message_count,
        }

        # Отправка запроса ИИ
        answer_gpt_instance = AnswerChatGPT(**send_eva)
        asyncio.create_task(answer_gpt_instance.get_answer_from_ai())

        # Отправка сообщения в комнату
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat.message',
                'message': message,
                'username': user.username,
            }
        )

    async def chat_message(self, event):
        # Отправка сообщения обратно на клиент
        message = event['message']
        username = event['username']

        message = f'<li class="other">{message}</li>' if username == 'Eva' else f'<li class="self">{message}</li>'

        await self.send(text_data=json.dumps({
            'message': message,
            'username': username,
        }))

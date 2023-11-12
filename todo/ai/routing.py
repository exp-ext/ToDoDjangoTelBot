from ai.consumers import ChatConsumer
from django.urls import re_path

uuid_pattern = r'(?P<room_name>[0-9a-f-]+)/$'

websocket_urlpatterns = [
    re_path(uuid_pattern, ChatConsumer.as_asgi()),
]

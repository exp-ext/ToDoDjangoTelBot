from ai.consumers import ChatConsumer
from django.urls import re_path

websocket_urlpatterns = [
    re_path(r'ws/(?P<room_name>[0-9a-f-]+)/$', ChatConsumer.as_asgi()),
]

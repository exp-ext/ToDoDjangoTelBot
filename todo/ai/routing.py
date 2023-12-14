from ai.consumers import ChatConsumer
from django.urls import re_path

urlpatterns = r'ws/(?P<room_name>[0-9a-f-]+)/$'

websocket_urlpatterns = [
    re_path(urlpatterns, ChatConsumer.as_asgi()),
]

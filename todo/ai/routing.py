from ai.consumers import ChatConsumer
from django.conf import settings
from django.urls import re_path

urlpatterns = r'(?P<room_name>[0-9a-f-]+)/$' if settings.DEBUG else r'ws/(?P<room_name>[0-9a-f-]+)/$'

websocket_urlpatterns = [
    re_path(urlpatterns, ChatConsumer.as_asgi()),
]

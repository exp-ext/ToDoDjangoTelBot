from django.conf import settings
from django.urls import path
from django.views.decorators.csrf import csrf_exempt

from . import views
from .queue import ScheduleProcess

urlpatterns = [
    path(
        f'{settings.TOKEN}/webhooks/',
        csrf_exempt(views.TelegramBotWebhookView.as_view())
    ),
]

# start another process
ScheduleProcess.threading_process()

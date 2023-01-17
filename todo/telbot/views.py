import json
from typing import Any, Dict

from django.http import HttpRequest, JsonResponse
from django.views import View
from telegram import Update

from todo.celery import app
from todo.settings import DEBUG

from .cleaner import clear_commands
from .dispatcher import dispatcher
from .loader import bot


@app.task(ignore_result=True)
def process_telegram_event(update_json: Dict[str, Any]) -> None:
    """Обработка json и распределение запроса."""
    update = Update.de_json(update_json, bot)
    dispatcher.process_update(update)
    if update.message:
        clear_commands(update)


def index(request):
    return JsonResponse({"error": "sup hacker"})


class TelegramBotWebhookView(View):
    """Получение запроса от Телеграмм."""
    def post(self, request: HttpRequest, *args, **kwargs) -> Dict[str, Any]:
        if DEBUG:
            process_telegram_event(json.loads(request.body))
        else:
            process_telegram_event.delay(json.loads(request.body))
        return JsonResponse({"ok": "POST request processed"})

    def get(self, request: HttpRequest, *args, **kwargs) -> Dict[str, Any]:
        return JsonResponse({"ok": "Get request received! But nothing done"})

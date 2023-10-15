import traceback

from django.conf import settings
from django.http import HttpResponseServerError
from telbot.loader import bot

ADMIN_ID = settings.TELEGRAM_ADMIN_ID


class ServerErrorHandlerMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            response = self.get_response(request)
        except Exception as err:
            traceback_str = traceback.format_exc()
            error_message = f'Ошибка 500:\n{err}\n{traceback_str[-2000:]}'
            bot.send_message(ADMIN_ID, error_message)
            return HttpResponseServerError()
        return response

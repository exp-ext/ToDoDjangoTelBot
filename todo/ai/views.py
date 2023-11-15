import asyncio

from django.http import HttpRequest, JsonResponse
from django.views import View

from .utils import AnswerChatGPT, convert_markdown


class AI(View):

    def get(self, request: HttpRequest) -> JsonResponse:
        """Возвращает последние  запросов к ИИ."""
        data = []
        if request.user.is_authenticated:
            history = (
                request.user
                .history_ai
                .exclude(answer__in=[None, AnswerChatGPT.ERROR_TEXT])
                .order_by('-created_at')
                .values('question', 'answer')[:20]
            )
            for item in history[::-1]:
                data.append({
                    'question': item['question'],
                    'answer': convert_markdown(item['answer']),
                })

        response_data = {
            'history': data,
        }
        return JsonResponse(response_data, status=200)

    def post(self, request: HttpRequest) -> JsonResponse:
        """Обращается к ИИ и отправляет ответ в PopUp."""

        question = request.POST.get('message')
        chat_id = request.POST.get('chat_id')
        response_data = {}

        get_answer = AnswerChatGPT(request.user, question)
        message = asyncio.run(get_answer.get_answer_from_ai())

        if message:
            message_html = convert_markdown(message)
            response_data = {
                'chat_id': chat_id,
                'message': message_html,
            }
            return JsonResponse(response_data, status=200)
        return JsonResponse(response_data, status=102)

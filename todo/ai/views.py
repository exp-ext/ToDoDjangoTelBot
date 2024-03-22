from django.http import HttpRequest, JsonResponse
from django.views import View


class AI(View):

    def get(self, request: HttpRequest) -> JsonResponse:
        """Возвращает последние  запросов к ИИ."""
        data = []
        if request.user.is_authenticated:
            history = (
                request.user
                .history_ai
                .exclude(answer__in=(None,))
                .order_by('-created_at')
                .values('question', 'answer')[:20]
            )
            for item in history[::-1]:
                data.append({
                    'question': item['question'],
                    'answer': item['answer'],
                })

        response_data = {
            'history': data,
        }
        return JsonResponse(response_data, status=200)

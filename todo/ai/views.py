from typing import Any, Dict

from django.contrib.auth import get_user_model
from django.http import HttpRequest, JsonResponse
from django.urls import reverse_lazy
from django.views import View
from django.views.generic.edit import UpdateView
from telbot.models import UserGptModels

from .forms import UserGptModelsForm

User = get_user_model()


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


class UserModelsProfile(UpdateView):
    model = UserGptModels
    form_class = UserGptModelsForm
    template_name = 'users/models_profile.html'

    def get_object(self, queryset=None):
        obj, created = UserGptModels.objects.get_or_create(user=self.request.user)
        return obj

    def get_form_kwargs(self):
        kwargs = super(UserModelsProfile, self).get_form_kwargs()
        kwargs['instance'] = self.get_object()
        return kwargs

    def get_success_url(self) -> Dict[str, Any]:
        return reverse_lazy('models_profile', kwargs={'username': self.request.user.username})

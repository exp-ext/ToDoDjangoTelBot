from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django_user_agents.utils import get_user_agent


def about_view(request: HttpRequest) -> HttpResponse:
    """Контакты."""
    user_agent = get_user_agent(request)
    context = {
        'is_mobile': user_agent.is_mobile,
    }
    template = 'about/support.html'
    return render(request, template, context)

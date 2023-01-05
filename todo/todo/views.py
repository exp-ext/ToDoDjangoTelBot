from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django_user_agents.utils import get_user_agent


def index(request: HttpRequest) -> HttpResponse:

    text = """
    <H1>Приветствую тебя, мой друг!</H1>
    """

    user_agent = get_user_agent(request)
    context = {
        'page_obj': text,
        'is_mobile': user_agent.is_mobile,
    }
    template = 'main/index.html'
    return render(request, template, context)

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render


def index(request: HttpRequest) -> HttpResponse:

    text = """
    <H1>Приветствую тебя, мой друг!</H1>
    """

    context = {
        'page_obj': text,
    }
    template = 'main/index.html'
    return render(request, template, context)

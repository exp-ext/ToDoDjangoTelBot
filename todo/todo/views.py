from django.http import HttpRequest, HttpResponse
from django.shortcuts import render


def index(request: HttpRequest) -> HttpResponse:

    context = {
        'page_obj': 'sup hacker',
    }
    template = 'main/index.html'
    return render(request, template, context)

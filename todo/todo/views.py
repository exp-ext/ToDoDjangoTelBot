from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET
from django_user_agents.utils import get_user_agent


def index(request: HttpRequest) -> HttpResponse:
    """Главная страница сайта."""
    is_main = True
    user_agent = get_user_agent(request)
    context = {
        'is_main': is_main,
        'is_mobile': user_agent.is_mobile,
    }
    template = 'main/index.html'
    return render(request, template, context)


@require_GET
def robots_txt(request):
    lines = [
        "User-agent: *",
        "Disallow: /tasks/one_entry/create/",
        "Disallow: /tasks/notes/",
        "Disallow: /tasks/birthdays/",
        "Disallow: /profile/",
        "Disallow: /auth/",
        f"Sitemap: https://www.{settings.DOMAIN}/sitemap.xml",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")

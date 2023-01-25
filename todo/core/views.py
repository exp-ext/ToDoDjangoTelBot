from difflib import SequenceMatcher

from django.core.paginator import Paginator
from django.db.models.query import QuerySet
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render


def page_not_found(request: HttpRequest, exception) -> HttpResponse:
    return render(request, 'core/404.html', {'path': request.path}, status=404)


def server_error(request: HttpRequest) -> HttpResponse:
    return render(request, 'core/500.html', status=500)


def permission_denied(request: HttpRequest, exception) -> HttpResponse:
    return render(request, 'core/403.html', status=403)


def csrf_failure(request: HttpRequest, reason='') -> HttpResponse:
    return render(request, 'core/403csrf.html')


def paginator_handler(request: HttpRequest, query: QuerySet) -> Paginator:
    paginator = Paginator(query, 9)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)


def similarity(s1: str, s2: str) -> float:
    """
    Сравнение 2-х строк в модуле difflib
    [https://docs.python.org/3/library/difflib.html].
    """
    normalized = tuple((map(lambda x: x.lower(), [s1, s2])))
    matcher = SequenceMatcher(
        lambda x: x == " ",
        normalized[0],
        normalized[1]
    )
    return matcher.ratio()

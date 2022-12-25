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
    paginator = Paginator(query, 10)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)

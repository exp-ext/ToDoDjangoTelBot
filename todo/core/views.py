from difflib import SequenceMatcher

import markdown
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.db.models import Model
from django.db.models.query import QuerySet
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from telbot.loader import bot
from users.models import Group

User = get_user_model()


def page_not_found(request: HttpRequest, exception) -> HttpResponse:
    return render(request, 'core/404.html', {'path': request.path}, status=404)


def server_error(request: HttpRequest) -> HttpResponse:
    return render(request, 'core/500.html', status=500)


def permission_denied(request: HttpRequest, exception) -> HttpResponse:
    return render(request, 'core/403.html', status=403)


def csrf_failure(request: HttpRequest, reason='') -> HttpResponse:
    return render(request, 'core/403csrf.html')


def paginator_handler(request: HttpRequest,
                      query: QuerySet,
                      issuance: int = 12) -> Paginator:
    """
    Использует класс Django Paginator для создания объекта paginator,
    принимает:
    - request (:obj:`HttpRequest`) - запрос
    - query (:obj:`QuerySet`) - объект QuerySet
    - issuance (:obj:`int`) - необязательный аргумент, количество элементов
    в выдаче на странице. По умолчанию 12.

    Возвращает постраничный QuerySet, используя метод get_page объекта
    paginator.
    """
    paginator = Paginator(query, issuance)
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


def linkages_check(user: Model) -> None:
    """
    Сравнивает связи модели GroupConnections с группами Телеграмм,
    если в группе нет user(вышел или кикнули) то удаляет связь.
    """
    exit_status = ['kicked', 'left']
    entries = user.groups_connections.select_related('group')
    for entry in entries:
        try:
            result = bot.get_chat_member(
                entry.group.chat_id,
                user.tg_id
            )
            if result.status in exit_status:
                entry.delete()
        except Exception:
            continue


def get_status_in_group(group: QuerySet[Group], user_id: int) -> bool:
    """
    Возвращает статус юзера в группе и обновляет описание группы.
    """
    try:
        chat = bot.get_chat(group.chat_id)
        flag = False
        if group.description != chat.description:
            group.description = chat.description
            flag = True
        if group.link != chat.link:
            group.link = chat.link
            flag = True
        if flag:
            group.save()
        result = bot.get_chat_member(group.chat_id, user_id)
        return result.status
    except Exception:
        return 'error'


def convert_markdown(text: str) -> str:
    """
    Конвертирует теги Markdown в HTML-теги

    ### Args:
    - text (str): Входной текст для конвертации.

    ### Return:
    - (str): Текст с замененными тегами
    """

    return markdown.markdown(text, extensions=['fenced_code', 'extra', 'codehilite', 'toc'])

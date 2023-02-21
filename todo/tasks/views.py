import re
from datetime import datetime, timezone

from core.views import linkages_check, paginator_handler
from django.contrib.auth.decorators import login_required
from django.db import models
from django.db.models import F, Q
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render

from .forms import TaskForm
from .models import Task


@login_required
def tasks(request: HttpRequest) -> HttpResponse:
    """Отображает все заметки."""
    user = request.user
    user_timezone = user.locations.first().timezone
    groups = user.groups_connections.values('group_id')
    groups_id = tuple(x['group_id'] for x in groups)

    if request.resolver_match.view_name == 'tasks:notes':
        now = datetime.now(timezone.utc)
        note_list = (
            Task.objects
            .filter(Q(user=user) | Q(group_id__in=groups_id))
            .annotate(
                relevance=models.Case(
                    models.When(
                        server_datetime__gte=now,
                        then=1
                    ),
                    models.When(
                        server_datetime__lt=now,
                        then=2
                    ),
                    output_field=models.IntegerField(),
                )).annotate(
                timediff=models.Case(
                    models.When(
                        server_datetime__gte=now,
                        then=F('server_datetime')-now
                    ),
                    models.When(
                        server_datetime__lt=now,
                        then=now-F('server_datetime')
                    ),
                    output_field=models.DurationField(),
                )).exclude(
                    it_birthday=True
                ).order_by('relevance', 'timediff')
        )
    else:
        note_list = (
            Task.objects
            .filter(Q(user=user) | Q(group_id__in=groups_id))
            .exclude(it_birthday=False)
            .order_by('server_datetime__month', 'server_datetime__day')
        )

    page_obj = paginator_handler(request, note_list)

    context = {
        'page_obj': page_obj,
        'timezone': user_timezone,
    }
    template = 'tasks/notes.html'
    return render(request, template, context)


@login_required
def task_create(request: HttpRequest) -> HttpResponseRedirect | HttpResponse:
    """Создаёт новую запись."""

    linkages_check(request.user)

    tz = request.user.locations.first().timezone
    form = TaskForm(
        request.POST or None,
        files=request.FILES or None,
        initial={
            'tz': tz,
            'user': request.user,
            'is_edit': False,
        }
    )
    if request.method == "POST" and form.is_valid():
        text = form.cleaned_data.get('text')
        form = form.save(commit=False)
        form.user = request.user
        form.text = generating_correct_text(text)
        form.save()
        redirecting = 'tasks:birthdays' if form.it_birthday else 'tasks:notes'
        return redirect(redirecting)
    context = {
        'form': form,
    }
    template = 'tasks/create_task.html'
    return render(request, template, context)


@login_required
def task_edit(request: HttpRequest,
              task_id: int) -> HttpResponseRedirect | HttpResponse:
    """Изменяет запись о напоминании."""
    task = get_object_or_404(Task, pk=task_id)

    redirecting = 'tasks:birthdays' if task.it_birthday else 'tasks:notes'

    if task.user != request.user:
        return redirect(redirecting, task_id=task_id)

    linkages_check(request.user)

    tz = request.user.locations.first().timezone
    is_edit = True

    form = TaskForm(
        request.POST or None,
        files=request.FILES or None,
        instance=task,
        initial={
            'tz': tz,
            'user': request.user,
            'is_edit': is_edit,
        }
    )

    if request.method == "POST" and form.is_valid():
        text = form.cleaned_data.get('text')
        form = form.save(commit=False)
        form.text = generating_correct_text(text)
        form.save()
        return redirect(redirecting)

    context = {
        'form': form,
    }
    template = 'tasks/create_task.html'
    return render(request, template, context)


@login_required
def task_delete(request: HttpRequest,
                task_id: int) -> HttpResponseRedirect:
    """Удаляет напоминание."""
    task = get_object_or_404(Task, pk=task_id)

    redirecting = 'tasks:birthdays' if task.it_birthday else 'tasks:notes'

    if task.user == request.user:
        task.delete()
    return redirect(redirecting)


def generating_correct_text(text: str) -> str:
    """Возвращает текст с якорем в ссылках."""
    urls = re.findall(r'([^href=\"]https?://\S+)', text)
    for url in urls:
        text = text.replace(
            url,
            f' <a href="{url.strip()}">{url.split("//")[-1].split("/")[0]}</a>'
        )
    return text

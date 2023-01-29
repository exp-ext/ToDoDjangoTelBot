from core.views import linkages_check, paginator_handler
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render

from .forms import TaskForm
from .models import Task


@login_required
def tasks(request: HttpRequest) -> HttpResponse:
    """Отображает все заметки."""
    user = request.user
    timezone = user.locations.first().timezone

    it_birthday = False
    if request.resolver_match.view_name == 'tasks:notes':
        it_birthday = True

    note_list = user.tasks.exclude(it_birthday=it_birthday)
    page_obj = paginator_handler(request, note_list)

    context = {
        'page_obj': page_obj,
        'timezone': timezone,
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
        form = form.save(commit=False)
        form.user = request.user
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
        task = form.save()
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

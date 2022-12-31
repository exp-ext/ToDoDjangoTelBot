from core.views import paginator_handler
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ProfileForm, TaskForm
from .models import Task

User = get_user_model()


@login_required
def accounts_profile(request: HttpRequest, username: str) -> HttpResponse:
    """Профиль юзера."""
    user = get_object_or_404(User.objects, username=username)
    if user != request.user:
        redirect('index')

    form = ProfileForm(
        request.POST or None,
        files=request.FILES or None,
        instance=user
    )

    if request.method == "POST" and form.is_valid():
        user = form.save()
        return redirect('tasks:accounts_profile', username=username)

    context = {
        'user': user,
        'form': form,
    }
    template = 'tasks/accounts_profile.html'
    return render(request, template, context)


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
    form = TaskForm(
        request.POST or None,
        files=request.FILES or None
    )

    if request.method == "POST" and form.is_valid():
        form = form.save(commit=False)
        form.user = request.user
        form.save()
        redirecting = 'tasks:birthdays' if form.it_birthday else 'tasks:notes'
        return redirect(redirecting)

    tz = request.user.locations.first().timezone
    form.initial['tz'] = tz
    form.initial['group'] = request.user.groups_connections.all()
    context = {
        'form': form,
        'tz': tz,
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

    form = TaskForm(
        request.POST or None,
        files=request.FILES or None,
        instance=task
    )

    if request.method == "POST" and form.is_valid():
        task = form.save()
        return redirect(redirecting)

    is_edit = True
    tz = request.user.locations.first().timezone
    form.initial['tz'] = tz
    form.initial['group'] = request.user.groups_connections.all()
    context = {
        'form': form,
        'is_edit': is_edit,
        'tz': tz,
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

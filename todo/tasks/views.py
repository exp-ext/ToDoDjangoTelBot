import re
from datetime import datetime, timezone
from typing import Any, Dict

from core.views import linkages_check
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Case, DurationField, F, IntegerField, Q, When
from django.db.models.query import QuerySet
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView, View

from .forms import TaskForm
from .models import Task


class TasksListView(LoginRequiredMixin, ListView):
    template_name = 'tasks/notes.html'
    paginate_by = 12

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['timezone'] = self.request.user.locations.first().timezone
        return context

    def get_queryset(self) -> QuerySet(Task):
        user = self.request.user
        groups = user.groups_connections.values('group_id')
        groups_id = tuple(x['group_id'] for x in groups)

        if self.request.resolver_match.view_name == 'tasks:notes':
            now = datetime.now(timezone.utc)
            note_list = (
                Task.objects
                .filter(Q(user=user) | Q(group_id__in=groups_id))
                .annotate(
                    relevance=Case(
                        When(
                            server_datetime__gte=now,
                            then=1
                        ),
                        When(
                            server_datetime__lt=now,
                            then=2
                        ),
                        output_field=IntegerField(),
                    )
                ).annotate(
                    timediff=Case(
                        When(
                            server_datetime__gte=now,
                            then=F('server_datetime') - now
                        ),
                        When(
                            server_datetime__lt=now,
                            then=now - F('server_datetime')
                        ),
                        output_field=DurationField(),
                    )
                ).exclude(
                    it_birthday=True
                ).order_by('relevance', 'timediff')
                .select_related('user')
            )
        else:
            note_list = (
                Task.objects
                    .filter(Q(user=user) | Q(group_id__in=groups_id))
                    .exclude(it_birthday=False)
                    .order_by('server_datetime__month', 'server_datetime__day')
                    .select_related('user')
            )
        return note_list


class TaskCreateView(LoginRequiredMixin, CreateView):
    """
    Делает запись в БД и reverse на лист с записями.
    """
    model = Task
    form_class = TaskForm
    template_name = 'tasks/create_task.html'

    def __init__(self) -> None:
        super().__init__()
        self.it_birthday = False

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related('group')
        return queryset

    def get_initial(self) -> Dict[str, Any]:
        initial = super().get_initial()
        tz = self.request.user.locations.first().timezone
        initial['user'] = self.request.user
        initial['tz'] = tz
        initial['is_edit'] = False
        return initial

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpRequest:
        linkages_check(request.user)
        return super().get(request, *args, **kwargs)

    def form_valid(self, form: TaskForm) -> HttpResponse:
        text = form.cleaned_data.get('text')
        form = form.save(commit=False)
        form.user = self.request.user
        form.text = generating_correct_text(text)
        self.it_birthday = form.it_birthday
        return super().form_valid(form)

    def get_success_url(self) -> Dict[str, Any]:
        redirecting = (
            'tasks:birthdays' if self.it_birthday else 'tasks:notes'
        )
        return reverse_lazy(redirecting)


class TaskUpdateView(LoginRequiredMixin, UpdateView):
    """Изменяет запись в БД и делает redirect на лист с записями."""
    model = Task
    form_class = TaskForm
    template_name = 'tasks/create_task.html'
    pk_url_kwarg = 'task_id'

    def __init__(self) -> None:
        super().__init__()
        self.it_birthday = False

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related('group')
        return queryset

    def get_initial(self) -> Dict[str, Any]:
        initial = super().get_initial()
        tz = self.request.user.locations.first().timezone
        initial['user'] = self.request.user
        initial['tz'] = tz
        initial['is_edit'] = True
        return initial

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any
            ) -> HttpRequest:
        linkages_check(request.user)
        return super().get(request, *args, **kwargs)

    def form_valid(self, form: TaskForm) -> HttpResponseRedirect:
        text = form.cleaned_data.get('text')
        form = form.save(commit=False)
        form.text = generating_correct_text(text)
        self.it_birthday = form.it_birthday
        return super().form_valid(form)

    def get_success_url(self) -> Dict[str, Any]:
        redirecting = (
            'tasks:birthdays' if self.it_birthday else 'tasks:notes'
        )
        return reverse_lazy(redirecting)


class TaskDeleteView(LoginRequiredMixin, View):
    """Удаление записи."""
    def get(self, request: HttpRequest, task_id: int) -> HttpResponseRedirect:
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

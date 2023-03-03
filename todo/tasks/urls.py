from django.urls import include, path

from .views import (TaskCreateView, TaskDeleteView, TasksListView,
                    TaskUpdateView)

urlpatterns = [
    path('notes/', TasksListView.as_view(), name='notes'),
    path('birthdays/', TasksListView.as_view(), name='birthdays'),
    path('one_entry/', include([
        path('create/', TaskCreateView.as_view(), name='task_create'),
        path(
            '<int:task_id>/edit/',
            TaskUpdateView.as_view(),
            name='task_edit'
        ),
        path(
            '<int:task_id>/delete/',
            TaskDeleteView.as_view(),
            name='task_delete'
        ),
        ])
    ),
]

from django.urls import include, path

from .views import accounts_profile, task_create, task_delete, task_edit, tasks

urlpatterns = [
    path(
        'profile/<str:username>/', accounts_profile,
        name='accounts_profile'
    ),
    path('notes/', tasks, name='notes'),
    path('birthdays/', tasks, name='birthdays'),
    path('one_entry/', include([
        path('create/', task_create, name='task_create'),
        path('<int:task_id>/edit/', task_edit, name='task_edit'),
        path('<int:task_id>/delete/', task_delete, name='task_delete'),
        ])
    ),
]

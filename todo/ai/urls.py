from django.urls import path

from .views import AI

urlpatterns = [
    path('message/', AI.as_view(), name='get_answer'),
    path('last-message/', AI.as_view(), name='last_message'),
]

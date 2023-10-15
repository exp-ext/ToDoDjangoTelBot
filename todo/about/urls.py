from django.urls import path

from .views import about_view

urlpatterns = [
    path('contacts/', about_view, name='support'),
]

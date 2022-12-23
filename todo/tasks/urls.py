from django.urls import path

from .views import accounts_profile

urlpatterns = [
    path(
        'profile/<str:username>/', accounts_profile,
        name='accounts_profile'
    ),
]

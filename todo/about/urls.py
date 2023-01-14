from django.urls import path

from .views import AboutProjectView

urlpatterns = [
    path('contacts/', AboutProjectView.as_view(), name='project'),
]

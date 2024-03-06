from django.contrib.auth.views import LoginView, LogoutView
from django.urls import include, path

from .views import LoginTgButtonView, LoginTgLinkView, LoginTgView, block

urlpatterns = [
    path('logout/', LogoutView.as_view(template_name='users/logged_out.html'), name='logout'),
    path(
        'login/', include([
            path('', LoginView.as_view(template_name='users/login.html'), name='login'),
            path('tg/<int:user_id>/<str:key>/', LoginTgLinkView.as_view(), name='tg_link_login'),
            path('tg/callback/', LoginTgView.as_view(), name='tg_login'),
            path('tg/generate-td-auth-url/', LoginTgButtonView.as_view(), name='tg_button_login'),
            path('block/', block)
        ])
    ),
]

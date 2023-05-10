"""todo URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path
from users.views import accounts_profile

from . import views
from .sitemap import DynamicViewSitemap, StaticViewSitemap

SITEMAPS = {
    'static': StaticViewSitemap,
    'dynamic': DynamicViewSitemap
}

urlpatterns = [
    path('', views.index, name='index'),
    path('admin/', include([
        path('', admin.site.urls),
        path('defender/', include('defender.urls')),
    ])
    ),
    path('about/', include(('about.urls', 'about'), namespace='about')),
    path('auth/', include([
        path('', include(('users.urls', 'users'), namespace='users')),
        path('', include('django.contrib.auth.urls')),
    ])
    ),
    path('bot/', include(('telbot.urls', 'telbot'))),
    path('tasks/', include(('tasks.urls', 'tasks'), namespace='tasks')),
    path(
        'profile/<str:username>/',
        accounts_profile,
        name='accounts_profile'
    ),
    path('posts/', include(('posts.urls', 'posts'), namespace='posts')),
    path(
        'sitemap.xml', sitemap, {'sitemaps': SITEMAPS},
        name='django.contrib.sitemaps.views.sitemap'
    ),
    path('robots.txt', views.robots_txt),
    path(
        'ckeditor5/',
        include('django_ckeditor_5.urls'),
        name='ck_editor_5_upload_file'
    ),
]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns += [
        path('__debug__/', include(debug_toolbar.urls)),
    ]
    urlpatterns += static(
        settings.STATIC_URL, document_root=settings.STATIC_ROOT
    )
    urlpatterns += static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
    )


handler403 = 'core.views.permission_denied'
handler404 = 'core.views.page_not_found'
handler500 = 'core.views.server_error'

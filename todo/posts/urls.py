from django.urls import include, path

from .views import (add_comment, follow_index, group_posts, index_posts,
                    post_create, post_delete, post_detail, post_edit, profile,
                    profile_follow, profile_unfollow, search)

urlpatterns = [
    path('', index_posts, name='index_posts'),
    path('s', search, name='search'),
    path('group/<slug:slug>/', group_posts, name='group_list'),
    path('create/', post_create, name='post_create'),
    path('<int:post_id>/', include([
        path('comment/', add_comment, name='add_comment'),
        path('edit/', post_edit, name='post_edit'),
        path('delete/', post_delete, name='post_delete'),
        path('', post_detail, name='post_detail'),
        ])
    ),
    path('follow/', follow_index, name='follow_index'),
    path('profile/<str:username>/', include([
        path('follow/', profile_follow, name='profile_follow'),
        path('unfollow/', profile_unfollow, name='profile_unfollow'),
        path('', profile, name='profile'),
        ])
    ),
]

from django.urls import path

from .views import (add_comment, follow_index, group_posts, index_posts,
                    post_create, post_delete, post_detail, post_edit, profile,
                    profile_follow, profile_unfollow, search)

urlpatterns = [
    path('', index_posts, name='index_posts'),
    path('s', search, name='search'),
    path('group/<slug:slug>/', group_posts, name='group_list'),
    path('create/', post_create, name='post_create'),
    path(
        '<int:post_id>/comment/',
        add_comment,
        name='add_comment'
    ),
    path('<int:post_id>/edit/', post_edit, name='post_edit'),
    path('<int:post_id>/delete/', post_delete, name='post_delete'),
    path('<int:post_id>/', post_detail, name='post_detail'),
    path('follow/', follow_index, name='follow_index'),
    path(
        'profile/<str:username>/follow/',
        profile_follow,
        name='profile_follow'
    ),
    path(
        'profile/<str:username>/unfollow/',
        profile_unfollow,
        name='profile_unfollow'
    ),
    path('profile/<str:username>/', profile, name='profile'),
]

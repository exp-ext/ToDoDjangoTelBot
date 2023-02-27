from django.urls import include, path

from .views import (AddCommentView, FollowIndexView, GroupPostsView,
                    IndexPostsView, PostCreateView, PostDeleteView,
                    PostDetailView, PostUpdateView, ProfileFollowView,
                    ProfileUnfollowView, ProfileView, SearchView)

urlpatterns = [
    path('', IndexPostsView.as_view(), name='index_posts'),
    path('s', SearchView.as_view(), name='search'),
    path('group/<slug:slug>/', GroupPostsView.as_view(), name='group_list'),
    path('create/', PostCreateView.as_view(), name='post_create'),
    path('<int:post_id>/', include([
        path('comment/', AddCommentView.as_view(), name='add_comment'),
        path('edit/', PostUpdateView.as_view(), name='post_edit'),
        path('delete/', PostDeleteView.as_view(), name='post_delete'),
        path('', PostDetailView.as_view(), name='post_detail'),
        ])
    ),
    path('follow/', FollowIndexView.as_view(), name='follow_index'),
    path('profile/<str:username>/', include([
        path('follow/', ProfileFollowView.as_view(), name='profile_follow'),
        path(
            'unfollow/',
            ProfileUnfollowView.as_view(),
            name='profile_unfollow'
        ),
        path('', ProfileView.as_view(), name='profile'),
        ])
    ),
]

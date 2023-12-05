from django.urls import include, path, re_path

from .views import (AddCommentView, FollowIndexListView, GroupPostsListView,
                    IndexPostsListView, PostCreateView, PostDeleteView,
                    PostDetailView, PostUpdateView, ProfileDetailView,
                    ProfileFollowView, ProfileUnfollowView, SearchListView)

urlpatterns = [
    path('', IndexPostsListView.as_view(), name='index_posts'),
    path('term', SearchListView.as_view(), name='search'),
    path('s', SearchListView.as_view(), name='search'),
    path('group/<slug:slug>/', GroupPostsListView.as_view(), name='group_list'),
    path('create/', PostCreateView.as_view(), name='post_create'),
    path('follow/', FollowIndexListView.as_view(), name='follow_index'),
    re_path(r'^(?P<post_identifier_pk>[\d]+)/', include([
        path('comment/', AddCommentView.as_view(), name='add_comment'),
        path('edit/', PostUpdateView.as_view(), name='post_edit'),
        path('delete/', PostDeleteView.as_view(), name='post_delete'),
        path('', PostDetailView.as_view(), name='post_detail'),
    ])
    ),
    re_path(r'^(?P<post_identifier_slug>[\w-]+)/', include([
        path('comment/', AddCommentView.as_view(), name='add_comment'),
        path('edit/', PostUpdateView.as_view(), name='post_edit'),
        path('delete/', PostDeleteView.as_view(), name='post_delete'),
        path('', PostDetailView.as_view(), name='post_detail'),
    ])
    ),
    path('profile/<str:username>/', include([
        path('follow/', ProfileFollowView.as_view(), name='profile_follow'),
        path('unfollow/', ProfileUnfollowView.as_view(), name='profile_unfollow'),
        path('', ProfileDetailView.as_view(), name='profile'),
    ])
    ),
]

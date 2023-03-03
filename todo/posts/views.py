from typing import Any, Dict

from core.views import get_status_in_group, linkages_check, paginator_handler
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.db.models.query import QuerySet
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, ListView, UpdateView
from django.views.generic.detail import DetailView
from django.views.generic.edit import FormView
from users.models import Group, GroupMailing

from .forms import CommentForm, GroupMailingForm, PostForm
from .models import Follow, Post

User = get_user_model()

PAGINATE_BY = 10


class SearchListView(ListView):
    """
    Возвращает
    - (:obj:`Paginator`) с результатом поиска в постах;
    - (:obj:`str`) поисковое слово keyword.
    """
    template_name = 'posts/search_result.html'
    paginate_by = PAGINATE_BY

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['keyword'] = self.request.GET.get('q', '')
        return context

    def get_queryset(self) -> QuerySet(Post):
        keyword = self.request.GET.get('q', '')
        user = self.request.user

        if not keyword:
            return redirect('posts:index_posts')

        post_list = (
            Post.objects
            .select_related('author', 'group')
            .exclude(group__link=None)
            .filter(text__icontains=keyword)
            .order_by('group')
        )
        if user.is_authenticated:
            post_list |= Post.objects.filter(
                group__in=(
                    user
                    .groups_connections
                    .values_list('group', flat=True)
                ),
                text__icontains=keyword,
            )
        return post_list


class IndexPostsListView(ListView):
    """
    Возвращает :obj:`Paginator` с заметками для общей ленты.
    """
    template_name = 'posts/index_posts.html'
    paginate_by = PAGINATE_BY

    def get_queryset(self) -> QuerySet(Post):
        user = self.request.user
        post_list = (
            Post.objects
            .exclude(Q(group=True) & Q(group__link__isnull=True))
            .select_related('author', 'group')
        )
        if user.is_authenticated:
            post_list |= Post.objects.filter(
                group__in=(
                    user
                    .groups_connections
                    .values_list('group', flat=True)
                ),
            )
        return post_list


class GroupPostsListView(LoginRequiredMixin, ListView):
    """
    Возвращает:
    - (:obj:`Paginator`) с заметками группы по slug;
    - (:obj:`queryset`) Group;
    - (:obj:`boolean`) is_admin, для отображения формы с переключателями
    рассылок;
    - form(:obj:`GroupMailingForm`) с переключателями рассылок;
    - (:obj:`boolean`) forism_check, найдена ли запись в БД с рассылкой
    для группы
    """
    model = Post
    template_name = 'posts/group_list.html'
    paginate_by = PAGINATE_BY

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any
                 ) -> HttpResponse:
        self.group = get_object_or_404(Group, slug=self.kwargs['slug'])

        status = get_status_in_group(self.group, request.user.username)
        self.is_admin = False
        admin_status = ['creator', 'administrator']
        self.is_admin = status in admin_status
        if not self.is_admin and not self.group.link and status != 'member':
            return redirect('posts:index_posts')

        self.form = GroupMailingForm(request.POST or None)
        self.forism_check = self.group.group_mailing.filter(
            mailing_type='forismatic_quotes'
        ).exists()
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self) -> QuerySet(Post):
        return self.group.posts.select_related('author', 'group')

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context |= {
            'group': self.group,
            'is_admin': self.is_admin,
            'form': self.form,
            'forism_check': self.forism_check,
        }
        return context

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any
             ) -> HttpRequest:
        if self.form.is_valid():
            quotes = self.form.cleaned_data.get('forismatic_quotes')
            if quotes:
                GroupMailing.objects.get_or_create(
                    group=self.group,
                    mailing_type='forismatic_quotes'
                )
                self.forism_check = True
            else:
                self.group.group_mailing.filter(
                    mailing_type='forismatic_quotes'
                ).delete()
                self.forism_check = False
        return self.get(request, *args, **kwargs)


class ProfileDetailView(LoginRequiredMixin, DetailView):
    """
    Возвращает:
    - (:obj:`Paginator`) все посты одного пользователя по его имени(id);
    - (:obj:`int`) количество постов posts_count;
    - (:obj:`boolean`) состояние подписки на того автора для пользователя;
    """
    model = User
    template_name = 'posts/profile.html'
    context_object_name = 'author'

    def get_object(self, queryset: QuerySet = None) -> QuerySet(User):
        queryset = (
            super().get_queryset()
            .prefetch_related('group', 'posts__author', 'posts__group')
        )
        return queryset.get(username=self.kwargs['username'])

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        post_list = self.get_user_posts().select_related('author', 'group')
        page_obj = paginator_handler(self.request, post_list, PAGINATE_BY)
        context |= {
            'page_obj': page_obj,
            'posts_count': page_obj.paginator.count,
            'following': (
                self.request.user.follower.filter(author=self.object).exists()
            )
        }
        return context

    def get_user_posts(self) -> QuerySet(Post):
        groups = self.get_user_groups()
        return (
            self.object.posts
            .filter(
                Q(group=None)
                | Q(group__in=groups)
                | Q(group__link__isnull=False)
            )
            .select_related('author', 'group')
        )

    def get_user_groups(self) -> QuerySet(Group):
        if self.request.user.is_authenticated:
            groups = (
                self.request.user
                .groups_connections.values_list('group_id', flat=True)
            )
            return Group.objects.filter(id__in=groups)
        return Group.objects.none()


class PostCreateView(LoginRequiredMixin, CreateView):
    """
    Делает запись в БД и reverse в профиль автора.
    """
    model = Post
    form_class = PostForm
    template_name = 'posts/create_post.html'

    def get_initial(self) -> Dict[str, Any]:
        initial = super().get_initial()
        initial['user'] = self.request.user
        initial['is_edit'] = False
        return initial

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpRequest:
        linkages_check(request.user)
        return super().get(request, *args, **kwargs)

    def form_valid(self, form: PostForm) -> HttpResponse:
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self) -> Dict[str, Any]:
        return reverse_lazy(
            'posts:profile',
            kwargs={'username': self.request.user.username}
        )


class PostUpdateView(LoginRequiredMixin, UpdateView):
    """Изменяет запись в БД и делает redirect к представлению этого поста."""
    model = Post
    form_class = PostForm
    template_name = 'posts/create_post.html'
    pk_url_kwarg = 'post_id'

    def get_initial(self) -> Dict[str, Any]:
        initial = super().get_initial()
        initial['user'] = self.request.user
        initial['is_edit'] = True
        return initial

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any
            ) -> HttpRequest:
        linkages_check(request.user)
        post = self.get_object()
        if post.author != request.user:
            return redirect('posts:post_detail', post_id=post.pk)
        return super().get(request, *args, **kwargs)

    def form_valid(self, form: PostForm) -> HttpResponseRedirect:
        post = form.save()
        return redirect('posts:post_detail', post_id=post.pk)


class PostDetailView(DetailView):
    """
    Возвращает:
    - (:obj:`QuerySet`) поста по его post_id;
    - (:obj:`int`) количество постов автора authors_posts_count;
    - (:obj:`CommentForm`) форму для добавления комментария.
    """
    model = Post
    template_name = 'posts/post_detail.html'
    context_object_name = 'post'
    pk_url_kwarg = 'post_id'

    def get_queryset(self) -> QuerySet(Post):
        return super().get_queryset().select_related('author')

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        post = self.get_object()
        context['authors_posts_count'] = post.author.posts.count()
        context['comments'] = post.comments.all()
        context['form'] = CommentForm(self.request.POST or None)
        return context


class AddCommentView(LoginRequiredMixin, FormView):
    """
    Создаёт комментарий к посту по его post_id и
    перенаправляет  обратно к посту.
    """
    form_class = CommentForm
    template_name = 'posts/post_detail.html'

    def form_valid(self, form: CommentForm) -> HttpResponseRedirect:
        post = get_object_or_404(Post, pk=self.kwargs['post_id'])
        comment = form.save(commit=False)
        comment.author = self.request.user
        comment.post = post
        comment.save()
        return redirect('posts:post_detail', post_id=post.pk)

    def form_invalid(self, form: CommentForm) -> HttpResponseRedirect:
        post = get_object_or_404(Post, pk=self.kwargs['post_id'])
        return render(
            self.request,
            self.template_name, {
                'post': post,
                'form': form,
            }
        )


class FollowIndexListView(LoginRequiredMixin, ListView):
    """
    Возвращает :obj:`Paginator` с заметками авторов на которых
    подписан авторизованный пользователь в запросе.
    """
    template_name = 'posts/follow.html'
    paginate_by = PAGINATE_BY

    def get_queryset(self) -> QuerySet(Post):
        user = self.request.user
        post_list = (
            Post.objects
            .filter(author__following__user=user)
            .exclude(Q(group=True) & Q(group__link__isnull=True))
            .select_related('author', 'group')
        )
        if user.is_authenticated:
            post_list |= Post.objects.filter(
                author__following__user=user,
                group__in=(
                    user
                    .groups_connections
                    .values_list('group', flat=True)
                ),
            )
        return post_list


class ProfileFollowView(LoginRequiredMixin, View):
    """Подписка на пользователя в его профиле."""
    def get(self, request: HttpRequest, username: str) -> HttpResponseRedirect:
        author = get_object_or_404(User, username=username)
        if author != request.user:
            Follow.objects.get_or_create(user=request.user, author=author)
        return redirect('posts:profile', username=username)


class ProfileUnfollowView(LoginRequiredMixin, View):
    """Отписка от пользователя в его профиле."""
    def get(self, request: HttpRequest, username: str) -> HttpResponseRedirect:
        author = get_object_or_404(User, username=username)
        Follow.objects.filter(user=request.user, author=author).delete()
        return redirect('posts:profile', username=username)


class PostDeleteView(LoginRequiredMixin, View):
    """Удаление поста."""
    def get(self, request: HttpRequest, post_id: int) -> HttpResponseRedirect:
        post = get_object_or_404(Post, pk=post_id)
        if post.author == request.user:
            post.delete()
        return redirect('posts:profile', post.author.username)

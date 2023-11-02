import json
import re
from typing import Any, Dict

from advertising.models import PartnerBanner
from core.views import get_status_in_group, linkages_check, paginator_handler
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q
from django.db.models.query import QuerySet
from django.http import (HttpRequest, HttpResponse, HttpResponseRedirect,
                         JsonResponse)
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, ListView, UpdateView
from django.views.generic.detail import DetailView
from django.views.generic.edit import FormView
from django_user_agents.utils import get_user_agent
from users.models import Group, GroupMailing

from .forms import CommentForm, GroupMailingForm, PostForm
from .models import Follow, Post

User = get_user_model()
redis_client = settings.REDIS_CLIENT
PAGINATE_BY = 10


class SearchListView(ListView):
    """
    Возвращает
    - (:obj:`Paginator`) с результатом поиска в постах;
    - (:obj:`str`) поисковое слово keyword.
    """
    template_name = 'posts/search_result.html'
    paginate_by = PAGINATE_BY

    def get(self, request, *args, **kwargs):
        self.keyword = request.GET.get('q', '')
        term = request.GET.get('term', '')
        if not self.keyword and not term:
            return redirect('posts:index_posts')
        if term and ' ' in term:
            return self.term_queryset_answer(term)
        if term:
            return self.term_answer(term)
        return super().get(request, *args, **kwargs)

    def term_answer(self, term):
        """Автодополнение."""
        self.keyword = term
        qs = self.get_queryset()
        qs = qs.filter(text__icontains=self.keyword).values_list('text', flat=True)
        matching_words = set()
        for item in qs:
            words = re.findall(r'\b\w+\b', item)
            for word in words:
                if self.keyword in word and word:
                    matching_words.add(word)
        return JsonResponse(list(matching_words)[:7], safe=False)

    def term_queryset_answer(self, term):
        """Возврат фильтрованного о поиску queryset."""
        self.keyword = term
        queryset = self.get_queryset()
        queryset = queryset.annotate(match_count=Count('text'))
        queryset = queryset.order_by('-match_count')
        results = []

        for item in queryset[:3]:
            results.append({
                'label': item.title,
                'link': f'https://www.{settings.DOMAIN}/posts/{item.id}/',
                'image': item.image.url,
            })
        return JsonResponse(results, safe=False)

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['keyword'] = self.keyword
        return context

    def get_queryset(self) -> QuerySet(Post):
        user = self.request.user
        post_list = (
            Post.objects
            .select_related('author', 'group')
            .filter(Q(group__isnull=True) | Q(group__link__isnull=False), text__icontains=self.keyword)
            .order_by('group')
        )
        if user.is_authenticated:
            post_list |= Post.objects.filter(
                group__in=(
                    user
                    .groups_connections
                    .values_list('group', flat=True)
                ),
                text__icontains=self.keyword,
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
        post_list = Post.objects.filter(Q(group__isnull=True) | Q(group__link__isnull=False))
        if user.is_authenticated:
            post_list |= Post.objects.filter(
                group__in=(
                    user
                    .groups_connections
                    .values_list('group', flat=True)
                ),
            )
        return post_list


class GroupPostsListView(ListView):
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
        if not self.group.link:
            return redirect('posts:index_posts')
        status = (
            'is_anonymous' if request.user.is_anonymous or not request.user.tg_id
            else get_status_in_group(self.group, request.user.tg_id)
        )
        self.is_admin = False
        admin_status = ['creator', 'administrator']
        self.is_admin = status in admin_status
        self.form = GroupMailingForm(request.POST or None)
        self.forism_check = self.group.group_mailing.filter(
            mailing_type='forismatic_quotes'
        ).exists()
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self) -> QuerySet(Post):
        return self.group.posts.select_related('author', 'group')

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        user_agent = get_user_agent(self.request)
        context |= {
            'group': self.group,
            'is_admin': self.is_admin,
            'form': self.form,
            'forism_check': self.forism_check,
            'is_mobile': user_agent.is_mobile,
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


class ProfileDetailView(DetailView):
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
            .prefetch_related('posts__author', 'posts__group')
        )
        return queryset.get(username=self.kwargs['username'])

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        post_list = self.get_user_posts().select_related('author', 'group')
        page_obj = paginator_handler(self.request, post_list, PAGINATE_BY)
        user_agent = get_user_agent(self.request)
        user = self.request.user
        context |= {
            'page_obj': page_obj,
            'posts_count': page_obj.paginator.count,
            'following': False if user.is_anonymous else user.follower.filter(author=self.object).exists(),
            'is_mobile': user_agent.is_mobile,
        }
        return context

    def get_user_posts(self) -> QuerySet(Post):
        groups = self.get_user_groups()
        return (
            self.object.posts
            .filter(Q(group=None) | Q(group__in=groups) | Q(group__link__isnull=False))
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

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpRequest:
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
        user_agent = get_user_agent(self.request)
        ip = self.get_client_ip()
        all_banners = PartnerBanner.objects.all()
        random_banner = all_banners.order_by('?').first()

        redis_key_post_ips = f'ips_post_{post.id}'
        redis_key_post_counter = f'counter_post_{post.id}'
        redis_key_agent_posts = 'list_agent_posts'

        try:
            check_ip = redis_client.sismember(redis_key_post_ips, ip)
        except Exception:
            check_ip = False
            ip = '127.0.0.1'

        if not check_ip:
            if redis_client.get(redis_key_post_counter):
                counter = redis_client.incr(redis_key_post_counter)
            else:
                counter = post.view_count.count()
                redis_client.set(redis_key_post_counter, counter)

            agent_data = {
                'post_id': post.id,
                'browser': user_agent.browser.family,
                'os': user_agent.os.family,
                'is_bot': user_agent.is_bot,
                'is_mobile': user_agent.is_mobile,
                'is_pc': user_agent.is_pc,
                'is_tablet': user_agent.is_tablet,
                'is_touch_capable': user_agent.is_touch_capable,
            }
            serialized_agent_data = json.dumps(agent_data)

            redis_client.sadd(redis_key_post_ips, ip)
            redis_client.lpush(redis_key_agent_posts, json.dumps(serialized_agent_data))
        else:
            counter = redis_client.get(redis_key_post_counter).decode('utf-8')

        context |= {
            'authors_posts_count': post.author.posts.count(),
            'comments': post.comments.all(),
            'form': CommentForm(self.request.POST or None),
            'is_mobile': user_agent.is_mobile,
            'advertising': random_banner if random_banner else False,
            'counter': counter,
        }
        return context

    def get_client_ip(self):
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        return ip


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
    def post(self, request: HttpRequest, username: str) -> HttpResponseRedirect:
        author = get_object_or_404(User, username=username)
        if author != request.user:
            Follow.objects.get_or_create(user=request.user, author=author)
        return redirect('posts:profile', username=username)


class ProfileUnfollowView(LoginRequiredMixin, View):
    """Отписка от пользователя в его профиле."""
    def post(self, request: HttpRequest, username: str) -> HttpResponseRedirect:
        author = get_object_or_404(User, username=username)
        Follow.objects.filter(user=request.user, author=author).delete()
        return redirect('posts:profile', username=username)


class PostDeleteView(LoginRequiredMixin, View):
    """Удаление поста."""
    def post(self, request: HttpRequest, post_id: int) -> HttpResponseRedirect:
        post = get_object_or_404(Post, pk=post_id)
        if post.author == request.user:
            post.delete()
        return redirect('posts:profile', post.author.username)

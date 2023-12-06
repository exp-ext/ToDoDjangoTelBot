import json
import re
from collections import Counter
from typing import Any, Dict

from advertising.models import AdvertisementWidget, PartnerBanner
from core.views import get_status_in_group, linkages_check, paginator_handler
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Case, Count, IntegerField, Q, When
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
from telbot.service_message import send_message_to_chat
from users.models import Group, GroupMailing

from .forms import CommentForm, GroupMailingForm, PostForm
from .models import Follow, Post, PostContents

User = get_user_model()
redis_client = settings.REDIS_CLIENT
PAGINATE_BY = 10
ADMIN_ID = settings.TELEGRAM_ADMIN_ID


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
        if term:
            return self.term_answer(term)
        return super().get(request, *args, **kwargs)

    def term_answer(self, term: str) -> JsonResponse:
        """Автодополнение в поиске."""
        self.keyword = term.lower()
        queryset = self.get_queryset()
        queryset = (
            queryset.filter(text__icontains=self.keyword, moderation='PS')
            .annotate(
                title_match=Case(
                    When(title__icontains=self.keyword, then=1),
                    default=0,
                    output_field=IntegerField()
                ),
                text_match_count=Count('text')
            ).order_by('-title_match', '-text_match_count')
        )
        qs = queryset.values_list('text', flat=True)
        word_counts = Counter()

        for item in qs[:5]:
            words = re.findall(r'\b\w+\b', item.lower())
            for word in words:
                if self.keyword in word:
                    word_counts[word] += 1

        results = sorted(word_counts, key=lambda x: (-word_counts[x], len(x)))[:5]

        for item in queryset[:3]:
            results.append({
                'label': item.title,
                'link': f'https://www.{settings.DOMAIN}/posts/{item.slug}/',
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
            .filter(Q(group__isnull=True) | Q(group__link__isnull=False), text__icontains=self.keyword, moderation='PS')
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
        post_list = (
            Post.objects
            .filter(Q(group__isnull=True) | Q(group__link__isnull=False), moderation='PS')
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

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        user_agent = get_user_agent(self.request)
        context |= {
            'is_mobile': user_agent.is_mobile,
        }
        return context


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
        return self.group.posts.select_related('author', 'group').filter(moderation='PS')

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

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpRequest:
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
        moderation = ('PS', 'WT') if self.request.user == self.object else ('PS',)
        return (
            self.object.posts
            .filter(Q(group=None) | Q(group__in=groups) | Q(group__link__isnull=False), moderation__in=moderation)
            .select_related('author', 'group')
        )

    def get_user_groups(self) -> QuerySet(Group):
        if self.request.user.is_authenticated:
            groups = self.request.user.groups_connections.values_list('group_id', flat=True)
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
        message = f'Создан новый пост с темой "{self.object.title}"'
        send_message_to_chat.delay(ADMIN_ID, message)
        return reverse_lazy('posts:profile', kwargs={'username': self.request.user.username})


class PostUpdateView(LoginRequiredMixin, UpdateView):
    """Изменяет запись в БД и делает redirect к представлению этого поста."""
    model = Post
    form_class = PostForm
    template_name = 'posts/create_post.html'
    pk_url_kwarg = 'post_identifier_pk'

    def get_initial(self) -> Dict[str, Any]:
        initial = super().get_initial()
        initial['user'] = self.request.user
        initial['is_edit'] = True
        return initial

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpRequest:
        linkages_check(request.user)
        post = self.get_object()
        if post.author != request.user:
            return redirect('posts:post_detail', post_identifier_slug=post.slug)
        return super().get(request, *args, **kwargs)

    def form_valid(self, form: PostForm) -> HttpResponseRedirect:
        post = form.save()
        return redirect('posts:post_detail', post_identifier_slug=post.slug)


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
    pk_url_kwarg = 'post_identifier_pk'
    slug_url_kwarg = 'post_identifier_slug'

    def get(self, request, *args, **kwargs):

        if 'post_identifier_pk' in self.kwargs:
            post_pk = int(self.kwargs.get('post_identifier_pk'))
            posts_data = redis_client.get('posts')
            post_slug = None

            def get_slug_by_pk(id_slug_pair):
                return next((item['slug'] for item in id_slug_pair if item['id'] == post_pk), None)

            if posts_data:
                id_slug_pair = posts_data.decode('utf-8')
                data_list = json.loads(id_slug_pair)
                post_slug = get_slug_by_pk(data_list)

            if not posts_data or not post_slug:
                id_slug_pair = list(Post.objects.values('id', 'slug'))
                redis_client.set('posts', json.dumps(id_slug_pair))
                post_slug = get_slug_by_pk(id_slug_pair)

            return redirect('posts:post_detail', post_identifier_slug=post_slug)

        return super().get(request, *args, **kwargs)

    def get_queryset(self) -> QuerySet(Post):
        queryset = super().get_queryset().select_related('author')
        user = self.request.user
        if user.is_anonymous:
            return queryset.filter(moderation='PS')
        return queryset.filter(Q(moderation='PS') | Q(author=user))

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        post = kwargs.get('object')

        user_agent = get_user_agent(self.request)
        ip = self.get_client_ip()

        random_banner = PartnerBanner.objects.order_by('?').first()
        random_widget = AdvertisementWidget.objects.order_by('?').first()

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

        root_contents = post.contents.filter(depth=1).first()

        contents = PostContents.dump_bulk(root_contents) if root_contents else None

        context |= {
            'authors_posts_count': post.author.posts.count(),
            'comments': post.comments.all(),
            'form': CommentForm(self.request.POST or None),
            'is_mobile': user_agent.is_mobile,
            'advertising': random_banner if random_banner else False,
            'advertisement_widget': random_widget if random_widget else False,
            'counter': counter,
            'contents': contents[0].get('children', None) if contents else None,
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
    Создаёт комментарий к посту по его post_identifier_pk и
    перенаправляет  обратно к посту.
    """
    form_class = CommentForm
    template_name = 'posts/post_detail.html'

    def form_valid(self, form: CommentForm) -> HttpResponseRedirect:
        post = get_object_or_404(Post, pk=self.kwargs['post_identifier_pk'])
        comment = form.save(commit=False)
        comment.author = self.request.user
        comment.post = post
        comment.save()
        message = (
            f'Написан новый комментарий к Вашей заметке [{post.title}](https://www.{settings.DOMAIN}/posts/{post.slug}/):\n\n'
            f'_{comment.text.replace("_", " ")}_\n'
        )
        send_message_to_chat.delay(post.author.tg_id, message, parse_mode_markdown=True)
        return redirect('posts:post_detail', post_identifier_slug=post.slug)

    def form_invalid(self, form: CommentForm) -> HttpResponseRedirect:
        post = get_object_or_404(Post, pk=self.kwargs['post_identifier_pk'])
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
            .filter(author__following__user=user, moderation='PS')
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

    def post(self, request: HttpRequest, post_identifier_pk: int) -> HttpResponseRedirect:
        post = get_object_or_404(Post, pk=post_identifier_pk)
        if post.author == request.user:
            post.delete()
        return redirect('posts:profile', post.author.username)

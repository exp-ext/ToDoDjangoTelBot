import json
import re
from collections import Counter
from typing import Any, Dict
from urllib.parse import quote

from advertising.models import AdvertisementWidget, PartnerBanner
from core.views import get_status_in_group, linkages_check, paginator_handler
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Case, Count, IntegerField, Q, Value, When
from django.db.models.query import QuerySet
from django.http import (HttpRequest, HttpResponse,
                         HttpResponsePermanentRedirect, HttpResponseRedirect,
                         JsonResponse)
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import CreateView, ListView, UpdateView
from django.views.generic.detail import DetailView
from django.views.generic.edit import FormView
from django_user_agents.utils import get_user_agent
from sorl.thumbnail import get_thumbnail
from telbot.service_message import send_message_to_chat
from users.models import Group, GroupConnections, GroupMailing

from .forms import CommentForm, GroupMailingForm, PostForm
from .models import Follow, Post, PostContents, PostTags

User = get_user_model()
redis_client = settings.REDIS_CLIENT
PAGINATE_BY = 10
ADMIN_ID = settings.TELEGRAM_ADMIN_ID

KEY_PRIVATE_GROUPS = 'private_groups'
KEY_POSTS = 'posts'


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
        user_agent = get_user_agent(self.request)
        context |= {
            'is_mobile': user_agent.is_mobile,
            'keyword': self.keyword,
        }
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
        tag = self.request.GET.get('q', '')
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
        if tag and tag != 'vse':
            post_list = post_list.filter(tags__slug=tag)
        return post_list

    def get_pagination_querystring(self):
        query_params = self.request.GET.copy()
        query_params.pop('page', None)
        return query_params.urlencode()

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        user_agent = get_user_agent(self.request)
        custom_order = Case(When(slug='vse', then=Value(0)), default=Value(1), output_field=IntegerField())
        queryset = PostTags.objects.annotate(custom_sort=custom_order).order_by('custom_sort')
        data = [
            {
                'title': item.title,
                'description': item.description,
                'slug': item.slug,
                'image': item.image.url if item.image else None,
            }
            for item in queryset
        ]
        json_data = json.dumps(data, cls=DjangoJSONEncoder)
        context |= {
            'is_mobile': user_agent.is_mobile,
            'tags': json_data,
            'media_bucket': settings.MEDIA_URL,
            'pagination_querystring': self.get_pagination_querystring(),
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

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
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
        self.forism_check = self.group.group_mailing.filter(mailing_type='forismatic_quotes').exists()
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
                self.group.group_mailing.filter(mailing_type='forismatic_quotes').delete()
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


class AutosaveView(View):

    def post(self, data) -> JsonResponse:
        """Обработка POST-запроса с данными поста и их автосохранение.

        ## Args:
            data (`HttpRequest`): Объект запроса с данными поста и информацией о пользователе.

        ## Returns:
            `JsonResponse`: JSON-ответ с информацией о статусе автосохранения данных.
        """
        post_data = data.POST
        user = data.user
        save_data = {
            'title': post_data.get('title'),
            'group': post_data.get('group'),
            'text': post_data.get('text'),
        }
        serialized_data = json.dumps(save_data)
        redis_client.setex(f'user_{user.id}_post_autosave', 3600, serialized_data)
        return JsonResponse({'status': 'Data autosaved'})


class PostCreateView(LoginRequiredMixin, CreateView):
    """
    Делает запись в БД и reverse в профиль автора.
    """
    model = Post
    form_class = PostForm
    template_name = 'posts/create_post.html'
    initial_post_data = {}

    def get_initial(self) -> Dict[str, Any]:
        initial = super().get_initial()
        initial['user'] = self.request.user
        initial['is_edit'] = False
        initial.update(self.initial_post_data)
        return initial

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpRequest:
        user = request.user
        linkages_check(user)
        data = redis_client.get(f'user_{user.id}_post_autosave')
        if data:
            self.initial_post_data = json.loads(data.decode('utf-8'))
        return super().get(request, *args, **kwargs)

    def form_valid(self, form: PostForm) -> HttpResponse:
        form.instance.author = self.request.user
        self.object = form.save()
        group = self.object.group
        if group and not group.link:
            redis_client.sadd(KEY_PRIVATE_GROUPS, group.id)
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self) -> Dict[str, Any]:
        message = f'Создан новый пост с темой "{self.object.title}"'
        if self.object.author.tg_id != 'test_id':
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
        group = post.group
        if group and not group.link:
            redis_client.sadd(KEY_PRIVATE_GROUPS, group.id)
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
    tag_queryset = None

    def get_post_slug_from_redis(self, post_pk: int) -> str or None:
        """Получает слаг поста по его идентификатору из Redis.

        ### Parameters:
        - post_pk (`int`): Идентификатор поста.

        ### Returns:
        - str or None: Слаг поста или None, если пост не найден.
        """
        posts_data = redis_client.get(KEY_POSTS)
        if posts_data:
            data_list = json.loads(posts_data.decode('utf-8'))
            return self.get_slug_by_pk(data_list, post_pk)
        return None

    def get_slug_by_pk(self, id_slug_pair: list, post_pk: int) -> str or None:
        """Получает слаг из пары идентификатора и слага поста.

        ### Parameters:
        - id_slug_pair (`list`): Список словарей, представляющих пары идентификатора и слага поста.
        - post_pk (`int`): Идентификатор поста.

        ### Returns:
        - str or None: Слаг поста или None, если пост не найден.
        """
        return next((item['slug'] for item in id_slug_pair if item['id'] == post_pk), None)

    def handle_group_access(self, group: Group):
        """Загружает приватные группы в Редис, если их там нет, и делает проверку на отношение юзера к группе.

        ### Parameters:
        - group (`Group`): Объект группы.

        ### Returns:
        - None or HttpResponseRedirect: Если группа приватная и пользователь анонимный, то он перенаправляется.
        """
        if not group.link:
            if self.request.user.is_anonymous:
                return redirect('posts:index_posts')

            group_id = group.id
            if not redis_client.exists(KEY_PRIVATE_GROUPS):
                private_groups = Group.objects.filter(link__isnull=True).values_list('id', flat=True)
                redis_client.sadd(KEY_PRIVATE_GROUPS, *private_groups)

            if redis_client.sismember(KEY_PRIVATE_GROUPS, group_id):
                if not GroupConnections.objects.filter(user=self.request.user, group__id=group_id).exists():
                    return redirect('posts:index_posts')
        return None

    def get(self, request, *args, **kwargs):
        post_pk = int(self.kwargs.get('post_identifier_pk')) if 'post_identifier_pk' in self.kwargs else None
        if post_pk:
            post_slug = self.get_post_slug_from_redis(post_pk)

            if not post_slug:
                id_slug_pair = list(Post.objects.values('id', 'slug'))
                redis_client.set(KEY_POSTS, json.dumps(id_slug_pair))
                post_slug = self.get_slug_by_pk(id_slug_pair, post_pk)

            if post_slug:
                return HttpResponsePermanentRedirect(reverse('posts:post_detail', args=(post_slug,)))
            return redirect('posts:index_posts')

        self.object = self.get_object()

        if self.object.group:
            redirect_response = self.handle_group_access(self.object.group)
            if redirect_response:
                return redirect_response

        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)

    def get_queryset(self) -> QuerySet(Post):
        queryset = super().get_queryset().select_related('author', 'group').prefetch_related('tags')
        user = self.request.user
        if user.is_anonymous:
            queryset = queryset.filter(moderation='PS')
        else:
            queryset = queryset.filter(Q(moderation='PS') | Q(author=user))
        self.tag_queryset = queryset
        return queryset

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        post = kwargs.get('object')

        user_agent = get_user_agent(self.request)
        ip = self.get_client_ip()
        ref_url = self.get_ref_url()

        random_banner = PartnerBanner.objects.order_by('?').first()
        random_widget = AdvertisementWidget.objects.order_by('?').first()

        redis_key_post_ips = f'ips_post_{post.id}'
        redis_key_post_counter = f'counter_post_{post.id}'
        redis_key_agent_posts = 'list_agent_posts'

        try:
            check_ip = redis_client.sismember(redis_key_post_ips, ip)
        except Exception:
            check_ip = False
            ip = ip or '127.0.0.1'

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
                'ip': ip,
                'ref_url': ref_url
            }
            serialized_agent_data = json.dumps(agent_data)

            redis_client.sadd(redis_key_post_ips, ip)
            redis_client.lpush(redis_key_agent_posts, serialized_agent_data)
        else:
            counter = redis_client.get(redis_key_post_counter).decode('utf-8')

        root_contents = post.contents.filter(depth=1).first()

        contents = PostContents.dump_bulk(root_contents) if root_contents else None

        tags, tag_posts_chunked = self.get_tags_and_posts()

        context |= {
            'authors_posts_count': post.author.posts.count(),
            'comments': post.comments.all(),
            'form': CommentForm(self.request.POST or None),
            'is_mobile': user_agent.is_mobile,
            'advertising': random_banner if random_banner else False,
            'advertisement_widget': random_widget if random_widget else False,
            'counter': counter,
            'contents': contents[0].get('children', None) if contents else None,
            'tags': tags,
            'tag_posts_chunked': tag_posts_chunked
        }
        return context

    def get_tags_and_posts(self):
        tags = self.object.tags.values_list('title', flat=True)
        posts = self.tag_queryset.filter(tags__title__in=tags)
        posts_processed = []

        for post in posts:
            thumbnail = get_thumbnail(post.image, '960x339', crop='center', upscale=True)
            posts_processed.append({
                'image_url': thumbnail.url,
                'slug': post.slug,
                'short_description': post.short_description
            })
        return ', '.join(tags), self.chunker(posts_processed, 3)

    @staticmethod
    def chunker(seq, size):
        return (seq[pos:pos + size] for pos in range(0, len(seq), size))

    def get_client_ip(self):
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        return x_forwarded_for.split(',')[0] if x_forwarded_for else self.request.META.get('REMOTE_ADDR')

    def get_ref_url(self):
        return quote(self.request.META.get('HTTP_REFERER', '')) if self.request.META.get('HTTP_REFERER') else None


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
        if post.author.tg_id != 'test_id':
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

import json
import re
from collections import Counter
from typing import Any, Dict
from urllib.parse import quote

from advertising.models import MyBanner, PartnerBanner
from bs4 import BeautifulSoup
from core.re_compile import WORD_PATTERN
from core.views import get_status_in_group, linkages_check, paginator_handler
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import (Case, Count, IntegerField, Prefetch, Q, Value,
                              When)
from django.db.models.query import QuerySet
from django.http import (Http404, HttpRequest, HttpResponse,
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
from telegram import ParseMode
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
    model = Post
    template_name = 'desktop/posts/search_result.html'
    paginate_by = PAGINATE_BY

    def get_template_names(self):
        user_agent = get_user_agent(self.request)
        if user_agent.is_mobile:
            return ['mobile/posts/search_result.html']
        return [self.template_name]

    def get(self, request, *args, **kwargs):
        self.keyword = request.GET.get('q', '')
        self.term = request.GET.get('term', '')
        if not self.keyword and not self.term:
            return redirect('posts:index_posts')
        if self.term:
            return self.term_answer()
        return super().get(request, *args, **kwargs)

    def term_answer(self) -> JsonResponse:
        """Автодополнение в поиске."""
        self.keyword = self.term.lower()
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
            words = WORD_PATTERN.findall(item.lower())
            for word in words:
                if self.keyword in word:
                    word_counts[word] += 1

        results = sorted(word_counts, key=lambda x: (-word_counts[x], len(x)))[:5]

        for item in queryset[:3]:
            results.append({
                'label': item.title,
                'link': f'https://{settings.DOMAINPREFIX}.{settings.DOMAIN}/posts/{item.slug}/',
                'image': item.image.url,
            })
        return JsonResponse(results, safe=False)

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update({'keyword': self.keyword})
        return context

    def get_queryset(self) -> QuerySet[Post]:
        queryset = super().get_queryset().select_related('author', 'group')
        user = self.request.user
        post_list = (
            queryset
            .select_related('author', 'group')
            .filter(Q(group__isnull=True) | Q(group__link__isnull=False), text__icontains=self.keyword, moderation='PS')
            .order_by('group')
        )
        if user.is_authenticated:
            user_groups = user.groups_connections.values_list('group', flat=True)
            post_list = queryset.filter(
                Q(group__in=user_groups, moderation__in=('PS', 'WT'))
                | Q(author=user, moderation__in=('PS', 'WT'))
                | Q(group__isnull=True, moderation='PS')
                | Q(group__link__isnull=False, moderation='PS'),
                text__icontains=self.keyword
            )
        if not self.term:
            for post in post_list:
                post.filter_text = self.annotate_paragraphs(post)
        return post_list

    def annotate_paragraphs(self, post):
        soup = BeautifulSoup(post.text, 'html.parser')
        paragraphs = soup.find_all('p')
        search_word = self.keyword.lower()
        first_text = None
        max_length = 253

        for item in paragraphs:
            search_text = item.get_text()
            if first_text is None:
                first_text = search_text
            if re.search(re.escape(search_word), search_text.lower()):
                return search_text if len(search_text) < max_length else search_text[:max_length] + '...'
        return first_text if len(first_text) < max_length else first_text[:max_length] + '...'


class IndexPostsListView(ListView):
    """
    Возвращает :obj:`Paginator` с заметками для общей ленты.
    """
    model = Post
    template_name = 'desktop/posts/index_posts.html'
    paginate_by = PAGINATE_BY

    def get_template_names(self):
        user_agent = get_user_agent(self.request)
        if user_agent.is_mobile:
            return ['mobile/posts/index_posts.html']
        return [self.template_name]

    def get_queryset(self) -> QuerySet:
        queryset = super().get_queryset().select_related('author', 'group')
        tag = self.request.GET.get('q', '')
        user = self.request.user
        post_list = (
            queryset
            .filter(Q(group__isnull=True) | Q(group__link__isnull=False), moderation='PS')
            .select_related('author', 'group')
        )
        if user.is_authenticated:
            user_groups = user.groups_connections.values_list('group', flat=True)
            post_list = queryset.filter(
                Q(group__in=user_groups, moderation__in=('PS', 'WT'))
                | Q(author=user, moderation__in=('PS', 'WT'))
                | Q(group__isnull=True, moderation='PS')
                | Q(group__link__isnull=False, moderation='PS')
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
        context.update({
            'tags': json_data,
            'media_bucket': settings.MEDIA_URL,
            'pagination_querystring': self.get_pagination_querystring(),
        })
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
    template_name = 'desktop/posts/group_list.html'
    paginate_by = PAGINATE_BY

    def get_template_names(self):
        user_agent = get_user_agent(self.request)
        if user_agent.is_mobile:
            return ['mobile/posts/group_list.html']
        return [self.template_name]

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        self.group = get_object_or_404(Group, slug=self.kwargs['slug'])
        status = (
            'is_anonymous' if request.user.is_anonymous or not request.user.tg_id
            else get_status_in_group(self.group, request.user.tg_id)
        )
        if not self.group.link and (status == 'is_anonymous' or not self.group.groups_connections.filter(user=request.user).exists()):
            return redirect('posts:index_posts')
        self.is_admin = False
        admin_status = ['creator', 'administrator']
        self.is_admin = status in admin_status
        self.form = GroupMailingForm(request.POST or None)
        self.forism_check = self.group.group_mailing.filter(mailing_type='forismatic_quotes').exists()
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self) -> QuerySet:
        user = self.request.user
        post_list = (
            self.group.posts
            .filter(Q(group__isnull=True) | Q(group__link__isnull=False), moderation='PS')
            .select_related('author', 'group')
        )
        if user.is_authenticated:
            user_groups = user.groups_connections.values_list('group', flat=True)
            post_list = self.group.posts.filter(
                Q(group__in=user_groups, moderation__in=('PS', 'WT'))
                | Q(author=user, moderation__in=('PS', 'WT'))
                | Q(group__isnull=True, moderation='PS')
                | Q(group__link__isnull=False, moderation='PS')
            )
        return post_list

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update({
            'group': self.group,
            'is_admin': self.is_admin,
            'form': self.form,
            'forism_check': self.forism_check,
            'group_public': not self.group or bool(self.group.link),
        })
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
    template_name = 'desktop/posts/profile.html'
    context_object_name = 'author'

    def get_template_names(self):
        user_agent = get_user_agent(self.request)
        if user_agent.is_mobile:
            return ['mobile/posts/profile.html']
        return [self.template_name]

    def get_object(self, queryset=None):
        queryset = User.objects.prefetch_related(
            Prefetch('posts', queryset=Post.objects.select_related('author', 'group').filter(Q(group__isnull=True) | Q(group__link__isnull=False), moderation='PS'))
        )
        return queryset.get(username=self.kwargs['username'])

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        user = self.request.user
        if not hasattr(self.object, '_prefetched_objects_cache'):
            self.object._prefetched_objects_cache = {}

        post_list = self.get_user_posts(user)
        page_obj = paginator_handler(self.request, post_list, PAGINATE_BY)
        context.update({
            'page_obj': page_obj,
            'posts_count': page_obj.paginator.count,
            'following': False if user.is_anonymous else user.follower.filter(author=self.object).exists(),
        })
        return context

    def get_user_posts(self, user):
        if user.is_authenticated:
            user_groups = user.groups_connections.values_list('group', flat=True)
            return self.object.posts.filter(
                Q(group__in=user_groups, moderation__in=('PS', 'WT'))
                | Q(author=user, moderation__in=('PS', 'WT'))
                | Q(group__isnull=True, moderation='PS')
                | Q(group__link__isnull=False, moderation='PS')
            ).distinct()
        return self.object.posts.filter(Q(group__isnull=True) | Q(group__link__isnull=False), moderation='PS').distinct()


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
    template_name = 'desktop/posts/create_post.html'
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
        publication_type = self.request.POST.get('publication_type')
        if self.object.author.tg_id != 'test_id' and publication_type == 'public':
            message = f'Новый пост для модерации с темой "{self.object.title}"'
            send_message_to_chat.delay(ADMIN_ID, message)
        return reverse_lazy('posts:profile', kwargs={'username': self.request.user.username})


class PostUpdateView(LoginRequiredMixin, UpdateView):
    """Изменяет запись в БД и делает redirect к представлению этого поста."""
    model = Post
    form_class = PostForm
    template_name = 'desktop/posts/create_post.html'
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
        publication_type = self.request.POST.get('publication_type')
        if self.object.author.tg_id != 'test_id' and publication_type == 'public':
            message = f'Новый пост для модерации с темой "{self.object.title}"'
            send_message_to_chat.delay(ADMIN_ID, message)
        return redirect('posts:post_detail', post_identifier_slug=post.slug)


class PostDetailView(DetailView):
    """
    Возвращает:
    - (:obj:`QuerySet`) поста по его post_id;
    - (:obj:`int`) количество постов автора authors_posts_count;
    - (:obj:`CommentForm`) форму для добавления комментария.
    """
    model = Post
    template_name = 'desktop/posts/post_detail.html'
    context_object_name = 'post'
    pk_url_kwarg = 'post_identifier_pk'
    slug_url_kwarg = 'post_identifier_slug'
    tag_queryset = None

    def get_template_names(self):
        if self.user_agent.is_mobile:
            return ['mobile/posts/post_detail.html']
        return [self.template_name]

    def get_post_slug_from_redis(self, post_pk: int) -> str | bool:
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

    def get_slug_by_pk(self, id_slug_pair: list, post_pk: int) -> str:
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
                return self.error_checking()

            group_id = group.id
            if not redis_client.exists(KEY_PRIVATE_GROUPS):
                private_groups = Group.objects.filter(link__isnull=True).values_list('id', flat=True)
                redis_client.sadd(KEY_PRIVATE_GROUPS, *private_groups)

            if redis_client.sismember(KEY_PRIVATE_GROUPS, group_id):
                if not GroupConnections.objects.filter(user=self.request.user, group__id=group_id).exists():
                    return self.error_checking()
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
        try:
            self.object = self.get_object()
        except Http404:
            return self.error_checking()

        if self.object.group:
            redirect_response = self.handle_group_access(self.object.group)
            if redirect_response:
                return redirect_response

        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)

    def error_checking(self) -> HttpResponse | Http404:
        """Возвращает ссылку на 403 шаблон или 404, если поста не существует."""
        get_object_or_404(Post, slug=self.kwargs.get(self.slug_url_kwarg))
        full_url = self.request.build_absolute_uri()
        return render(self.request, 'core/403.html', {'full_url': full_url}, status=403)

    def get_queryset(self) -> QuerySet:
        queryset = super().get_queryset().select_related('author', 'group').prefetch_related('tags')
        user = self.request.user
        if user.is_anonymous:
            queryset = queryset.filter(moderation='PS')
        else:
            user_groups = user.groups_connections.values_list('group', flat=True)
            queryset = queryset.filter(
                Q(group__in=user_groups, moderation__in=('PS', 'WT'))
                | Q(author=user, moderation__in=('PS', 'WT'))
                | Q(group__isnull=True, moderation='PS')
                | Q(group__link__isnull=False, moderation='PS')
            )
        self.tag_queryset = queryset
        return queryset

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        post = kwargs.get('object')

        self.user_agent = get_user_agent(self.request)
        ip = self.get_client_ip()
        ref_url = self.get_ref_url()

        random_banner = None
        if not self.user_agent.is_mobile:
            random_banner = PartnerBanner.objects.order_by('?').first()

        my_banner = MyBanner.objects.order_by('?').first()

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
                'browser': self.user_agent.browser.family,
                'os': self.user_agent.os.family,
                'is_bot': self.user_agent.is_bot,
                'is_mobile': self.user_agent.is_mobile,
                'is_pc': self.user_agent.is_pc,
                'is_tablet': self.user_agent.is_tablet,
                'is_touch_capable': self.user_agent.is_touch_capable,
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

        tags, tag_posts_present, tag_posts_chunked = self.get_tags_and_posts()

        context.update({
            'authors_posts_count': post.author.posts.count(),
            'comments': post.comments.all(),
            'form': CommentForm(self.request.POST or None),
            'advertising': random_banner or False,
            'counter': counter,
            'contents': contents[0].get('children', None) if contents else None,
            'tags': tags,
            'tag_posts_present': tag_posts_present,
            'tag_posts_chunked': tag_posts_chunked,
            'my_banner': my_banner,
            'group_public': not post.group or bool(post.group.link),
            'is_mobile': self.user_agent.is_mobile,
        })
        return context

    def get_tags_and_posts(self):
        """Получает теги и соответствующие им посты.

        ### Returns:
        `tuple`: Кортеж, содержащий строку с перечисленными тегами и генератор словарей постов по этим тегам.

        """
        user = self.request.user
        tags = self.object.tags.values_list('title', flat=True)

        query = self.tag_queryset.filter(
            Q(group__isnull=True) | Q(group__link__isnull=False),
            tags__title__in=tags
        ).distinct().exclude(id=self.object.id)

        if user.is_authenticated:
            user_groups = user.groups_connections.values_list('group', flat=True)
            query = self.tag_queryset.filter(
                Q(group__isnull=True) | Q(group__link__isnull=False) | Q(group__in=user_groups),
                tags__title__in=tags
            ).distinct().exclude(id=self.object.id)

        posts_processed = []
        for post in query:
            thumbnail = get_thumbnail(post.image, '960x339', crop='center', upscale=True)
            posts_processed.append({
                'image_url': thumbnail.url,
                'slug': post.slug,
                'short_description': post.short_description
            })
        line_size = 1 if self.user_agent.is_mobile else 3
        return ', '.join(tags), query.count() > 0, self.chunker(posts_processed, line_size)

    @staticmethod
    def chunker(seq, size):
        """Разбивает последовательность на части заданного размера.

        ### Args:
        - seq (`iterable`): Итерируемая последовательность.
        - size (`int`): Размер частей.

        ### Returns:
        - `generator`: Генератор частей последовательности.

        ### Example:
        ```python
        # Разбиение списка на части по 3 элемента
        data = [1, 2, 3, 4, 5, 6, 7, 8, 9]
        chunks = list(self.chunker(data, 3))
        # chunks = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
        ```
        """
        return (seq[pos:pos + size] for pos in range(0, len(seq), size))

    def get_client_ip(self):
        """Получает IP-адрес клиента.

        ### Returns:
        - `str`: IP-адрес клиента.

        """
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        return x_forwarded_for.split(',')[0] if x_forwarded_for else self.request.META.get('REMOTE_ADDR')

    def get_ref_url(self):
        """Получает URL-ссылку клиента.

        ### Returns:
        - `str` or `None`: URL-ссылка клиента или None, если отсутствует.

        """
        return quote(self.request.META.get('HTTP_REFERER', '')) if self.request.META.get('HTTP_REFERER') else None


class AddCommentView(LoginRequiredMixin, FormView):
    """
    Создаёт комментарий к посту по его post_identifier_pk и
    перенаправляет  обратно к посту.
    """
    form_class = CommentForm
    template_name = 'desktop/posts/post_detail.html'

    def form_valid(self, form: CommentForm) -> HttpResponseRedirect:
        post = get_object_or_404(Post, pk=self.kwargs['post_identifier_pk'])
        comment = form.save(commit=False)
        comment.author = self.request.user
        comment.post = post
        comment.save()
        message = (
            f'Написан новый комментарий к Вашей заметке [{post.title}](https://{settings.DOMAINPREFIX}.{settings.DOMAIN}/posts/{post.slug}/):\n\n'
            f'_{comment.text.replace("_", " ")}_\n'
        )
        if post.author.tg_id != 'test_id':
            send_message_to_chat.delay(post.author.tg_id, message, parse_mode=ParseMode.MARKDOWN)
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
    template_name = 'desktop/posts/follow.html'
    paginate_by = PAGINATE_BY

    def get_queryset(self) -> QuerySet:
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

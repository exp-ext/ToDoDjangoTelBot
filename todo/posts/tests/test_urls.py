from django.contrib.auth import get_user_model
from django.test import Client as DjangoClient
from django.test import TestCase
from users.models import Group, GroupConnections

from ..models import Post

User = get_user_model()


class NamedClient(DjangoClient):
    def __init__(self, name='', **kwargs):
        super().__init__(**kwargs)
        self.name = name


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создание пользователей
        cls.author = User.objects.create_user(
            tg_id=8523123321,
            username='author_posts_urls',
            password='1234GLKLl5',
        )
        cls.somebody = User.objects.create_user(
            tg_id=1254553321,
            username='user_posts_urls',
            password='54321',
        )
        cls.somebody_in_public_group = User.objects.create_user(
            tg_id=1254553385,
            username='group_user_posts_urls',
            password='5432112',
        )
        cls.somebody_in_private_group = User.objects.create_user(
            tg_id=1254553399,
            username='private_user_posts_urls',
            password='543856112',
        )
        # Создание групп
        cls.group_private = Group.objects.create(
            chat_id=5567451332131,
            title='Тестовая private группа',
            slug='slug-private',
            description='Тестовое описание private',
        )
        cls.group_public = Group.objects.create(
            chat_id=5567452692132,
            title='Тестовая public группа',
            slug='slug-public',
            description='Тестовое описание public',
            link='slug-link'
        )
        # Создание постов
        cls.post_group_private_ps = Post.objects.create(
            id=1,
            title='private group PS',
            author=cls.author,
            text='Тестовый пост 1' * 3,
            moderation='PS',
            group=cls.group_private
        )
        cls.post_group_private_wt = Post.objects.create(
            id=2,
            title='private group WT',
            author=cls.author,
            text='Тестовый пост 2' * 3,
            moderation='WT',
            group=cls.group_private
        )
        cls.post_public_group_ps = Post.objects.create(
            id=3,
            title='public group PS',
            author=cls.author,
            text='Тестовый пост 3' * 3,
            moderation='PS',
            group=cls.group_public
        )
        cls.post_public_group_wt = Post.objects.create(
            id=4,
            title='public group WT',
            author=cls.author,
            text='Тестовый пост 4' * 3,
            moderation='WT',
            group=cls.group_public
        )
        cls.post_without_group_ps = Post.objects.create(
            id=5,
            title='without group PS',
            author=cls.author,
            text='Тестовый пост 5' * 3,
            moderation='PS',
            group=None
        )
        cls.post_without_group_wt = Post.objects.create(
            id=6,
            title='without group WT',
            author=cls.author,
            text='Тестовый пост 6' * 3,
            moderation='WT',
            group=None
        )
        # Подключение пользователя к группам
        GroupConnections.objects.create(
            user=cls.author,
            group=cls.group_private
        )
        GroupConnections.objects.create(
            user=cls.author,
            group=cls.group_public
        )
        GroupConnections.objects.create(
            user=cls.somebody_in_public_group,
            group=cls.group_public
        )
        GroupConnections.objects.create(
            user=cls.somebody_in_private_group,
            group=cls.group_private
        )
        # Определение URL
        cls.index = '/posts/'
        cls.group_list_private = f'/posts/group/{cls.group_private.slug}/'
        cls.group_list_public = f'/posts/group/{cls.group_public.slug}/'
        cls.post_detail_group_private_ps = f'/posts/{cls.post_group_private_ps.slug}/'
        cls.post_detail_group_private_wt = f'/posts/{cls.post_group_private_wt.slug}/'
        cls.post_detail_public_group_ps = f'/posts/{cls.post_public_group_ps.slug}/'
        cls.post_detail_public_group_wt = f'/posts/{cls.post_public_group_wt.slug}/'
        cls.post_detail_without_group_ps = f'/posts/{cls.post_without_group_ps.slug}/'
        cls.post_detail_without_group_wt = f'/posts/{cls.post_without_group_wt.slug}/'
        cls.post_create = '/posts/create/'
        cls.profile = f'/posts/profile/{cls.author.username}/'
        cls.post_edit = f'/posts/{cls.post_group_private_ps.id}/edit/'

    def setUp(self):
        self.guest_client = NamedClient(name='Guest')
        self.authorized_author = NamedClient(name='Author')
        self.authorized_author.force_login(self.author)
        self.authorized_somebody = NamedClient(name='Authorized Somebody')
        self.authorized_somebody.force_login(self.somebody)
        self.authorized_somebody_in_public_group = NamedClient(name='Authorized somebody in public group')
        self.authorized_somebody_in_public_group.force_login(self.somebody_in_public_group)
        self.authorized_somebody_in_private_group = NamedClient(name='Authorized somebody in private group')
        self.authorized_somebody_in_private_group.force_login(self.somebody_in_private_group)

    def test_pages_codes_by_url(self):
        """Доступность URL в приложении posts."""
        code_ok = 200
        code_found = 302
        code_not_found = 404
        code_forbidden = 403
        url_names = [
            [self.authorized_somebody_in_public_group, self.post_detail_without_group_wt, code_forbidden],
            [self.guest_client, self.index, code_ok],

            [self.authorized_author, self.profile, code_ok],
            [self.guest_client, self.profile, code_ok],

            # проверка доступности постов групп
            [self.guest_client, self.group_list_private, code_found],
            [self.guest_client, self.group_list_public, code_ok],

            # проверка доступности постов для неавторизованного пользователя
            [self.guest_client, self.post_detail_group_private_ps, code_forbidden],
            [self.guest_client, self.post_detail_group_private_wt, code_forbidden],

            [self.guest_client, self.post_detail_public_group_ps, code_ok],
            [self.guest_client, self.post_detail_public_group_wt, code_forbidden],

            [self.guest_client, self.post_detail_without_group_ps, code_ok],
            [self.guest_client, self.post_detail_without_group_wt, code_forbidden],

            # проверка доступности постов для авторизованного пользователя не участника группы
            [self.authorized_somebody, self.post_detail_group_private_ps, code_forbidden],
            [self.authorized_somebody, self.post_detail_group_private_wt, code_forbidden],

            [self.authorized_somebody, self.post_detail_public_group_ps, code_ok],
            [self.authorized_somebody, self.post_detail_public_group_wt, code_forbidden],

            [self.authorized_somebody, self.post_detail_without_group_ps, code_ok],
            [self.authorized_somebody, self.post_detail_without_group_wt, code_forbidden],

            # проверка доступности постов для автора
            [self.authorized_author, self.post_detail_group_private_ps, code_ok],
            [self.authorized_author, self.post_detail_group_private_wt, code_ok],

            [self.authorized_author, self.post_detail_public_group_ps, code_ok],
            [self.authorized_author, self.post_detail_public_group_wt, code_ok],

            [self.authorized_author, self.post_detail_without_group_ps, code_ok],
            [self.authorized_author, self.post_detail_without_group_wt, code_ok],

            # проверка доступности постов для участника публичной группы
            [self.authorized_somebody_in_public_group, self.post_detail_group_private_ps, code_forbidden],
            [self.authorized_somebody_in_public_group, self.post_detail_group_private_wt, code_forbidden],

            [self.authorized_somebody_in_public_group, self.post_detail_public_group_ps, code_ok],
            [self.authorized_somebody_in_public_group, self.post_detail_public_group_wt, code_ok],

            [self.authorized_somebody_in_public_group, self.post_detail_without_group_ps, code_ok],
            [self.authorized_somebody_in_public_group, self.post_detail_without_group_wt, code_forbidden],

            # проверка доступности постов для участника приватной группы
            [self.authorized_somebody_in_private_group, self.post_detail_group_private_ps, code_ok],
            [self.authorized_somebody_in_private_group, self.post_detail_group_private_wt, code_ok],

            [self.authorized_somebody_in_private_group, self.post_detail_public_group_ps, code_ok],
            [self.authorized_somebody_in_private_group, self.post_detail_public_group_wt, code_forbidden],

            [self.authorized_somebody_in_private_group, self.post_detail_without_group_ps, code_ok],
            [self.authorized_somebody_in_private_group, self.post_detail_without_group_wt, code_forbidden],

            # остальные проверки
            [self.guest_client, '/unexisting_page/', code_not_found],
            [self.authorized_somebody, self.post_edit, code_found],
            [self.authorized_author, self.post_edit, code_ok],

            [self.guest_client, self.post_create, code_found],
            [self.guest_client, self.post_edit, code_found],

            [self.authorized_somebody, self.post_create, code_ok],
        ]
        for client, address, code in url_names:
            with self.subTest(address=address):
                response = client.get(address)
                self.assertEqual(response.status_code, code, f'client {client.name}, address {address}')

    def test_urls_correct_template(self):
        """URL-адрес использует соответствующий шаблон в приложении posts."""
        templates_url_names = {
            self.index: 'desktop/posts/index_posts.html',
            self.profile: 'desktop/posts/profile.html',
            self.post_detail_group_private_ps: 'desktop/posts/post_detail.html',
            self.post_create: 'desktop/posts/create_post.html',
            self.post_edit: 'desktop/posts/create_post.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_author.get(address)
                self.assertTemplateUsed(response, template)

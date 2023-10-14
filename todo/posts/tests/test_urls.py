from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from users.models import Group, GroupConnections

from ..models import Post

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(
            username='author_posts_urls',
            password='1234GLKLl5',
        )
        cls.somebody = User.objects.create_user(
            username='user_posts_urls',
            password='54321',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост' * 3
        )
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание'
        )
        GroupConnections.objects.create(
            user=cls.user,
            group=cls.group
        )
        cls.index = '/posts/'
        cls.group_list = f'/posts/group/{cls.group.slug}/'
        cls.profile = f'/posts/profile/{cls.user.username}/'
        cls.post_detail = f'/posts/{cls.post.id}/'
        cls.post_edit = f'/posts/{cls.post.id}/edit/'
        cls.post_create = '/posts/create/'

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_somebody = Client()
        self.authorized_somebody.force_login(self.somebody)

    def test_pages_codes_by_url(self):
        """Доступность URL в приложении posts."""
        code_ok = 200
        code_found = 302
        code_not_found = 404
        url_names = [
            [self.guest_client, self.index, code_ok],
            [self.guest_client, self.post_create, code_found],
            [self.guest_client, self.post_edit, code_found],
            [self.guest_client, self.group_list, code_found],
            [self.authorized_client, self.profile, code_ok],
            [self.guest_client, self.profile, code_ok],
            [self.guest_client, self.post_detail, code_ok],
            [self.guest_client, '/unexisting_page/', code_not_found]
        ]
        for client, address, code in url_names:
            with self.subTest(address=address):
                response = client.get(address)
                self.assertEqual(response.status_code, code)

    def test_urls_correct_template(self):
        """URL-адрес использует соответствующий шаблон в приложении posts."""

        templates_url_names = {
            self.index: 'posts/index_posts.html',
            self.profile: 'posts/profile.html',
            self.post_detail: 'posts/post_detail.html',
            self.post_edit: 'posts/create_post.html',
            self.post_create: 'posts/create_post.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

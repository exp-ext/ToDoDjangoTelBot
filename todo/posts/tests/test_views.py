import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.paginator import Paginator
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.models import Follow, Post
from users.models import Group, GroupConnections

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
SMALL_GIF = (
    b'\x47\x49\x46\x38\x39\x61\x02\x00'
    b'\x01\x00\x80\x00\x00\x00\x00\x00'
    b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
    b'\x00\x00\x00\x2C\x00\x00\x00\x00'
    b'\x02\x00\x01\x00\x00\x02\x02\x0C'
    b'\x0A\x00\x3B'
)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_author = User.objects.create_user(
            username='author_posts_views',
            password='1234GLKLl5',
        )
        cls.user_action = User.objects.create_user(
            username='action_author_posts_views',
            password='123TKLDKlk45',
        )
        cls.group = Group.objects.create(
            chat_id='-453213215613',
            title='Тестовая группа',
            slug='test-slug-views',
            description='Тестовое описание'
        )
        cls.group_not_hit = Group.objects.create(
            chat_id='-84165156265465',
            title='Тестовая группа для 12-ого поста',
            slug='test-slug-views-not-hit',
            description='Тестовое описание той самой группы'
        )
        connections = [
            {
                'user': cls.user_author,
                'group': cls.group,
            },
            {
                'user': cls.user_author,
                'group': cls.group_not_hit,
            },
            {
                'user': cls.user_action,
                'group': cls.group,
            },
            {
                'user': cls.user_action,
                'group': cls.group_not_hit,
            },
        ]
        for item in connections:
            GroupConnections.objects.create(**item)

        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=SMALL_GIF,
            content_type='image/gif'
        )
        for count in range(13):
            cls.post = Post.objects.create(
                author=cls.user_author,
                text=f'Тестовый пост с группой, №{count}',
                group=cls.group if count < 12 else cls.group_not_hit,
                image=uploaded
            )
        cls.index = reverse('posts:index_posts')

        cls.profile = reverse(
            'posts:profile',
            kwargs={'username': cls.post.author}
        )
        cls.post_detail = reverse(
            'posts:post_detail',
            kwargs={'post_id': cls.post.id}
        )
        cls.post_edit = reverse(
            'posts:post_edit',
            kwargs={'post_id': cls.post.id}
        )
        cls.post_create = reverse('posts:post_create')
        cls.profile_follow = reverse(
            'posts:profile_follow',
            kwargs={'username': cls.post.author}
        )
        cls.profile_unfollow = reverse(
            'posts:profile_unfollow',
            kwargs={'username': cls.post.author}
        )
        cls.follow_index = reverse('posts:follow_index')

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user_author)

        self.followers_authorized_client = Client()
        self.followers_authorized_client.force_login(self.user_action)

    def test_urls_correct_template_by_namespace(self):
        """Namespace:name использует соответствующий шаблон."""
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

    def test_index_profile_show_correct_context(self):
        """Шаблон index, profile сформирован с правильным контекстом."""
        names = [
            self.index,
            self.profile,
        ]
        for name in names:
            with self.subTest(name=name):
                response = self.authorized_client.get(name)
                objects = response.context['page_obj']
                last_object = objects[0]
                self.assertEqual(
                    last_object.author, self.post.author
                )
                self.assertEqual(
                    last_object.group, self.post.group
                )
                self.assertEqual(
                    last_object.image, self.post.image
                )
                self.assertEqual(len(objects), 10)
                self.assertIsInstance(objects.paginator, Paginator)

                if name == self.index:
                    penultimate_object = objects[1]
                    self.assertEqual(penultimate_object.text,
                                     'Тестовый пост с группой, №11')

                elif name == self.profile:
                    username = response.context['author']
                    self.assertEqual(
                        username.username, self.user_author.username
                    )
                    posts_count = response.context['posts_count']
                    self.assertEqual(posts_count, 13)

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        names = [
            self.post_detail
        ]
        for name in names:
            with self.subTest(name=name):
                response = self.authorized_client.get(name)
                post = response.context['post']
                self.assertEqual(post.text,
                                 'Тестовый пост с группой, №12')
                authors_posts_count = response.context['authors_posts_count']
                self.assertEqual(authors_posts_count, 13)
                self.assertEqual(post.image, self.post.image)

    def test_post_create_edit_show_correct_context(self):
        """Шаблон post _create & _edit сформирован с правильным контекстом."""
        names = [
            self.post_create,
            self.post_edit
        ]
        for name in names:
            with self.subTest(name=name):
                response = self.authorized_client.get(name)
                form_fields = {
                    'text': forms.fields.CharField,
                    'group': forms.fields.ChoiceField,
                }
                for value, expected in form_fields.items():
                    with self.subTest(value=value):
                        form_field = (
                            response.context.get('form').fields.get(value)
                        )
                        self.assertIsInstance(form_field, expected)

    def test_follow_unfollow(self):
        """Авторизованный пользователь может подписаться/отписаться
        на авторов."""
        # подписка на самого себя
        follow_count = Follow.objects.count()
        self.authorized_client.get(self.profile_follow)

        self.assertEqual(
            Follow.objects.count(),
            follow_count,
            'кол-во записей не равно, подписка на самого себя возможна'
        )
        # подписка на автора
        self.followers_authorized_client.get(self.profile_follow)
        self.assertTrue(
            Follow.objects.filter(
                user=self.user_action,
                author=self.user_author
            ).exists,
            f'В БД не найдена подписка юзера {self.user_action} '
            f'на автора {self.user_author}'
        )
        # отписка от автора
        self.followers_authorized_client.get(self.profile_unfollow)
        self.assertEquals(
            Follow.objects.filter(
                user=self.user_action,
                author=self.user_author
            ).count(),
            0,
            f'В БД найдена подписка юзера {self.user_action} '
            f'на {self.user_author}, а её там не должно быть!'
        )

    def test_post_in_feed(self):
        """Тест появления поста у подписанных и неподписанных пользователей."""
        self.followers_authorized_client.get(self.profile_follow)
        # при подписке пост отображаются в index
        text = 'Новая запись пользователя появляется в ленте'
        Post.objects.create(
            author=self.user_author,
            text=text
        )
        response = self.followers_authorized_client.get(self.follow_index)
        followed_context = response.context['page_obj'].object_list
        self.assertEqual(
            followed_context[0].text, text,
            'не найден проверочный текст в последнем посте автора'
        )
        # после отписки, из follow_index приходит 0 постов
        self.followers_authorized_client.get(self.profile_unfollow)
        response = self.followers_authorized_client.get(self.follow_index)
        object = response.context['page_obj'].object_list
        self.assertEqual(object.count(), 0)

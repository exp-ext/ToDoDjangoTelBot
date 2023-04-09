from django.contrib.auth import get_user_model
from django.test import TestCase
from posts.models import Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(
            username='auth_posts_models',
            password='1234GLKLl5',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            title='title777',
            text='Тестовый пост 777. ' * 3
        )

    def test_posts_have_correct_object_names(self):
        """Проверяем, что у модели корректно работает __str__."""
        post = self.post
        str_text = post.title[:20]
        self.assertEqual(
            str_text,
            str(post),
            f'У модели Post результат __str__ = "{str_text}" '
            f'не соответствует ожидаемому "{str(post)}"'
        )

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

User = get_user_model()


class UsersViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(
            username='user_users_views',
            password="12345l*kjh/ljk%&$",
        )
        cls.password_change_form = reverse('users:password_change_form')
        cls.logout = reverse('users:logout')
        # cls.login = reverse('users:login')
        cls.password_reset_done = reverse('users:password_reset_done')
        cls.password_reset_form = reverse('users:password_reset_form')
        cls.password_reset_complete = reverse(
            'users:password_reset_complete'
        )

    def setUp(self):
        self.guest_client = Client()

        self.authorized_client = Client()
        self.authorized_client.force_login(UsersViewsTests.user)

    def test_urls_uses_correct_template(self):
        """Namespace:name использует соответствующий шаблон
        в приложении users."""
        templates_url_names = {
            UsersViewsTests.password_change_form:
            'users/password_change_form.html',
            UsersViewsTests.logout:
            'users/logged_out.html',
            # UsersViewsTests.login:
            # 'users/login.html',
            UsersViewsTests.password_reset_done:
            'users/password_reset_done.html',
            UsersViewsTests.password_reset_form:
            'users/password_reset_form.html',
            UsersViewsTests.password_reset_complete:
            'users/password_reset_complete.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

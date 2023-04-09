from django.contrib.auth import get_user_model
from django.test import Client, TestCase

User = get_user_model()


class UsersURLTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(
            username='user_users_urls',
            password="12345",
        )

    def setUp(self):
        self.guest_client = Client()

        self.authorized_client = Client()
        self.authorized_client.force_login(UsersURLTests.user)

    def test_pages_codes(self):
        """Доступность URL в приложении users."""
        code_ok = 200
        code_found = 302
        code_not_found = 404
        url_names = [
            [self.authorized_client, '/auth/password_change/', code_ok],
            [self.guest_client, '/auth/password_change/', code_found],
            [self.guest_client, '/auth/logout/', code_ok],
            # [self.guest_client, '/auth/login/', code_ok],
            [self.guest_client, '/auth/password_reset/done/', code_ok],
            [self.guest_client, '/auth/password_reset/', code_ok],
            [self.guest_client, '/auth/reset/done/', code_ok],
            [self.guest_client, '/unexacting_page/', code_not_found]
        ]
        for client, address, code in url_names:
            with self.subTest(address=address):
                response = client.get(address)
                self.assertEqual(code, response.status_code)

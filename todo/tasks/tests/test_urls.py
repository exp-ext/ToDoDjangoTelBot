from datetime import datetime, timezone

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from users.models import Group, GroupConnections, Location

from ..models import Task

User = get_user_model()


class TaskURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(
            tg_id=176432323321,
            username='user_tasks_url_test',
            password='1234GLKLl5',
        )
        cls.somebody = User.objects.create_user(
            tg_id=1235672123453321,
            username='somebody_tasks_url_test',
            password='54321',
        )
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug-url-test',
            description='Тестовое описание'
        )
        GroupConnections.objects.create(
            user=cls.user,
            group=cls.group
        )
        Location.objects.create(
            user=cls.user,
            latitude=59.799,
            longitude=30.274
        )
        cls.task = Task.objects.create(
            user=cls.user,
            group=cls.group,
            server_datetime=datetime.now(timezone.utc),
            text='Тестовое напоминание 23232',
            reminder_period='N',
            it_birthday=False,
            remind_min=120
        )
        cls.task = Task.objects.create(
            user=cls.user,
            group=cls.group,
            server_datetime=datetime.now(timezone.utc),
            text='Тестовое напоминание о ДР 23232',
            it_birthday=True,
        )
        cls.notes = '/tasks/notes/'
        cls.birthdays = '/tasks/birthdays/'
        cls.task_create = '/tasks/one_entry/create/'
        cls.task_edit = f'/tasks/one_entry/{cls.task.id}/edit/'
        cls.task_delete = f'/tasks/one_entry/{cls.task.id}/delete/'

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_somebody = Client()
        self.authorized_somebody.force_login(self.somebody)

    def test_pages_codes_by_url(self):
        """Доступность URL в приложении tasks."""
        code_ok = 200
        code_found = 302
        code_not_found = 404
        url_names = [
            [self.authorized_client, self.notes, code_ok],
            [self.guest_client, self.notes, code_found],
            [self.authorized_client, self.birthdays, code_ok],
            [self.guest_client, self.birthdays, code_found],
            [self.authorized_client, self.task_create, code_ok],
            [self.guest_client, self.task_create, code_found],
            [self.authorized_client, self.task_edit, code_ok],
            [self.guest_client, self.task_edit, code_found],
            [self.authorized_client, '/unexisting_page/', code_not_found]
        ]
        for client, address, code in url_names:
            with self.subTest(address=address):
                response = client.get(address)
                self.assertEqual(
                    response.status_code,
                    code
                )

    def test_urls_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""

        templates_url_names = {
            self.notes: 'desktop/tasks/notes.html',
            self.birthdays: 'desktop/tasks/notes.html',
            self.task_edit: 'desktop/tasks/create_task.html',
            self.task_create: 'desktop/tasks/create_task.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

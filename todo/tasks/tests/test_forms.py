
from datetime import datetime, timedelta, timezone

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from users.models import Group, GroupConnections, Location

from ..models import Task

User = get_user_model()


class TaskFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_author = User.objects.create_user(
            username='author_tasks_form',
            password='1234GLKLl5',
        )
        cls.group = Group.objects.create(
            chat_id='-512315613210651',
            title='Тестовая группа',
            slug='test-slug-159196524321',
            description='Тестовое описание'
        )
        GroupConnections.objects.create(
            user=cls.user_author,
            group=cls.group
        )
        Location.objects.create(
            user=cls.user_author,
            latitude=59.799,
            longitude=30.274
        )
        cls.task = Task.objects.create(
            user=cls.user_author,
            group=cls.group,
            server_datetime=datetime.now(timezone.utc),
            text='Тестовое напоминание 22789',
            reminder_period='N',
            it_birthday=False,
            remind_min=120
        )
        cls.task = Task.objects.create(
            user=cls.user_author,
            group=cls.group,
            server_datetime=datetime.now(timezone.utc),
            text='Тестовое напоминание о ДР 23456465',
            it_birthday=True,
        )
        cls.notes = reverse('tasks:notes')
        cls.birthdays = reverse('tasks:birthdays')
        cls.task_edit = reverse(
            'tasks:task_edit',
            kwargs={'task_id': cls.task.id}
        )
        cls.task_create = reverse('tasks:task_create')

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user_author)

    def test_post_create_forms(self):
        """Форма создает заметку."""
        posts_count = Task.objects.count()
        posts_first = set(Task.objects.all())
        now = datetime.now() + timedelta(days=1)
        form_data = {
            'server_datetime_0': now.strftime('%Y-%m-%d'),
            'server_datetime_1': now.strftime('%H:%M'),
            'text': 'напоминание о ДР 2278921635156165123',
            'reminder_period': 'N',
            'it_birthday': True,
            'remind_min': 120,
        }
        response = self.authorized_client.post(
            self.task_create,
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, self.birthdays)

        posts_second = set(Task.objects.all())
        post = posts_second.difference(posts_first)
        post = list(post).pop()

        self.assertTrue(
            Task.objects.filter(
                text='напоминание о ДР 2278921635156165123',).exists()
        )
        self.assertEqual(Task.objects.count(), posts_count + 1)

    def test_post_edit_form(self):
        """Валидная форма изменяет заметку."""
        posts_count = Task.objects.count()
        self.assertTrue(
            Task.objects.filter(text=self.task.text).exists()
        )
        now = datetime.now() + timedelta(days=2)
        form_data = {
            'server_datetime_0': now.strftime('%Y-%m-%d'),
            'server_datetime_1': now.strftime('%H:%M'),
            'text': 'пост 2278921635156165123',
            'reminder_period': 'N',
            'it_birthday': True,
            'remind_min': 120,
        }
        response = self.authorized_client.post(
            self.task_edit,
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, self.birthdays)

        self.assertEqual(
            Task.objects.get(
                text='пост 2278921635156165123',
            ).text,
            'пост 2278921635156165123'
        )
        self.assertEqual(Task.objects.count(), posts_count)
        self.assertFalse(Task.objects.filter(text=self.task.text).exists())

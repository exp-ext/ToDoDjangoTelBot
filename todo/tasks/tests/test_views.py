from datetime import datetime, timezone

from django import forms
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.test import Client, TestCase
from django.urls import reverse
from tasks.models import Task
from users.models import Group, GroupConnections, Location

User = get_user_model()


class PostViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_author = User.objects.create_user(
            username='author_tasks_views',
            password='1234GLKLl5',
        )
        cls.group = Group.objects.create(
            chat_id='-5165159361265165',
            title='Тестовая группа',
            slug='test-slug-views',
            description='Тестовое описание'
        )
        GroupConnections.objects.create(
            user=cls.user_author,
            group=cls.group,
        )
        Location.objects.create(
            user=cls.user_author,
            latitude=59.799,
            longitude=30.274
        )
        for count in range(13):
            cls.task = Task.objects.create(
                user=cls.user_author,
                group=cls.group if count < 12 else None,
                server_datetime=datetime.now(timezone.utc),
                text=f'ДР человека, №{count}',
                it_birthday=True
            )
        for count in range(13):
            cls.task = Task.objects.create(
                user=cls.user_author,
                group=cls.group if count < 12 else None,
                server_datetime=datetime.now(timezone.utc),
                text=f'Тестовое напоминание, №{count}',
                reminder_period='N',
                it_birthday=False,
                remind_min=120,
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

    def test_urls_correct_template_by_namespace(self):
        """Namespace:name использует соответствующий шаблон."""
        templates_url_names = {
            self.notes: 'tasks/notes.html',
            self.birthdays: 'tasks/notes.html',
            self.task_edit: 'tasks/create_task.html',
            self.task_create: 'tasks/create_task.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_show_correct_context(self):
        """Шаблон notes, birthdays сформирован с правильным контекстом."""
        names = [
            self.notes,
            self.birthdays,
        ]
        for name in names:
            with self.subTest(name=name):
                response = self.authorized_client.get(name)
                objects = response.context['page_obj']
                test_object = {
                    '/tasks/notes/': {
                        '0': {
                            'text': 'Тестовое напоминание, №12',
                        },
                        '11': {
                            'text': 'Тестовое напоминание, №1',
                        },
                    },
                    '/tasks/birthdays/': {
                        '0': {
                            'text': 'ДР человека, №0',
                        },
                        '11': {
                            'text': 'ДР человека, №11',
                        },
                    },
                }

                for key, item in test_object.get(name).items():
                    self.assertEqual(objects[int(key)].text, item['text'])

                self.assertEqual(len(objects), 12)
                self.assertIsInstance(objects.paginator, Paginator)

    def test_post_create_edit_show_correct_context(self):
        """Шаблон task_create & _edit сформирован с правильным контекстом."""
        names = [
            self.task_create,
            self.task_edit
        ]
        form_fields = {
            'group': forms.fields.ChoiceField,
            'server_datetime': forms.fields.DateTimeField,
            'picture_link': forms.fields.CharField,
            'text': forms.fields.CharField,
            'reminder_period': forms.fields.ChoiceField,
            'it_birthday': forms.fields.BooleanField,
            'remind_min': forms.fields.IntegerField,
            'tz': forms.fields.CharField,
        }
        for name in names:
            with self.subTest(name=name):
                response = self.authorized_client.get(name)
                for value, expected in form_fields.items():
                    with self.subTest(value=value):
                        form_field = (
                            response.context.get('form').fields.get(value)
                        )
                        self.assertIsInstance(form_field, expected)

from django.test import TestCase

from ..models import Group


class GroupModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            chat_id=1324654632134,
            title='Тестовая группа',
            slug='slug-group',
            description='Тестовое описание'
        )

    def test_group_have_correct_object_names(self):
        """Проверяем, что у модели корректно работает __str__."""
        group = self.group
        str_text = f'~ {group.title}'
        self.assertEqual(
            str_text,
            str(group),
            f'У модели Group результат __str__ = "{str_text}" '
            f'не соответствует ожидаемому "{str(group)}"'
        )

from unittest.mock import MagicMock, patch

from django.test import TestCase
from telbot.checking import check_registration
from telegram import Chat, Update
from telegram import User as TgUser
from telegram.ext import CallbackContext


class RegistrationTest(TestCase):
    def setUp(self):
        self.chat = Chat(id=12345, type='private')
        self.user = TgUser(id=67890, first_name='Test', is_bot=False)
        self.update = MagicMock(spec=Update)
        self.update.effective_chat = self.chat
        self.update.effective_user = self.user
        self.update.message.message_id = 42
        self.context = MagicMock(spec=CallbackContext)
        self.answers = {'привет': 'Добро пожаловать!'}  # Пример ответа

    @patch('telbot.checking.redis_client')
    @patch('telbot.checking.get_user_model')
    def test_user_already_registered(self, mock_get_user_model, mock_redis_client):
        """Пользователь уже зарегистрирован и имеется в Redis."""
        mock_redis_client.get.return_value = b'{"user_id": 1, "tg_user_id": 67890, "favorite_group": 1, "groups_connections": [1]}'

        registered = check_registration(self.update, self.context, self.answers)

        self.assertTrue(registered)
        mock_redis_client.get.assert_called_once()

    @patch('telbot.checking.redis_client')
    @patch('telbot.checking.User')
    def test_new_user_in_db_not_in_redis(self, mock_user_model, mock_redis_client):
        """Пользователь есть в базе, но нет в Redis."""
        mock_redis_client.get.return_value = None
        mock_user = mock_user_model.objects.filter.return_value.select_related.return_value.first.return_value
        mock_user.id = 1
        mock_user.tg_id = 67890
        mock_user.favorite_group.id = 1

        registered = check_registration(self.update, self.context, self.answers)

        self.assertTrue(registered)
        mock_user_model.objects.filter.assert_called_once()
        mock_redis_client.set.assert_called_once()

    @patch('telbot.checking.redis_client')
    @patch('telbot.checking.User')
    @patch('telbot.checking.Group')
    @patch('telbot.checking.GroupConnections')
    def test_user_and_group_update(self, mock_group_connections, mock_group, mock_user_model, mock_redis_client):
        """Пользователь и группа требуют обновления."""
        mock_redis_client.get.return_value = b'{"user_id": 1, "tg_user_id": 67890, "favorite_group": null, "groups_connections": []}'
        mock_user = mock_user_model.objects.filter.return_value.first.return_value
        mock_user.id = 1
        mock_user.tg_id = 67890

        mock_group.objects.get_or_create.return_value = (MagicMock(), True)
        test_group = mock_group.objects.get_or_create.return_value[0]
        test_group.id = 1
        test_group.link = 'link'
        test_group.title = 'title'

        self.chat.type = 'group'
        self.chat = MagicMock(spec=Chat, id=12345, type='group', link='new_link', title='new_title')
        self.update.effective_chat = self.chat

        self.chat.title = 'new_title'

        registered = check_registration(self.update, self.context, self.answers)

        self.assertTrue(registered)
        test_group.save.assert_called_once()
        mock_user.save.assert_called_once()
        mock_group_connections.objects.get_or_create.assert_called_once()
        mock_redis_client.set.assert_called_once()

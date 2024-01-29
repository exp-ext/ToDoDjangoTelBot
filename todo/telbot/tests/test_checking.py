from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from telbot.checking import check_registration
from telegram import Chat, Update
from telegram import User as TgUser
from telegram.ext import CallbackContext

User = get_user_model()


class RegistrationTest(TestCase):
    def setUp(self):
        self.chat = Chat(id=12345, type='private')
        self.user = TgUser(id=67890, first_name='Test', is_bot=False)
        self.update = MagicMock(spec=Update)
        self.update.effective_chat = self.chat
        self.update.effective_user = self.user
        self.update.message.message_id = 42
        self.context = MagicMock(spec=CallbackContext)
        self.answers = {'привет': 'Добро пожаловать!'}

    @patch('telbot.checking.redis_client')
    @patch('telbot.checking.get_user_model')
    def test_user_already_registered_none(self, mock_get_user_model, mock_redis_client):
        """Пользователь зарегистрирован и имеется в Redis, но возвращается None так как не затребован экземпляр."""
        mock_redis_client.get.return_value = b'{"user_id": 1, "tg_user_id": 67890, "favorite_group": 1, "groups_connections": [1]}'

        user = check_registration(self.update, self.context, self.answers)

        self.assertEqual(user, None)
        mock_redis_client.get.assert_called_once()

    @patch('telbot.checking.redis_client')
    @patch('telbot.checking.get_user_model')
    def test_user_already_registered_user(self, mock_get_user_model, mock_redis_client):
        """Пользователь не был зарегистрирован. Возвращается пользователь с ограничениями."""
        mock_redis_client.get.return_value = b'{"user_id": 1, "tg_user_id": 67890, "favorite_group": 1, "groups_connections": [1]}'

        user = check_registration(self.update, self.context, self.answers, allow_unregistered=True, return_user=True)

        self.assertTrue(user.is_blocked_bot)
        mock_redis_client.get.assert_called_once()

    @patch('telbot.checking.redis_client')
    @patch('telbot.checking.get_user_model')
    def test_user_already_registered_false(self, mock_get_user_model, mock_redis_client):
        """Пользователь не был зарегистрирован. Возвращается пользователь с ограничениями."""
        mock_redis_client.get.return_value = b'{"user_id": 1, "tg_user_id": 67890, "favorite_group": 1, "groups_connections": [1], "is_blocked_bot": true}'

        user = check_registration(self.update, self.context, self.answers, allow_unregistered=True, return_user=True)

        self.assertTrue(user.is_blocked_bot)
        mock_redis_client.get.assert_called_once()

    # @patch('telbot.checking.redis_client.get')
    # @patch('telbot.checking.User.objects.get_or_create')
    # @patch('telbot.checking.Group.objects.get_or_create')
    # @patch('telbot.checking.GroupConnections.objects.get_or_create')
    # def test_user_and_group_update(self, mock_group_connections_get_or_create, mock_group_get_or_create, mock_user_get_or_create, mock_redis_client):
    #     mock_redis_client.return_value = json.dumps({
    #         "user_id": 1, "tg_user_id": 67890,
    #         "favorite_group": None, "groups_connections": [],
    #         "is_blocked_bot": True
    #     }).encode('utf-8')

    #     mock_user = MagicMock(spec=User)
    #     mock_user.id = 1
    #     mock_user.tg_id = 67890
    #     mock_user_get_or_create.return_value = (mock_user, True)

    #     mock_group = MagicMock(spec=Group)
    #     mock_group.id = 1
    #     mock_group.link = 'link'
    #     mock_group.title = 'title'
    #     mock_group_get_or_create.return_value = (mock_group, True)

    #     self.chat = MagicMock(spec=Chat, id=12345, type='group', link='new_link', title='new_title')
    #     self.update.effective_chat = self.chat

    #     user = check_registration(self.update, self.context, self.answers, return_user=True)

    #     self.assertTrue(user.is_blocked_bot)
    #     mock_group_get_or_create.assert_called_once()
    #     mock_user_get_or_create.assert_called_once()
    #     mock_group_connections_get_or_create.assert_called_once()

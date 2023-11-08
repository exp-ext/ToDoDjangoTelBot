# import unittest
# from unittest.mock import MagicMock, patch

# from users.views import Authentication


# class TestAuthentication(unittest.TestCase):

#     def setUp(self):
#         self.update = MagicMock()
#         self.context = MagicMock()
#         self.update.effective_chat.type = 'private'
#         self.update.effective_user.username = 'test_user'
#         self.update.effective_user.id = 123456789

#         self.auth = Authentication(self.update, self.context)

#     @patch('users.views.User.objects.get_or_create')
#     @patch('users.views.JsonResponse')
#     def test_send_message_response(self, mock_json_response, mock_get_or_create):

#         mock_user = MagicMock()
#         pass

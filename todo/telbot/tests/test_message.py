import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch

from telegram import Chat, Update, User
from telegram.ext import CallbackContext

from ..notes.add_notes import NoteManager


class TestNoteManager(unittest.TestCase):

    def setUp(self):
        self.update = MagicMock(spec=Update)
        self.update.effective_chat = Chat(id=1234, type='private')
        self.update.effective_message.message_thread_id = 1
        self.update.effective_user = User(id=5678, is_bot=False, first_name="Test User")
        self.update.message = MagicMock()
        self.update.message.text = "Тестовое напоминание на 12.12.2024 12:00"
        self.update.message.message_id = 2

        self.context = MagicMock(spec=CallbackContext)
        self.context.user_data = {}

        self.context.bot.send_message = MagicMock()
        self.context.bot.delete_message = MagicMock()

    @patch('telbot.message.add_notes.TaskParse')
    @patch('telbot.message.add_notes.get_object_or_404')
    @patch('telbot.message.add_notes.Task.objects.filter')
    @patch('telbot.message.add_notes.Task.objects.create')
    def test_add_notes(self, mock_create, mock_filter, mock_get_object_or_404, mock_task_parse):
        mock_get_object_or_404.return_value = MagicMock()

        mock_task_parse_instance = mock_task_parse.return_value
        mock_task_parse_instance.server_date = datetime(2024, 12, 12, 12, 1)
        mock_task_parse_instance.user_date = datetime(2024, 12, 12, 12, 1)
        mock_task_parse_instance.only_message = "Тестовое напоминание"
        mock_task_parse_instance.parse_message = MagicMock()

        mock_filter.return_value = MagicMock()

        note_manager = NoteManager(self.update, self.context)
        note_manager.add_notes()

        mock_task_parse_instance.parse_message.assert_called_once()
        mock_get_object_or_404.assert_called()
        mock_filter.return_value.count.return_value = 0
        mock_create.assert_called()
        self.context.bot.send_message.assert_called()

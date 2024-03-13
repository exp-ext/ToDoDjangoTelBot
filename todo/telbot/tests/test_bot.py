import json
import unittest
from unittest.mock import ANY, MagicMock, patch

from django.test import Client, TestCase
from django.urls import reverse

from ..dispatcher import setup_dispatcher
from ..notes.add_notes import first_step_add


class ViewsTestCase(TestCase):
    def setUp(self):
        self.client = Client()

    @patch('telbot.views.process_telegram_event')
    def test_telegram_bot_webhook_post(self, mock_process_telegram_event):
        data = {'key': 'value'}
        response = self.client.post(reverse('telbot:tg_bot'), json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        mock_process_telegram_event.delay.assert_called_once_with(data)

    def test_telegram_bot_webhook_get(self):
        response = self.client.get(reverse('telbot:tg_bot'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"ok": "Get request received! But nothing done"})


class DispatcherTestCase(TestCase):
    @patch('telbot.dispatcher.CommandHandler')
    @patch('telbot.dispatcher.ConversationHandler')
    @patch('telbot.dispatcher.CallbackQueryHandler')
    @patch('telbot.dispatcher.MessageHandler')
    def test_setup_dispatcher(self, mock_MessageHandler, mock_CallbackQueryHandler, mock_ConversationHandler, mock_CommandHandler):
        bot = MagicMock()
        dispatcher = setup_dispatcher(MagicMock())

        self.assertTrue(mock_CommandHandler.called)
        self.assertTrue(mock_ConversationHandler.called)
        self.assertTrue(mock_CallbackQueryHandler.called)
        self.assertTrue(mock_MessageHandler.called)

        mock_CommandHandler.assert_any_call('start', ANY)
        mock_ConversationHandler.assert_any_call(
            entry_points=[ANY],
            states={'add_note': [ANY]},
            fallbacks=[ANY]
        )

        print(bot)
        print(dispatcher)


class TestFirstStepAdd(unittest.TestCase):
    @patch('telegram.Update')
    @patch('telegram.ext.CallbackContext')
    def test_first_step_add(self, MockUpdate, MockCallbackContext):
        update = MockUpdate()
        context = MockCallbackContext()

        update.effective_chat.id = 12345
        update.effective_user.first_name = 'TestUser'
        update.effective_message.message_thread_id = 'thread123'
        context.bot.send_message.return_value.message_id = 111

        result = first_step_add(update, context)

        context.bot.send_message.assert_called_with(
            12345,
            '*TestUser*, введите текст заметки с датой и временем 🖌',
            parse_mode='Markdown',
            message_thread_id='thread123'
        )

        # Проверка, что клавиатура была удалена и т.д.

        # Проверка возвращаемого значения функции
        self.assertEqual(result, 'add_note')

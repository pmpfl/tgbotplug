import unittest
from twx import botapi
from . import TGBot


class PluginTestCase(unittest.TestCase):
    def fake_bot(self, *args, **kwargs):
        me = kwargs.pop('me', botapi.User(9999999, 'Test', 'Bot', 'test_bot'),)
        bot = TGBot(*args, **kwargs)
        bot.tg = FakeTelegramBot()
        bot.tg._bot_user = me
        return bot

    def assertReplied(self, bot, text):
        self.assertEqual(self.last_reply(bot), text)

    def clear_replies(self, bot):
        bot.tg._sent_messages = []

    def last_reply(self, bot):
        self.assertGreater(len(bot.tg._sent_messages), 0, msg='No replies')
        return bot.tg._sent_messages[-1][0][1]


class FakeTelegramBot(botapi.TelegramBot):

    class FakeRPCRequest(object):
        def __init__(self, return_value):
            self.return_value = return_value

        def wait(self):
            return self.return_value

    def __init__(self):
        botapi.TelegramBot.__init__(self, '')
        self._sent_messages = []
        self._current_message_id = 0

    def send_message(self, chat_id, text, disable_web_page_preview=None, reply_to_message_id=None, reply_markup=None, **kwargs):
        self._sent_messages.append(([chat_id, text], kwargs))
        self._current_message_id += 1
        return FakeTelegramBot.FakeRPCRequest(botapi.Message.from_result({
            'message_id': self._current_message_id,
            'chat': {
                'id': chat_id,
            }
        }))

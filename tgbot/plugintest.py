import unittest
from twx import botapi
from . import TGBot


class PluginTestCase(unittest.TestCase):
    def fake_bot(self, *args, **kwargs):
        bot = TGBot(*args, **kwargs)
        bot.tg = FakeTelegramBot()
        return bot

    def assertReplied(self, bot, text):
        self.assertEqual(self.last_reply(bot), text)

    def last_reply(self, bot):
        self.assertGreater(len(bot.tg._sent_messages), 0, msg='No replies')
        return bot.tg._sent_messages[-1][0][1]



class FakeTelegramBot(botapi.TelegramBot):

    class FakeRPCRequest(object):
        def wait(self):
            return None

    def __init__(self):
        botapi.TelegramBot.__init__(self, '')
        self._sent_messages = []

    def send_message(self, *args, **kwargs):
        self._sent_messages.append((args, kwargs))
        return FakeTelegramBot.FakeRPCRequest()

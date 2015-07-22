from tgbot import plugintest, TGPluginBase
from twx.botapi import Update


class TestPlugin(TGPluginBase):
    def chat(self, bot, message, text):
        pass

    def list_commands(self):
        return [
            ('echo', self.echo, 'right back at ya')
        ]

    def echo(self, bot, message, text):
        reply = text
        if not reply:
            reply = 'echo'
        bot.tg.send_message(message.chat.id, reply, reply_to_message_id=message.message_id)


class TestPluginTest(plugintest.PluginTestCase):
    def setUp(self):
        self.bot = self.fake_bot('', plugins=[TestPlugin()])

    def test_reply(self):
        self.bot.process_update(
            Update.from_dict({
                'update_id': 1,
                'message': {
                    'message_id': 1,
                    'text': '/echo',
                    'chat': {
                        'id': 1,
                    },
                }
            })
        )
        self.assertReplied(self.bot, 'echo')

        self.bot.process_update(
            Update.from_dict({
                'update_id': 1,
                'message': {
                    'message_id': 1,
                    'text': '/echo test',
                    'chat': {
                        'id': 1,
                    },
                }
            })
        )
        self.assertReplied(self.bot, 'test')

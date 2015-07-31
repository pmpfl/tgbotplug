from tgbot import plugintest, models
from twx.botapi import Update, User


class DBTrackTest(plugintest.PluginTestCase):
    def setUp(self):
        self.bot = self.fake_bot(
            '',
            me=User(99, 'Test', 'Bot', 'test_bot'),
        )
        self.received_id = 1

    def receive_message(self, text, sender=None, chat=None, reply_to_message_id=None):
        if sender is None:
            sender = {
                'id': 1,
                'first_name': 'John',
                'last_name': 'Doe',
            }

        if chat is None:
            chat = sender

        reply_to_message = None

        if reply_to_message_id is not None:
            reply_to_message = {
                'message_id': reply_to_message_id,
                'chat': chat,
            }

        self.bot.process_update(
            Update.from_dict({
                'update_id': self.received_id,
                'message': {
                    'message_id': self.received_id,
                    'text': text,
                    'chat': chat,
                    'from': sender,
                    'reply_to_message': reply_to_message,
                }
            })
        )

        self.received_id += 1

    def receive_update(self, sender=None, chat=None, left_chat_participant=None, new_chat_participant=None, group_chat_created=False):
        if sender is None:
            sender = {
                'id': 1,
                'first_name': 'John',
                'last_name': 'Doe',
            }

        if chat is None:
            chat = sender

        self.bot.process_update(
            Update.from_dict({
                'update_id': self.received_id,
                'message': {
                    'message_id': self.received_id,
                    'text': None,
                    'chat': chat,
                    'from': sender,
                    'left_chat_participant': left_chat_participant,
                    'new_chat_participant': new_chat_participant,
                    'group_chat_created': group_chat_created,
                }
            })
        )

        self.received_id += 1

    def test_reply(self):
        chat1 = {'id': 1, 'title': 'test chat'}
        sender2 = {
            'id': 2,
            'first_name': 'John',
            'last_name': 'Doe',
        }

        # empty DB
        self.assertEqual(models.User.select().count(), 0)
        self.assertEqual(models.GroupChat.select().count(), 0)

        # user message, no chat created
        self.receive_message('one')
        self.assertEqual(models.User.select().count(), 1)
        self.assertEqual(models.GroupChat.select().count(), 0)

        # group chat message
        self.receive_message('two', chat=chat1)
        self.assertEqual(models.User.select().count(), 1)
        self.assertEqual(models.GroupChat.select().count(), 1)

        # different user, same chat
        self.receive_message('two', sender=sender2, chat=chat1)
        self.assertEqual(models.User.select().count(), 2)
        self.assertEqual(models.GroupChat.select().count(), 1)

        # kicked out of group
        self.receive_update(chat=chat1, left_chat_participant=dict(self.bot.me.__dict__))
        self.assertEqual(models.GroupChat.select().count(), 0)

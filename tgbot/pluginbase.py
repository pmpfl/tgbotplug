from twx.botapi import GroupChat
from . import models
import json


class TGPluginBase(object):
    def __init__(self):
        self.key_name = '%s.%s' % (self.__module__, self.__class__.__name__)

    def list_commands(self):
        '''
        this method should return a list of tuples containing:
        ('command', method_to_execute, 'command description')

        Set command description to None (or '') to prevent that
        command from being listed by TGBot.list_commands
        '''
        raise NotImplementedError('Abstract method')

    def chat(self, bot, message, text):
        '''
        this method will be called on plugins used with option no_command
        '''
        raise NotImplementedError('Abstract method, no_command plugins need to implement this')

    def need_reply(self, handler, in_message, out_message=None, selective=False):
        try:
            sender = models.User.get(models.User.id == in_message.sender.id)
        except models.User.DoesNotExist:
            sender = models.User.create(
                id=in_message.sender.id,
                first_name=in_message.sender.first_name,
                last_name=in_message.sender.last_name,
            )

        if isinstance(in_message.chat, GroupChat):
            try:
                chat = models.GroupChat.get(models.GroupChat.id == in_message.chat.id)
            except models.GroupChat.DoesNotExist:
                chat = models.GroupChat.create(id=in_message.chat.id, title=in_message.chat.title)
        elif in_message.chat.id == in_message.sender.id:
            chat = None
        else:
            raise RuntimeError('Unexpected chat id %s (not a GroupChat nor sender)')

        m = models.Message.create(
            id=in_message.message_id,
            group_chat=chat,
            sender=sender,
            text=in_message.text,
            reply_plugin=self.key_name,
            reply_method=handler.im_func.func_name,
            reply_selective=selective,
        )

        if out_message is not None:
            m.reply_id = out_message.message_id
            m.save()

    def clear_chat_replies(self, chat):
        if isinstance(chat, GroupChat):
            models.Message.delete().where(models.Message.group_chat_id == chat.id)
        else:
            models.Message.delete().where(models.Message.sender_id == chat.id)

    def save_data(self, key1, key2=None, obj=None):
        json_obj = None
        if obj is not None:
            json_obj = json.dumps(obj)

        try:
            data = models.PluginData.get(
                models.PluginData.name == self.key_name,
                models.PluginData.k1 == key1,
                models.PluginData.k2 == key2,
            )
            data.data = json_obj
        except models.PluginData.DoesNotExist:
            data = models.PluginData(
                name=self.key_name,
                k1=key1,
                k2=key2,
                data=json_obj
            )

        data.save()

    def read_data(self, key1, key2=None):
        try:
            data = models.PluginData.get(
                models.PluginData.name == self.key_name,
                models.PluginData.k1 == key1,
                models.PluginData.k2 == key2
            )
            return json.loads(data.data)
        except models.PluginData.DoesNotExist:
            return None

    def is_expected(self, bot, message):  # noqa - not complex at all!
        msg = None
        if message.reply_to_message is not None:
            try:
                msg = models.Message.get(
                    models.Message.reply_id == message.reply_to_message.message_id,
                    models.Message.reply_plugin == self.key_name,
                )
            except models.Message.DoesNotExist:
                return False

        if msg is None:
            if isinstance(message.chat, GroupChat):
                msgs = models.Message.select().where(
                    models.Message.group_chat == message.chat.id,
                    models.Message.reply_plugin == self.key_name,
                )
                for m in msgs:
                    if not m.reply_selective:
                        msg = m
                        break
                    if m.sender.id == message.sender.id:
                        msg = m
                        break
            else:
                try:
                    msg = models.Message.get(
                        models.Message.sender == message.chat.id,
                        models.Message.reply_plugin == self.key_name,
                    )
                except models.Message.DoesNotExist:
                    pass

        if msg is None:
            return False

        handler = getattr(self, msg.reply_method)

        if handler is None:
            return False

        msg.delete_instance()

        handler(bot, message, message.text)

        return True

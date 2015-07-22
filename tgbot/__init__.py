#!/usr/bin/env python
# coding=utf-8

from time import sleep
from twx.botapi import TelegramBot, GroupChat


class TGPluginBase(object):
    def __init__(self):
        self._msg_id_track = {}
        self._msg_in_track = {}

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
        if in_message.chat.id not in self._msg_in_track:
            self._msg_in_track[in_message.chat.id] = {}

        chat = self._msg_in_track[in_message.chat.id]

        if isinstance(in_message.chat, GroupChat) and selective:
            key2 = in_message.sender.id
        else:
            key2 = 'any'

        if out_message is not None:
            self._msg_id_track[out_message.message_id] = key2
            chat[key2] = (handler, out_message.message_id)
        else:
            chat[key2] = (handler, None)

    def clear_chat_replies(self, chat_id):
        if chat_id not in self._msg_in_track:
            return

        chat = self._msg_in_track[chat_id]
        for msg in chat:
            _, out_id = chat[msg]
            if out_id is not None:
                del(self._msg_id_track[out_id])

        del(self._msg_in_track[chat_id])

    def is_expected(self, bot, message):
        if message.reply_to_message is not None:
            if message.reply_to_message.message_id in self._msg_id_track:
                chat_id = message.chat.id
                key2 = self._msg_id_track[message.reply_to_message.message_id]
                handler, _ = self._msg_in_track[chat_id][key2]
                del(self._msg_in_track[chat_id][key2])
                del(self._msg_id_track[message.reply_to_message.message_id])
                handler(bot, message, message.text)
                return True
            else:
                return False
        if message.chat.id in self._msg_in_track:
            chat = self._msg_in_track[message.chat.id]
            if chat.get('any') is not None:
                key2 = 'any'
            if key2 is None and chat.get(message.sender.id) is not None:
                key2 = message.sender.id
            if key2 is None:
                return False
            handler, out_id = chat[key2]
            del(chat[key2])
            if out_id is not None:
                del(self._msg_id_track[out_id])

            handler(bot, message, message.text)
            return True

        return False

class TGBot(object):
    def __init__(self, token, polling_time=2, plugins=[], no_command=None):
        self._token = token
        self.tg = TelegramBot(token)
        self._last_id = None
        self.cmds = {}
        self._polling_time = polling_time
        self._no_cmd = no_command
        self._msgs = {}
        self._plugins = plugins

        if no_command is not None:
            if not isinstance(no_command, TGPluginBase):
                raise NotImplementedError('%s does not subclass tgbot.TGPluginBase' % type(no_command).__name__)

        for p in self._plugins:

            if not isinstance(p, TGPluginBase):
                raise NotImplementedError('%s does not subclass tgbot.TGPluginBase' % type(p).__name__)

            for cmd in p.list_commands():
                if cmd[0] in self.cmds:
                    raise Exception(
                        'Duplicate command %s: both in %s and %s' % [
                            cmd[0],
                            type(p).__name__,
                            self.cmds[cmd[0]][2],
                        ])
                self.cmds[cmd[0]] = (cmd[1], cmd[2], type(p).__name__)

    def run(self):
        while True:
            ups = self.tg.get_updates(offset=self._last_id).wait()
            for up in ups:
                if up.message.text:
                    if up.message.text.startswith('/'):
                        spl = up.message.text.find(' ')
                        if spl < 0:
                            self.process(up.message.text[1:], '', up.message)
                        else:
                            self.process(up.message.text[1:spl], up.message.text[spl + 1:], up.message)
                    else:
                        was_expected = False
                        for p in self._plugins:
                            was_expected = p.is_expected(self, up.message)
                            if was_expected:
                                break

                        if self._no_cmd is not None and not was_expected:
                            self._no_cmd.chat(self, up.message, up.message.text)

                else:
                    pass
                self._last_id = up.update_id + 1

            sleep(self._polling_time)

    def list_commands(self):
        out = []
        for ck in self.cmds:
            if self.cmds[ck][1]:
                out.append((ck, self.cmds[ck][1]))
        return out

    def print_commands(self):
        '''
        utility method to print commands and descriptions
        for @BotFather
        '''
        cmds = self.list_commands()
        for ck in cmds:
            print '%s - %s' % ck

    def process(self, cmd, text, message):
        if cmd in self.cmds:
            self.cmds[cmd][0](self, message, text)

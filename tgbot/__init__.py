#!/usr/bin/env python
# coding=utf-8

from time import sleep
from twx.botapi import TelegramBot


class TGPlugin(object):
    def list_commands(self):
        return {
            'echo': self.echo
        }

    def echo(self, tg, message, text):
        reply = text
        if not reply:
            reply = 'echo'
        tg.send_message(message.chat.id, reply, reply_to_message_id=message.message_id)


class TGBot(object):
    def __init__(self, token, polling_time=2, plugins=None):
        self._token = token
        self._tg = TelegramBot(token)
        self._last_id = None
        self.cmds = {}
        self._polling_time = polling_time

        for p in plugins:
            cmds = p.list_commands()
            for cmd in cmds:
                if cmd in self.cmds:
                    raise Exception('Duplicate command %s' % cmd)
                self.cmds[cmd] = cmds[cmd]

    def run(self):
        while True:
            ups = self._tg.get_updates(offset=self._last_id).wait()
            for up in ups:
                if up.message.text:
                    if up.message.text.startswith('/'):
                        spl = up.message.text.find(' ')
                        if spl < 0:
                            self.process(up.message.text[1:], '', up.message)
                        else:
                            self.process(up.message.text[1:spl], up.message.text[spl + 1:], up.message)
                    else:
                        if up.message.reply_to_message:
                            self.process(up.message.reply_to_message.text[1:], up.message.text, up.message)
                        else:
                            pass
                else:
                    pass
                self._last_id = up.update_id + 1

            sleep(self._polling_time)

    def process(self, cmd, text, message):
        if cmd in self.cmds:
            self.cmds[cmd](self._tg, message, text)

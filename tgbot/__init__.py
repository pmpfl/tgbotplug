#!/usr/bin/env python
# coding=utf-8

from time import sleep
from twx.botapi import TelegramBot


class TGPluginBase(object):
    def list_commands(self):
        '''
        this method should return a dictionary such as
        { 'echo': self.echo_cmd }
        '''
        return {}


class TGBot(object):
    def __init__(self, token, polling_time=2, plugins=[], no_command=None):
        self._token = token
        self._tg = TelegramBot(token)
        self._last_id = None
        self.cmds = {}
        self._polling_time = polling_time
        self._no_cmd = no_command

        for p in plugins:
            cmds = p.list_commands()
            for cmd in cmds:
                if cmd in self.cmds:
                    raise Exception(
                        'Duplicate command %s: both in %s and %s' % [
                            cmd,
                            type(p).__name__,
                            self.cmds[cmd][1],
                        ])
                self.cmds[cmd] = (cmds[cmd], type(p).__name__)

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
                        elif self._no_cmd is not None:
                            self._no_cmd(self._tg, up.message, up.message.text)

                else:
                    pass
                self._last_id = up.update_id + 1

            sleep(self._polling_time)

    def process(self, cmd, text, message):
        if cmd in self.cmds:
            self.cmds[cmd][0](self._tg, message, text)

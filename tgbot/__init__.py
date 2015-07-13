#!/usr/bin/env python
# coding=utf-8

from time import sleep
from twx.botapi import TelegramBot


class TGBot(object):
    def __init__(self, token, plugins=None):
        self._token = token
        self._tg = TelegramBot(token)
        self._last_id = None

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
            sleep(2)

    def process(self, cmd, text, message):
        self._tg.send_message(message.chat.id, 'Sup?')


def main():
    tg = TGBot('token')
    tg.run()

if __name__ == '__main__':
    main()

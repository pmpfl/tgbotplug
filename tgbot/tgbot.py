from twx.botapi import TelegramBot, Error, GroupChat
from . import models
from .pluginbase import TGPluginBase, TGCommandBase
from playhouse.db_url import connect
import peewee
import sys


class TGBot(object):
    def __init__(self, token, plugins=[], no_command=None, db_url=None):
        self._token = token
        self.tg = TelegramBot(token)
        self._last_id = None
        self.cmds = {}
        self.pcmds = {}
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

                if not isinstance(cmd, TGCommandBase):
                    raise NotImplementedError('%s does not subclass tgbot.TGCommandBase' % type(cmd).__name__)

                if cmd in self.cmds or cmd in self.pcmds:
                    raise Exception(
                        'Duplicate command %s: both in %s and %s' % (
                            cmd.command,
                            type(p).__name__,
                            self.cmds.get(cmd.command) or self.pcmds.get(cmd.command),
                        )
                    )

                if cmd.prefix:
                    self.pcmds[cmd.command] = cmd
                else:
                    self.cmds[cmd.command] = cmd

        if db_url is None:
            self.db = connect('sqlite:///:memory:')
            models.database_proxy.initialize(self.db)
            self.setup_db()
        else:
            self.db = connect(db_url)
            self.db.autorollback = True
            models.database_proxy.initialize(self.db)

    def update_bot_info(self):
        # re-implement update_bot_info to make it synchronous
        if self.tg.username is None:
            self.tg._bot_user = self.tg.get_me().wait()

    def process_update(self, update):  # noqa not complex at all!
        self.update_bot_info()
        message = update.message

        try:
            models.User.create(
                id=message.sender.id,
                first_name=message.sender.first_name,
                last_name=message.sender.last_name,
            )
        except peewee.IntegrityError:
            pass  # ignore, already exists

        if message.left_chat_participant is not None and message.left_chat_participant.username == self.tg.username:
            models.GroupChat.delete().where(models.GroupChat.id == message.chat.id).execute()
        elif isinstance(message.chat, GroupChat):
            try:
                models.GroupChat.create(id=message.chat.id, title=message.chat.title)
            except peewee.IntegrityError:
                pass

        if message.new_chat_participant is not None and message.new_chat_participant != self.me:
            try:
                models.User.create(
                    id=message.new_chat_participant.id,
                    first_name=message.new_chat_participant.first_name,
                    last_name=message.new_chat_participant.last_name,
                )
            except peewee.IntegrityError:
                pass  # ignore, already exists

        if message.contact is not None:
            try:
                models.User.create(
                    id=message.contact.user_id,
                    first_name=message.contact.first_name,
                    last_name=message.contact.last_name,
                )
            except peewee.IntegrityError:
                pass  # ignore, already exists

        if message.text is not None and message.text.startswith('/'):
            spl = message.text.find(' ')

            if spl < 0:
                cmd = message.text[1:]
                text = ''
            else:
                cmd = message.text[1:spl]
                text = message.text[spl+1:]

            spl = cmd.find('@')
            if spl > -1:
                cmd = cmd[:spl]

            self.process(message, cmd, text)
        else:
            was_expected = False
            for p in self._plugins:
                was_expected = p.is_expected(self, message)
                if was_expected:
                    break

            if self._no_cmd is not None and not was_expected:
                self._no_cmd.chat(self, message, message.text)

    def setup_db(self):
        models.create_tables(self.db)

    def run(self, polling_time=2):
        from time import sleep
        # make sure all webhooks are disabled
        self.tg.set_webhook().wait()

        while True:
            ups = self.tg.get_updates(offset=self._last_id).wait()
            if isinstance(ups, Error):
                print 'Error: ', ups
            else:
                for up in ups:
                    self.process_update(up)
                    self._last_id = up.update_id + 1

            sleep(polling_time)

    def run_web(self, hook_url, **kwargs):
        from .webserver import run_server
        url = hook_url
        if url[-1] != '/':
            url += '/'
        self.tg.set_webhook(url + 'update/' + self._token)
        run_server(self, **kwargs)

    def list_commands(self):
        return self.cmds.values() + self.pcmds.values()

    def print_commands(self, out=sys.stdout):
        '''
        utility method to print commands
        and descriptions for @BotFather
        '''
        cmds = self.list_commands()
        for ck in cmds:
            if ck.printable:
                out.write('%s\n' % ck)

    def process(self, message, cmd, text):
        if cmd in self.cmds:
            self.cmds[cmd].method(self, message, text)
        elif cmd in self.pcmds:
            self.pcmds[cmd].method(self, message, text)
        else:
            for pcmd in self.pcmds:
                if cmd.startswith(pcmd):
                    self.pcmds[pcmd].method(self, message, cmd[len(pcmd):] + text)
                    break

from twx.botapi import TelegramBot, Error, GroupChat
from . import models
from .pluginbase import TGPluginBase
from playhouse.db_url import connect
import peewee


class TGBot(object):
    def __init__(self, token, plugins=[], no_command=None, db_url=None):
        self._token = token
        self.tg = TelegramBot(token)
        self._last_id = None
        self.cmds = {}
        self._no_cmd = no_command
        self._msgs = {}
        self._plugins = plugins
        self.me = None

        if self._token:
            self.me = self.tg.get_me().wait()

        if no_command is not None:
            if not isinstance(no_command, TGPluginBase):
                raise NotImplementedError('%s does not subclass tgbot.TGPluginBase' % type(no_command).__name__)

        for p in self._plugins:

            if not isinstance(p, TGPluginBase):
                raise NotImplementedError('%s does not subclass tgbot.TGPluginBase' % type(p).__name__)

            for cmd in p.list_commands():
                if cmd[0] in self.cmds:
                    raise Exception(
                        'Duplicate command %s: both in %s and %s' % (
                            cmd[0],
                            type(p).__name__,
                            self.cmds[cmd[0]][2],
                        )
                    )
                self.cmds[cmd[0]] = (cmd[1], cmd[2], type(p).__name__)

        if db_url is None:
            self.db = connect('sqlite:///:memory:')
            models.database_proxy.initialize(self.db)
            self.setup_db()
        else:
            self.db = connect(db_url)
            models.database_proxy.initialize(self.db)

    def process_update(self, update):  # noqa not complex at all!
        message = update.message

        try:
            models.User.create(
                id=message.sender.id,
                first_name=message.sender.first_name,
                last_name=message.sender.last_name,
            )
        except peewee.IntegrityError:
            pass  # ignore, already exists

        if message.left_chat_participant == self.me:
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

        if message.text:
            if message.text.startswith('/'):
                spl = message.text.find(' ')
                if spl < 0:
                    self.process(message.text[1:], '', message)
                else:
                    self.process(message.text[1:spl], message.text[spl + 1:], message)
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
        spl = cmd.find('@')
        if spl > 0:
            cmd = cmd[:spl]
        if cmd in self.cmds:
            try:
                self.cmds[cmd][0](self, message, text)
            except:
                import traceback
                traceback.print_exc()
                self.tg.send_message(message.chat.id, 'some error occurred... (logged and reported)', reply_to_message_id=message.message_id)

from twx.botapi import TelegramBot, Error
from . import models
from .pluginbase import TGPluginBase, TGCommandBase
from playhouse.db_url import connect


class TGBot(object):
    def __init__(self, token, name, plugins=[], no_command=None, db_url=None):
        self._token = token
        self.tg = TelegramBot(token)
        self._last_id = None
        self.cmds = {}
        self._no_cmd = no_command
        self._msgs = {}
        self._plugins = plugins
        self._name = name

        if no_command is not None:
            if not isinstance(no_command, TGPluginBase):
                raise NotImplementedError('%s does not subclass tgbot.TGPluginBase' % type(no_command).__name__)

        for p in self._plugins:

            if not isinstance(p, TGPluginBase):
                raise NotImplementedError('%s does not subclass tgbot.TGPluginBase' % type(p).__name__)

            for cmd in p.list_commands():

                if not isinstance(cmd, TGCommandBase):
                    raise NotImplementedError('%s does not subclass tgbot.TGCommandBase' % type(cmd).__name__)

                if cmd in self.cmds:
                    raise Exception(
                        'Duplicate command %s: both in %s and %s' % (
                            cmd.command,
                            type(p).__name__,
                            self.cmds[cmd.command].description,
                        )
                    )
                self.cmds[cmd.command] = cmd

        if db_url is None:
            self.db = connect('sqlite:///:memory:')
            models.database_proxy.initialize(self.db)
            self.setup_db()
        else:
            self.db = connect(db_url)
            models.database_proxy.initialize(self.db)

    def process_update(self, update):
        if update.message.text:
            if update.message.text.startswith('/'):
                splat = update.message.text.find('@')
                text = update.message.text if splat < 0 else update.message.text[:splat] + update.message.text[(splat+len(self.name)+1):]
                for p in self._plugins:
                    self.process(p, update.message, text)
            else:
                was_expected = False
                for p in self._plugins:
                    was_expected = p.is_expected(self, update.message)
                    if was_expected:
                        break

                if self._no_cmd is not None and not was_expected:
                    self._no_cmd.chat(self, update.message, update.message.text)

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
        from . import webserver
        url = hook_url
        if url[-1] != '/':
            url += '/'
        self.tg.set_webhook(url + 'update/' + self._token)
        webserver.run_server(self, **kwargs)

    def list_commands(self):
        out = []
        for ck in self.cmds:
            if self.cmds[ck].description:
                out.append((ck, self.cmds[ck].description))
        return out

    def print_commands(self):
        '''
        utility method to print commands and descriptions
        for @BotFather
        '''
        cmds = self.list_commands()
        for ck in cmds:
            print '%s - %s' % ck

    def process(self, plugin, message, text):
        print text
        for cmd in plugin.list_commands():
            if text.startswith(cmd.command, 1):
                if len(text) == (len(cmd.command) + 1):
                    cmd.method(self, message, '')
                    break
                spl = text.find(' ')
                if spl > 0:
                    cmd.method(self, message, text[spl + 1:])
                    break
                if cmd.prefix:
                    cmd.method(self, message, text[len(cmd.command) + 1:])
                    break

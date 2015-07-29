#!/usr/bin/env python
from . import TGBot
import argparse


def build_parser():
    parser = argparse.ArgumentParser(description='Run your own Telegram bot.')
    parser.add_argument('plugins', metavar='plugin', nargs='*',
                        help='a subclass of TGPluginBase (ex: plugins.echo.EchoPlugin)')
    parser.add_argument('--token', '-t', dest='token',
                        help='bot token provided by @BotFather')
    parser.add_argument('--nocommand', '-n', dest='nocmd',
                        help='plugin.method to be used for non-command messages')
    parser.add_argument('--polling', '-p', dest='polling', type=int, default=2,
                        help='interval (in seconds) to check for message updates')
    parser.add_argument('--db_url', '-d', dest='db_url',
                        help='URL for database (default is in-memory sqlite)')
    parser.add_argument('--listcommands', '-l', dest='list', action='store_const',
                        const=True, default=False,
                        help='plugin method to be used for non-command messages (ex: plugins.simsimi.SimsimiPlugin.simsimi)')
    parser.add_argument('--webhook', '-w', dest='webhook', nargs=2, metavar=('hook_url', 'port'),
                        help='use webhooks (instead of polling) - requires bottle')
    return parser


def import_class(cl):
    d = cl.rfind(".")
    class_name = cl[d + 1:len(cl)]
    m = __import__(cl[0:d], globals(), locals(), [class_name])
    return getattr(m, class_name)


def main():
    from requests.packages import urllib3
    urllib3.disable_warnings()

    parser = build_parser()
    args = parser.parse_args()

    plugins = []

    try:
        for plugin_name in args.plugins:
            cl = import_class(plugin_name)
            plugins.append(cl())

        nocmd = None
        if args.nocmd is not None:
            cl = import_class(args.nocmd)
            nocmd = cl()
    except Exception as e:
        parser.error(e.message)

    tg = TGBot(args.token, plugins=plugins, no_command=nocmd, db_url=args.db_url)

    if args.list:
        tg.print_commands()
        return

    if args.token is None:
        parser.error('--token is required')

    if args.webhook is None:
        tg.run(polling_time=args.polling)
    else:
        tg.run_web(args.webhook[0], host='0.0.0.0', port=int(args.webhook[1]))


if __name__ == '__main__':
    main()

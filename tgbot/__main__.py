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
    parser.add_argument('--listcommands', '-l', dest='list', action='store_const',
                        const=True, default=False,
                        help='plugin method to be used for non-command messages (ex: plugins.simsimi.SimsimiPlugin.simsimi)')
    return parser


def import_class(cl):
    d = cl.rfind(".")
    classname = cl[d + 1:len(cl)]
    m = __import__(cl[0:d], globals(), locals(), [classname])
    return getattr(m, classname)


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

    tg = TGBot(args.token, polling_time=args.polling, plugins=plugins, no_command=nocmd)

    if args.list:
        tg.print_commands()
    else:
        if args.token is None:
            parser.error('--token is required')

    if args.token is not None:
        tg.run()


if __name__ == '__main__':
    main()

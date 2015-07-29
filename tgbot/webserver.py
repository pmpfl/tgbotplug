from bottle import route, run, request, abort
from twx.botapi import Update

tg_bot = None


@route('/ping/')
def ping():
    return '<b>Pong!</b>'


@route('/update/<token>', method='POST')
def test(token):
    if token != tg_bot._token:
        abort(404, 'Not found: \'/update/%s\'' % token)
    tg_bot.process_update(Update.from_dict(request.json))
    return None


def run_server(bot, **kwargs):
    global tg_bot
    tg_bot = bot
    run(**kwargs)
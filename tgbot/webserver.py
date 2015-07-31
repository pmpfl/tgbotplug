from bottle import route, run, request, abort
from twx.botapi import Update

tg_bot = None


@route('/ping/')
def ping():
    return '<b>Pong!</b>'


@route('/update/<token>', method='POST')
def update(token):
    if token != tg_bot._token:
        abort(404, 'Not found: \'/update/%s\'' % token)
    tg_bot.process_update(Update.from_dict(request.json))
    return None


def wsgi_app(bot):
    global tg_bot
    tg_bot = bot
    from bottle import default_app
    return default_app()


def run_server(bot, **kwargs):
    wsgi_app(bot)
    run(**kwargs)

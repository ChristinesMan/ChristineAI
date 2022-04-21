import os
import threading
from bottle import TEMPLATE_PATH, route, run, template, redirect, request, response, abort, static_file
import json

import log
import status
import sounds
import breath
import wernicke
import conversate

TEMPLATE_PATH.append('./httpserver/')

@route('/')
def index():

    return template('root')


@route('/<filename:re:.*\.js>')
def send_js(filename):
    return static_file(filename, root='./httpserver/', mimetype='application/javascript')
@route('/<filename:re:.*\.ico>')
def send_ico(filename):
    return static_file(filename, root='./httpserver/', mimetype='image/x-icon')
@route('/<filename:re:.*\.css>')
def send_css(filename):
    return static_file(filename, root='./httpserver/', mimetype='text/css')


@route('/wernicke/words/<words>')
def wernicke_words(words):

    # pass the incoming words to the locus of word control
    conversate.thread.Words(words)
    return 'OK'


@route('/wernicke/processing/<onoff>')
def wernicke_onoff(onoff):

    if onoff == 'on':

        wernicke.thread.StartProcessing()
        return 'OK'

    elif onoff == 'off':

        wernicke.thread.StopProcessing()
        return 'OK'

    else:

        return 'WUT'


@route('/status/set/<var>', method='POST')
def setvar(var):

    if var in dir(status):

        if isinstance(getattr(status, var), float):

            try:
                setattr(status, var, float(request.forms.get('value')))
            except ValueError:
                return 'FAIL'

        elif isinstance(getattr(status, var), int):

            try:
                setattr(status, var, int(request.forms.get('value')))
            except ValueError:
                return 'FAIL'

        elif isinstance(getattr(status, var), bool):

            if request.forms.get('value') == 'True':
                setattr(status, var, True)
            elif request.forms.get('value') == 'False':
                setattr(status, var, False)

        return 'OK'

    else:

        return 'WUT'


@route('/status/get/<var>', method='POST')
def getvar(var):

    if var in dir(status):

        return str(getattr(status, var))

    else:

        return 'WUT'


# run(host='0.0.0.0', port=80, debug=True)
# run the server in a thread, otherwise it blocks here and prevents everything else from happening
threading.Thread(target=run, daemon=True, kwargs=dict(host='0.0.0.0', port=80)).start()

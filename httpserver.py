import os
from bottle import TEMPLATE_PATH, route, run, template, redirect, request, response, abort, static_file
import json

import log
import status
import sounds
import breath
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


@route('/wernicke/<words>')
def wernicke(words):

    # pass the incoming words to the locus of word control
    conversate.thread.Words(words)
    return 'OK'


run(host='0.0.0.0', port=80, debug=True)


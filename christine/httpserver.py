"""
Handles the http server used for management, external signals, etc
"""
import os
import threading

# pylint: disable=missing-function-docstring,no-member
from bottle import TEMPLATE_PATH, route, run, template, request, static_file, debug

from christine import log
from christine.status import STATE
from christine.parietal_lobe import parietal_lobe
from christine.wernicke import wernicke
from christine.sleep import sleep

debug(True)

TEMPLATE_PATH.append("./httpserver/")


@route("/")
def index():
    return template("index", USER_NAME=parietal_lobe.user_name)


# @route(r"/<filename:re:.*\.js>")
# def send_js(filename):
#     return static_file(filename, root="./httpserver/", mimetype="application/javascript")
# @route(r"/<filename:re:.*\.html>")
# def send_html(filename):
#     return static_file(filename, root="./httpserver/", mimetype="text/html")
# @route(r"/<filename:re:.*\.txt>")
# def send_txt(filename):
#     return static_file(filename, root="./httpserver/", mimetype="text/plain")
# @route(r"/<filename:re:.*\.ico>")
# def send_ico(filename):
#     return static_file(filename, root="./httpserver/", mimetype="image/x-icon")
# @route(r"/<filename:re:.*\.css>")
# def send_css(filename):
#     return static_file(filename, root="./httpserver/", mimetype="text/css")
# @route(r"/<filename:re:.*\.(wav|mp3|gz|tar\.gz)>")
# def send_file_download(filename):
#     return static_file(filename, root="./httpserver/", mimetype="application/octet-stream")


@route("/status")
def getstatus():
    """This should return a json object with the current status of the system."""

    return STATE.to_json()


@route("/who_is_speaking", method="POST")
def set_speaker():
    """Set the current speaker"""

    try:
        speaker = request.json.get("speaker")
    except Exception as ex:
        return f"Error: {str(ex)}"

    STATE.who_is_speaking = speaker

    return "OK"


@route("/control", method="POST")
def control():
    """Various switches that can be flipped"""

    try:
        action = request.json.get("action")
    except Exception as ex:
        return f"Error: {str(ex)}"
    log.main.info("Received control action: '%s'", action)

    if action == "restart":
        os.system("systemctl restart christine.service")
        return "OK"

    elif action == "stop":
        os.system("systemctl stop christine.service")
        return "OK"

    elif action == "reboot":
        os.system("reboot")
        return "OK"

    elif action == "poweroff":
        os.system("poweroff")
        return "OK"

    elif action == "wernicke_on":
        wernicke.audio_processing_start()
        return "OK"

    elif action == "wernicke_off":
        wernicke.audio_processing_stop()
        return "OK"

    elif action == "sleep":
        sleep.wake_up(-1000000.0)
        return "OK"

    elif action == "wake":
        sleep.wake_up(50.0)
        return "OK"

    return "WUT"


@route("/logmark", method="POST")
def log_mark():
    """Add a message to the logs for later review"""

    msg = request.json.get("msg")

    if len(msg) < 100:
        log.main.critical(msg)
        return "OK"

    return "WTF"


@route("/status/set/<var>", method="POST")
def setvar(var):
    """Set a variable in the STATE."""

    if var in dir(STATE):
        if isinstance(getattr(STATE, var), float):
            try:
                setattr(STATE, var, float(request.json.get("value")))
            except ValueError:
                return "FAIL"

        elif isinstance(getattr(STATE, var), int):
            try:
                setattr(STATE, var, int(request.json.get("value")))
            except ValueError:
                return "FAIL"

        elif isinstance(getattr(STATE, var), bool):
            if request.forms.get("value") == "True":
                setattr(STATE, var, True)
            elif request.forms.get("value") == "False":
                setattr(STATE, var, False)

        return "OK"

    return "WUT"


@route("/status/get/<var>", method="POST")
def getvar(var):
    """Get the value of a variable."""

    if var in dir(STATE):
        return str(getattr(STATE, var))

    return "WUT"


# run the server in a thread
# don't start the thread; that is done from __main__
httpserver = threading.Thread(
    target=run, daemon=True, name="httpserver", kwargs=dict(host="0.0.0.0", port=80)
)

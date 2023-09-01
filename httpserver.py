"""
Handles the http server used for management, external signals, etc
"""
import os
import threading

# pylint: disable=missing-function-docstring,no-member
from bottle import TEMPLATE_PATH, route, run, template, request, static_file  # , debug

import log
from status import SHARED_STATE
import sounds
import broca
import sleep
import wernicke

# debug(True)

TEMPLATE_PATH.append("./httpserver/")


@route("/")
def index():
    return template("root")


@route(r"/<filename:re:.*\.js>")
def send_js(filename):
    return static_file(
        filename, root="./httpserver/", mimetype="application/javascript"
    )


@route(r"/<filename:re:.*\.html>")
def send_html(filename):
    return static_file(filename, root="./httpserver/", mimetype="text/html")


@route(r"/<filename:re:.*\.txt>")
def send_txt(filename):
    return static_file(filename, root="./httpserver/", mimetype="text/plain")


@route(r"/<filename:re:.*\.ico>")
def send_ico(filename):
    return static_file(filename, root="./httpserver/", mimetype="image/x-icon")


@route(r"/<filename:re:.*\.css>")
def send_css(filename):
    return static_file(filename, root="./httpserver/", mimetype="text/css")


@route(r"/<filename:re:.*\.(wav|mp3|gz|tar\.gz)>")
def send_file_download(filename):
    return static_file(
        filename, root="./httpserver/", mimetype="application/octet-stream"
    )


@route("/status")
def getstatus():
    return template("status", SHARED_STATE=SHARED_STATE)


@route("/control")
def getcontrol():
    return template("control")


@route("/sounds")
def getsounds():
    return template("sounds", sounds=sounds)


@route("/collections")
def getcollections():
    return template("collections", sounds=sounds)


@route("/upload")
def getupload():
    return template("upload")


@route("/Honey_Say", method="POST")
def posthoneysay():
    sound_id = request.forms.get("sound_id")
    broca.thread.queue_sound(
        sound=sounds.soundsdb.get_sound(sound_id=sound_id),
        play_sleeping=True,
        play_ignore_speaking=True,
        play_no_wait=True,
        priority=10,
    )
    log.http.info("Honey Say Request: %s", sound_id)
    return "OK"


# @route('/Sound_Detail', method='POST')
# def postsounddetail():
#     sound_id = request.forms.get('sound_id')
#     return template('sound_detail', Sound=sounds.soundsdb.GetSound(sound_id = sound_id), CollectionsForSound=sounds.soundsdb.CollectionsForSound(sound_id = sound_id))


@route("/New_Sound", method="POST")
def postnewsound():
    folder = request.forms.get("folder")
    upload = request.files.get("fileAjax")

    os.makedirs(f"sounds_master/{folder}/", exist_ok=True)
    newname = f"{folder}/{upload.filename}"
    upload.save(f"sounds_master/{newname}")
    new_sound_id = sounds.soundsdb.new_sound(newname)
    sounds.soundsdb.reprocess(new_sound_id)
    broca.thread.queue_sound(
        sound=sounds.soundsdb.get_sound(sound_id=new_sound_id),
        play_sleeping=True,
        play_ignore_speaking=True,
        play_no_wait=True,
        priority=10,
    )
    return "coolthxbai"


@route("/ShushPleaseHoney", method="POST")
def postshushpleasehoney():
    state = request.forms.get("state")
    if state == "on":
        log.main.info("Shushed On")
        SHARED_STATE.shush_please_honey = True
    elif state == "off":
        log.main.info("Shushed Off")
        SHARED_STATE.shush_please_honey = False
    return "done"


@route("/Delete_Sound", method="POST")
def postdelete_sound():
    sound_id = request.forms.get("sound_id")
    sounds.soundsdb.del_sound(sound_id=sound_id)
    return "executed"


@route("/BaseVolChange", method="POST")
def postbasevolchange():
    sound_id = request.forms.get("sound_id")
    volume = request.forms.get("volume")
    log.main.info("Base Volume Change: %s (new volume %s)", sound_id, volume)
    sounds.soundsdb.update(sound_id=sound_id, base_volume_adjust=volume)
    sounds.soundsdb.reprocess(sound_id=sound_id)
    broca.thread.queue_sound(
        sound=sounds.soundsdb.get_sound(sound_id=sound_id),
        play_sleeping=True,
        play_ignore_speaking=True,
        play_no_wait=True,
        priority=10,
    )
    return "done"


@route("/ProximityVolChange", method="POST")
def postproximityvolchange():
    sound_id = request.forms.get("sound_id")
    volume = request.forms.get("volume")
    log.main.info("Proximity Volume Change: %s (new volume %s)", sound_id, volume)
    sounds.soundsdb.update(sound_id=sound_id, proximity_volume_adjust=volume)
    return "done"


@route("/IntensityChange", method="POST")
def postintensitychange():
    sound_id = request.forms.get("sound_id")
    intensity = request.forms.get("intensity")
    log.main.info("Intensity change: %s (new intensity %s)", sound_id, intensity)
    sounds.soundsdb.update(sound_id=sound_id, intensity=intensity)
    return "done"


@route("/CutenessChange", method="POST")
def postcutenesschange():
    sound_id = request.forms.get("sound_id")
    cuteness = request.forms.get("cuteness")
    log.main.info("Cuteness change: %s (new cuteness %s)", sound_id, cuteness)
    sounds.soundsdb.update(sound_id=sound_id, cuteness=cuteness)
    return "done"


@route("/TempoRangeChange", method="POST")
def posttemporangechange():
    sound_id = request.forms.get("sound_id")
    tempo_range = request.forms.get("tempo_range")
    log.main.info("Tempo Range change: %s (new range %s)", sound_id, tempo_range)
    sounds.soundsdb.update(sound_id=sound_id, tempo_range=tempo_range)
    sounds.soundsdb.reprocess(sound_id=sound_id)
    return "done"


@route("/ReplayWaitChange", method="POST")
def postreplaywaitchange():
    sound_id = request.forms.get("sound_id")
    replay_wait = request.forms.get("replay_wait")
    log.main.info("Replay Wait change: %s (new wait %s)", sound_id, replay_wait)
    sounds.soundsdb.update(sound_id=sound_id, replay_wait=replay_wait)
    return "done"


@route("/CollectionUpdate", method="POST")
def postcollectionupdate():
    sound_id = request.forms.get("sound_id")
    collectionname = request.forms.get("collectionname")
    if request.forms.get("collectionstate") == "true":
        collectionstate = True
    else:
        collectionstate = False
    log.main.info(
        "Sound ID: %s Collection name: %s State: %s",
        sound_id,
        collectionname,
        collectionstate,
    )
    sounds.soundsdb.collection_update(
        sound_id=sound_id, collection_name=collectionname, state=collectionstate
    )
    return "done"


@route("/RecordingStart", method="POST")
def postrecordingstart():
    # post_data_split = post_data.split(',')
    # SpeakingDistance = post_data_split[0]
    # Training_Word = post_data_split[1]
    # if SpeakingDistance == 'close' or SpeakingDistance == 'mid' or SpeakingDistance == 'far':
    #     pass
    # else:
    #     SpeakingDistance = 'undefined'
    # # SHARED_STATE.ShushPleaseHoney = True
    # Thread_Wernicke.StartRecording(SpeakingDistance, Training_Word)
    # self.TrainingWordsDel(Training_Word)
    # log.wernicke.info('Started record: SpeakingDistance: %s Training_Word: %s', SpeakingDistance, Training_Word)
    return "done"


@route("/RecordingStop", method="POST")
def postrecordingstop():
    # Thread_Script_Sleep.EvaluateWakefulness()
    # SHARED_STATE.ShushPleaseHoney = False
    # Thread_Wernicke.StopRecording()
    # breath.thread.QueueSound(FromCollection='thanks')
    # log.wernicke.info('Stopped record')
    return "done"


# @route('/wernicke/words/<words>')
# def wernicke_words(words):

#     # pass the incoming words to the locus of word control
#     conversate.thread.Words(words)
#     return 'OK'


@route("/wernicke/hello", method="POST")
def wernicke_hello():
    server_name = request.forms.get("server_name")
    server_host = request.forms.get("server_host")
    server_rating = request.forms.get("server_rating")
    wernicke.thread.audio_server_update({"server_name": server_name, "server_host": server_host, "server_rating": int(server_rating)})
    return "OK"


@route("/wernicke/processing", method="POST")
def wernicke_onoff():
    onoff = request.forms.get("onoff")

    if onoff == "on":
        wernicke.thread.audio_processing_start()
        return "OK"

    elif onoff == "off":
        wernicke.thread.audio_processing_stop()
        return "OK"

    else:
        return "WUT"


@route("/brain_op", method="POST")
def brain_op():
    operation = request.forms.get("op")

    if operation == "stop":
        os.system("systemctl stop christine.service")
        return "OK"

    elif operation == "restart":
        os.system("systemctl restart christine.service")
        return "OK"

    else:
        return "WUT"


@route("/pi_op", method="POST")
def pi_op():
    operation = request.forms.get("op")

    if operation == "reboot":
        os.system("reboot")
        return "OK"

    elif operation == "poweroff":
        os.system("poweroff")
        return "OK"

    else:
        return "WUT"


@route("/logmark", method="POST")
def log_mark():
    msg = request.forms.get("msg")

    if len(msg) < 100:
        log.main.critical(msg)
        return "OK"

    else:
        return "WTF"


@route("/gotosleep", method="POST")
def sleep_now_bitch():
    sleep.thread.wake_up(-1000000.0)
    return "JEEZ_SORRY_OK"


@route("/status/set/<var>", method="POST")
def setvar(var):
    if var in dir(SHARED_STATE):
        if isinstance(getattr(SHARED_STATE, var), float):
            try:
                setattr(SHARED_STATE, var, float(request.forms.get("value")))
            except ValueError:
                return "FAIL"

        elif isinstance(getattr(SHARED_STATE, var), int):
            try:
                setattr(SHARED_STATE, var, int(request.forms.get("value")))
            except ValueError:
                return "FAIL"

        elif isinstance(getattr(SHARED_STATE, var), bool):
            if request.forms.get("value") == "True":
                setattr(SHARED_STATE, var, True)
            elif request.forms.get("value") == "False":
                setattr(SHARED_STATE, var, False)

        return "OK"

    else:
        return "WUT"


@route("/status/get/<var>", method="POST")
def getvar(var):
    if var in dir(SHARED_STATE):
        return str(getattr(SHARED_STATE, var))

    else:
        return "WUT"


# run(host='0.0.0.0', port=80, debug=True)
# run the server in a thread, otherwise it blocks here and prevents everything else from happening
threading.Thread(
    target=run, daemon=True, name="httpserver", kwargs=dict(host="0.0.0.0", port=80)
).start()

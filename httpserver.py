import os
import threading
from bottle import TEMPLATE_PATH, route, run, template, redirect, request, response, abort, static_file, debug
import json

import log
import status
import sounds
import breath
import sleep
import wernicke
import conversate

debug(True)

TEMPLATE_PATH.append('./httpserver/')

@route('/')
def index():
    return template('root')


@route('/<filename:re:.*\.js>')
def send_js(filename):
    return static_file(filename, root='./httpserver/', mimetype='application/javascript')
@route('/<filename:re:.*\.html>')
def send_html(filename):
    return static_file(filename, root='./httpserver/', mimetype='text/html')
@route('/<filename:re:.*\.txt>')
def send_txt(filename):
    return static_file(filename, root='./httpserver/', mimetype='text/plain')
@route('/<filename:re:.*\.ico>')
def send_ico(filename):
    return static_file(filename, root='./httpserver/', mimetype='image/x-icon')
@route('/<filename:re:.*\.css>')
def send_css(filename):
    return static_file(filename, root='./httpserver/', mimetype='text/css')


@route('/status')
def getstatus():
    return template('status', status=status)
@route('/control')
def getcontrol():
    return template('control')
@route('/sounds')
def getsounds():
    return template('sounds', sounds=sounds)
@route('/collections')
def getcollections():
    return template('collections', sounds=sounds)
@route('/upload')
def getupload():
    return template('upload')

@route('/Honey_Say', method='POST')
def posthoneysay():
    sound_id = request.forms.get('sound_id')
    breath.thread.QueueSound(Sound=sounds.soundsdb.GetSound(sound_id = sound_id), PlayWhenSleeping=True, IgnoreSpeaking=True, CutAllSoundAndPlay=True, Priority=10)
    log.web.debug(f'Honey Say Request: {sound_id}')
    return 'OK'


# @route('/Sound_Detail', method='POST')
# def postsounddetail():
#     sound_id = request.forms.get('sound_id')
#     return template('sound_detail', Sound=sounds.soundsdb.GetSound(sound_id = sound_id), CollectionsForSound=sounds.soundsdb.CollectionsForSound(sound_id = sound_id))


@route('/New_Sound', method='POST')
def postnewsound():
    folder = request.forms.get('folder')
    upload = request.files.get('fileAjax')

    os.makedirs(f'sounds_master/{folder}/', exist_ok=True)
    newname = f'{folder}/{upload.filename}'
    upload.save(f'sounds_master/{newname}')
    new_sound_id = sounds.soundsdb.NewSound(newname)
    sounds.soundsdb.Reprocess(new_sound_id)
    breath.thread.QueueSound(Sound=sounds.soundsdb.GetSound(sound_id = new_sound_id), PlayWhenSleeping=True, IgnoreSpeaking=True, CutAllSoundAndPlay=True, Priority=10)
    return 'coolthxbai'


@route('/ShushPleaseHoney', method='POST')
def postshushpleasehoney():
    state = request.forms.get('state')
    if state == 'on':
        log.main.info('Shushed On')
        status.ShushPleaseHoney = True
    elif state == 'off':
        log.main.info('Shushed Off')
        status.ShushPleaseHoney = False
    return 'done'

@route('/Delete_Sound', method='POST')
def postdelete_sound():
    sound_id = request.forms.get('sound_id')
    sounds.soundsdb.DelSound(sound_id = sound_id)
    return 'executed'

@route('/BaseVolChange', method='POST')
def postbasevolchange():
    sound_id = request.forms.get('sound_id')
    volume = request.forms.get('volume')
    log.main.info(f'Base Volume Change: {sound_id} (new volume {volume})')
    sounds.soundsdb.Update(sound_id = sound_id, base_volume_adjust = volume)
    sounds.soundsdb.Reprocess(sound_id = sound_id)
    breath.thread.QueueSound(Sound=sounds.soundsdb.GetSound(sound_id = sound_id), PlayWhenSleeping=True, IgnoreSpeaking=True, CutAllSoundAndPlay=True, Priority=10)
    return 'done'

@route('/ProximityVolChange', method='POST')
def postproximityvolchange():
    sound_id = request.forms.get('sound_id')
    volume = request.forms.get('volume')
    log.main.info(f'Proximity Volume Change: {sound_id} (new volume {volume})')
    sounds.soundsdb.Update(sound_id = sound_id, proximity_volume_adjust = volume)
    return 'done'

@route('/IntensityChange', method='POST')
def postintensitychange():
    sound_id = request.forms.get('sound_id')
    intensity = request.forms.get('intensity')
    log.main.info(f'Intensity change: {sound_id} (new intensity {intensity})')
    sounds.soundsdb.Update(sound_id = sound_id, intensity = intensity)
    return 'done'

@route('/CutenessChange', method='POST')
def postcutenesschange():
    sound_id = request.forms.get('sound_id')
    cuteness = request.forms.get('cuteness')
    log.main.info(f'Cuteness change: {sound_id} (new cuteness {cuteness})')
    sounds.soundsdb.Update(sound_id = sound_id, cuteness = cuteness)
    return 'done'

@route('/TempoRangeChange', method='POST')
def posttemporangechange():
    sound_id = request.forms.get('sound_id')
    tempo_range = request.forms.get('tempo_range')
    log.main.info(f'Tempo Range change: {sound_id} (new range {tempo_range})')
    sounds.soundsdb.Update(sound_id = sound_id, tempo_range = tempo_range)
    sounds.soundsdb.Reprocess(sound_id = sound_id)
    return 'done'

@route('/ReplayWaitChange', method='POST')
def postreplaywaitchange():
    sound_id = request.forms.get('sound_id')
    replay_wait = request.forms.get('replay_wait')
    log.main.info(f'Replay Wait change: {sound_id} (new wait {replay_wait})')
    sounds.soundsdb.Update(sound_id = sound_id, replay_wait = replay_wait)
    return 'done'

@route('/CollectionUpdate', method='POST')
def postcollectionupdate():
    sound_id = request.forms.get('sound_id')
    collectionname = request.forms.get('collectionname')
    if request.forms.get('collectionstate') == 'true':
        collectionstate = True
    else:
        collectionstate = False
    log.main.info(f'Sound ID: {sound_id} Collection name: {collectionname} State: {collectionstate}')
    sounds.soundsdb.CollectionUpdate(sound_id = sound_id, collection_name = collectionname, state = collectionstate)
    return 'done'

@route('/RecordingStart', method='POST')
def postrecordingstart():
    # post_data_split = post_data.split(',')
    # SpeakingDistance = post_data_split[0]
    # Training_Word = post_data_split[1]
    # if SpeakingDistance == 'close' or SpeakingDistance == 'mid' or SpeakingDistance == 'far':
    #     pass
    # else:
    #     SpeakingDistance = 'undefined'
    # # status.ShushPleaseHoney = True
    # Thread_Wernicke.StartRecording(SpeakingDistance, Training_Word)
    # self.TrainingWordsDel(Training_Word)
    # log.wernicke.info('Started record: SpeakingDistance: %s Training_Word: %s', SpeakingDistance, Training_Word)
    return 'done'

@route('/RecordingStop', method='POST')
def postrecordingstop():
    # Thread_Script_Sleep.EvaluateWakefulness()
    # status.ShushPleaseHoney = False
    # Thread_Wernicke.StopRecording()
    # breath.thread.QueueSound(FromCollection='thanks')
    # log.wernicke.info('Stopped record')
    return 'done'


@route('/wernicke/words/<words>')
def wernicke_words(words):

    # pass the incoming words to the locus of word control
    conversate.thread.Words(words)
    return 'OK'


@route('/wernicke/processing', method='POST')
def wernicke_onoff():

    onoff = request.forms.get('onoff')

    if onoff == 'on':

        wernicke.thread.StartProcessing()
        return 'OK'

    elif onoff == 'off':

        wernicke.thread.StopProcessing()
        return 'OK'

    else:

        return 'WUT'


@route('/brain_op', method='POST')
def brain_op():

    op = request.forms.get('op')

    if op == 'stop':
        os.system('systemctl stop christine.service')
        return 'OK'

    elif op == 'restart':
        os.system('systemctl restart christine.service')
        return 'OK'

    else:
        return 'WUT'

@route('/pi_op', method='POST')
def pi_op():

    op = request.forms.get('op')

    if op == 'reboot':
        os.system('reboot')
        return 'OK'

    elif op == 'poweroff':
        os.system('poweroff')
        return 'OK'

    else:
        return 'WUT'

@route('/logmark', method='POST')
def log_mark():

    msg = request.forms.get('msg')

    if len(msg) < 100:
        log.main.critical(msg)
        return 'OK'

    else:
        return 'WTF'

@route('/gotosleep', method='POST')
def sleep_now_bitch():

    sleep.thread.WakeUpABit(-1000000.0)
    return 'JEEZ_SORRY_OK'


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
threading.Thread(target=run, daemon=True, name='httpserver', kwargs=dict(host='0.0.0.0', port=80)).start()

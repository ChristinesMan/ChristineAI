"""
Main script that starts everything else
"""
import time
import log

# pylint: disable=unused-import,wrong-import-position
log.main.info("Script started")
from status import SHARED_STATE
import cputemp
import battery
import gyro
import sounds
import broca
import sleep
import light
import vagina
import wernicke
import httpserver
import touch
import horny
import iloveyou
import sex
import killsignal
import behaviour_conductor

if __name__ == "__main__":

    # time.sleep(5)
    # SHARED_STATE.ShushPleaseHoney = False

    # for temp data collection
    # SHARED_STATE.ShushPleaseHoney = True
    # time.sleep(15)
    # wernicke.thread.StopProcessing()

    # for Sound in sounds.soundsdb.All():
    #     SoundId = Sound['id']
    #     SoundName = Sound['name']

    #     if 'breathe_' not in SoundName:
    #         log.main.debug(f'Queuing {SoundName}')
    #         breath.thread.QueueSound(Sound = Sound, Priority = 9, PlayWhenSleeping = True, IgnoreSpeaking = True)
    #         time.sleep(5)

    # handle getting killed gracefully
    killer = killsignal.GracefulKiller()

    # wait here until a kill signal comes in
    while not killer.kill_now:
        time.sleep(2)

    log.main.info("Caught kill signal")

    # all the threads monitor this variable and try to shutdown
    SHARED_STATE.please_shut_down = True

    # wait a bit to allow graceful shutdown
    time.sleep(2)

    # try to shutdown threads
    # doesn't work anyway
    # cputemp.thread.shutdown()
    # cputemp.thread.join()
    # battery.thread.shutdown()
    # battery.thread.join()
    # status.thread.shutdown()
    # status.thread.join()
    # iloveyou.thread.shutdown()
    # iloveyou.thread.join()

    # this is supposed to finish off any daemon threads that may be left over
    # whatever
    # sys.exit()

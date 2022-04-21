import os
import sys
import time

import log
log.main.info('Script started')
log.main.debug('Import: status')
import status
log.main.debug('Import: cputemp')
import cputemp
log.main.debug('Import: battery')
import battery
log.main.debug('Import: gyro')
import gyro
log.main.debug('Import: sounds')
import sounds
log.main.debug('Import: breath')
import breath
log.main.debug('Import: iloveyou')
import iloveyou
log.main.debug('Import: sleep')
import sleep
log.main.debug('Import: light')
import light
log.main.debug('Import: wernicke')
import wernicke
log.main.debug('Import: conversate')
import conversate
log.main.debug('Import: httpserver')
import httpserver
log.main.debug('Import: touch')
import touch

# To be reinserted later, 
# and perhaps withdrawn and reinserted a lot
# log.main.debug('Import: sex')
# import sex

log.main.debug('Import: killsignal')
import killsignal

if __name__ == "__main__":

    time.sleep(5)
    status.ShushPleaseHoney = False


    # for temp data collection
    # status.ShushPleaseHoney = True
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

    log.main.info('Caught kill signal')

    # all the threads monitor this variable and try to shutdown
    status.PleaseShutdown = True

    # wait a bit to allow graceful shutdown
    time.sleep(2)

    # try to shutdown threads
    cputemp.thread.shutdown()
    cputemp.thread.join()
    battery.thread.shutdown()
    battery.thread.join()
    status.thread.shutdown()
    status.thread.join()
    iloveyou.thread.shutdown()
    iloveyou.thread.join()

    # this is supposed to finish off any daemon threads that may be left over
    sys.exit()

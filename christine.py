import os
import time

import log
import status
import cputemp
import battery
import gyro
import sounds
import breath
import iloveyou
import sleep
import light
import wernicke
import conversate
import httpserver

# To be reinserted later, 
# and perhaps withdrawn and reinserted a lot
# import touch
# import sex

import killsignal

if __name__ == "__main__":

    # We were here
    log.main.info('Script started')

    # handle getting killed gracefully
    killer = killsignal.GracefulKiller()

    # wait here until a kill signal comes in
    while not killer.kill_now:
        time.sleep(2)

    log.main.info('Caught kill signal')

    status.thread.exit()
    gyro.thread.exit()
    cputemp.thread.exit()
    battery.thread.exit()
    sleep.thread.exit()
    wernicke.thread.exit()

    time.sleep(3)
    os._exit()
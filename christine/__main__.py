"""
Main script that starts everything else
"""
# pylint: disable=unused-import,wrong-import-position

import time
import multiprocessing

from christine import log
from christine.database import database
from christine.status import STATE
from christine.config import CONFIG
from christine.broca import broca
from christine.wernicke import wernicke

# DIRECT BROCA-WERNICKE COORDINATION: Shared memory for microsecond-level audio control
# This bypasses the main thread entirely to prevent delays
# 0 = wernicke active (can process audio)
# 1 = wernicke paused (broca audio playing)
AUDIO_COORDINATION = multiprocessing.Value('i', 0)
log.main.info("Audio coordination shared memory initialized")

# Inject shared memory into broca and wernicke before starting them later
log.main.info("Injecting shared memory into broca and wernicke")
broca.audio_coordination = AUDIO_COORDINATION
wernicke.audio_coordination = AUDIO_COORDINATION

# Start broca and wernicke threads first thing so that all the other imports below
# don't wind up in the subprocesses and use lots of memory
for thread in [
    broca,
    wernicke,
]:
    time.sleep(4)
    log.main.info('Starting %s', thread.name)
    thread.start()
time.sleep(2)

from christine.vagina import vagina
from christine.parietal_lobe import parietal_lobe
from christine.prefrontal_cortex import prefrontal_cortex
from christine.light import light
from christine.cputemp import cputemp
from christine.gyro import gyro
from christine.sleep import sleep
from christine.touch import touch
from christine.horny import horny
from christine.sex import sex
from christine.httpserver import httpserver
from christine.cleaner import cleaner
from christine.killsignal import GracefulKiller

# for the modules above that are background threads, call their start() methods one at a time
for thread in [
    STATE,
    cleaner,
    cputemp,
    sleep,
    parietal_lobe,
    prefrontal_cortex,
    vagina,
    httpserver,
    horny,
    sex,
    gyro,
]:
    time.sleep(2)
    log.main.info('Starting %s', thread.name)
    thread.start()

# handle getting killed gracefully
killer = GracefulKiller()

# wait here until a kill signal comes in
while not killer.kill_now:
    time.sleep(2)

log.main.info("Caught kill signal")

# all the threads monitor this variable and try to shutdown
STATE.please_shut_down = True

# disconnect the sqlite db because around this time we tend to get kill nined
database.disconnect()

# wait a bit to allow graceful shutdown
time.sleep(4)

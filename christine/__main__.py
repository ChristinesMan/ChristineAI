"""
Main script that starts everything else
"""
# pylint: disable=unused-import,wrong-import-position

import time

from christine import log
from christine.database import database
from christine.sounds import sounds_db
from christine.status import STATE
from christine.config import CONFIG
from christine.broca import broca
from christine.parietal_lobe import parietal_lobe
from christine.wernicke import wernicke
from christine.light import light
from christine.cputemp import cputemp
from christine.gyro import gyro
from christine.sleep import sleep
from christine.vagina import vagina
from christine.touch import touch
from christine.horny import horny
from christine.sex import sex
from christine.cleaner import cleaner
from christine.server_discovery import servers
from christine.killsignal import GracefulKiller

log.main.info("Script started")

# for the modules above that are background threads, call their start() methods one at a time
for thread in [
    STATE,
    broca,
    cleaner,
    cputemp,
    sleep,
    parietal_lobe,
    vagina,
    horny,
    wernicke,
    sex,
    gyro,
    servers,
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

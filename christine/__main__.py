"""
Main script that starts everything else
"""
# pylint: disable=unused-import,wrong-import-position

import time

from christine import log
from christine import database
from christine import sounds
from christine.status import SHARED_STATE
from christine import cputemp
from christine import gyro
from christine import broca
from christine import sleep
from christine import light
from christine import vagina
from christine import wernicke
from christine import parietal_lobe
from christine import httpserver
from christine import touch
from christine import horny
from christine import sex
from christine import killsignal
from christine import behaviour_conductor

log.main.info("Script started")

# handle getting killed gracefully
killer = killsignal.GracefulKiller()

# wait here until a kill signal comes in
while not killer.kill_now:
    time.sleep(2)

log.main.info("Caught kill signal")

# all the threads monitor this variable and try to shutdown
SHARED_STATE.please_shut_down = True

# disconnect the sqlite db because around this time we tend to get kill nined
database.conn.disconnect()

# wait a bit to allow graceful shutdown
time.sleep(2)

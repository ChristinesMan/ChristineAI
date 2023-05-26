"""
Handles cuddles I guess
"""
import time
import threading

import log
from status import SHARED_STATE


class Cuddles(threading.Thread):
    """
    when proximity is real close, we want to start a cycle of saying cuddle-approapriate stuff
    """

    name = "Cuddles"

    def __init__(self):
        threading.Thread.__init__(self)

        # are we currently cuddling?
        self.cuddle_mode_on = False

        # how long to sleep between iterations in seconds
        self.sleep_seconds = 5

    def run(self):
        log.cuddles.debug("Thread started.")

        while True:
            # graceful shutdown
            if SHARED_STATE.please_shut_down:
                break

            # if self.CuddleModeOn == True:

            time.sleep(self.sleep_seconds)


# Instantiate and start the thread
thread = Cuddles()
thread.daemon = True
thread.start()

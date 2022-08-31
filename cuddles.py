import time
import random
import threading
import numpy as np

import log
import status
import breath
# import sleep

# when proximity is real close, we want to start a cycle of saying cuddle-approapriate stuff
class Cuddles(threading.Thread):

    name = 'Cuddles'

    def __init__ (self):

        threading.Thread.__init__(self)

        # are we currently cuddling? 
        self.CuddleModeOn = False

        # how long to sleep between iterations in seconds
        self.SleepSeconds = 5

    def run(self):
        log.cuddles.debug('Thread started.')

        try:

            while True:

                # graceful shutdown
                if status.PleaseShutdown:
                    break

                # if self.CuddleModeOn == True:


                time.sleep(self.SleepSeconds)


        # log exception in the main.log
        except Exception as e:
            log.main.error('Thread died. {0} {1} {2}'.format(e.__class__, e, log.format_tb(e.__traceback__)))


# Instantiate and start the thread
thread = Cuddles()
thread.daemon = True
thread.start()

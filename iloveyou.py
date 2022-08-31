import ctypes
import time
import threading
import random
import numpy as np

import log
import status
import breath

# When touched or spoken to, she becomes more likely to say something nice
class I_Love_You(threading.Thread):
    name = 'I_Love_You'

    def __init__ (self):
        threading.Thread.__init__(self)
    
        # save the current time since she/he last dropped the bomb, in seconds. 
        self.NextMakeOutSoundsTime = time.time()

    def run(self):

        try:

            while True:

                # Randomly say cute things
                if status.ShushPleaseHoney == False and time.time() > self.NextMakeOutSoundsTime and status.ChanceToSpeak > random.random():
                    self.NextMakeOutSoundsTime = time.time() + 10 + int(600*random.random())
                    status.ChanceToSpeak = 0.0
                    breath.thread.QueueSound(FromCollection='loving', Priority=3)

                time.sleep(5)

        # log exception in the main.log
        except Exception as e:
            log.main.error('Thread died. {0} {1} {2}'.format(e.__class__, e, log.format_tb(e.__traceback__)))

# Instantiate and start the thread
thread = I_Love_You()
thread.daemon = True
thread.start()

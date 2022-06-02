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
                log.sound.debug('ChanceToSpeak = %.2f', status.ChanceToSpeak)
                status.ChanceToSpeak -= 0.01

                # Can't go past 0 or past 1
                status.ChanceToSpeak = float(np.clip(status.ChanceToSpeak, 0.0, 1.0))

                time.sleep(5)

        # log exception in the main.log
        except Exception as e:
            log.main.error('Thread died. {0} {1} {2}'.format(e.__class__, e, log.format_tb(e.__traceback__)))

    # https://www.geeksforgeeks.org/python-different-ways-to-kill-a-thread/
    # it's a little rediculous how difficult thread killing is
    def get_id(self):
 
        # returns id of the respective thread
        if hasattr(self, '_thread_id'):
            return self._thread_id
        for id, thread in threading._active.items():
            if thread is self:
                return id
  
    def shutdown(self):
        thread_id = self.get_id()
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id,
              ctypes.py_object(SystemExit))
        if res > 1:
            ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, 0)
            log.main.warning('Exception raise failure')

# Instantiate and start the thread
thread = I_Love_You()
thread.daemon = True
thread.start()

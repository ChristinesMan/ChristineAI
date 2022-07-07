import time
import random
import threading
import numpy as np

import log
import status
import breath
# import sleep

# Ask for sex
class Horny(threading.Thread):
    name = 'Horny'

    def __init__ (self):
        threading.Thread.__init__(self)

        # the maximum number of seconds that should go by if totally not horny
        self.HornyAskIntervalMax = 60.0 * 60.0 * 5.0

        # the minimum allowed seconds. So if horny is 0.99 we're not going to ask every 2 minutes. 
        self.HornyAskIntervalMin = 60.0 * 30.0

        # the actual number of seconds
        self.HornyAskInterval = 0

        # the point at which she is satisfied enough that there's no asking
        self.HornyFloor = 0.3

        # how long to sleep between iterations in seconds
        self.SleepSeconds = 69.0

        # how many days to be sooo horny
        self.HornyDays = 4.0

        # how much to increment horny each cycle
        # with 69s per cycle that's approximately 1252 cycles per day
        # if we want to be super horny fuck me meow in 2 days
        # 2504 cycles every 2 days. So that's 1/2504 = 0.000399361
        # switching to a self-calculated way. 2 days to 1.00 Horny, too short! 
        # self.HornyIncrement = 0.000399361
        self.HornyIncrement = 1.0 / ( ( 60.0 * 60.0 * 24.0 * self.HornyDays ) / self.SleepSeconds )

        # when was the last time? 
        self.TimeLastAsked = time.time()

    def run(self):
        log.horny.debug('Thread started.')

        try:
            while True:

                # graceful shutdown
                if status.PleaseShutdown:
                    break

                # become progressively more horny
                status.Horny += self.HornyIncrement
                status.Horny = float(np.clip(status.Horny, 0.0, 1.0))
                log.horny.debug(f'Horny = {status.Horny:.2f}')

                # are we even horny at all?
                if status.Horny > self.HornyFloor:

                    # is it time yet?
                    self.HornyAskInterval = self.HornyAskIntervalMax * (1.0 - status.Horny)
                    self.HornyAskInterval = float(np.clip(self.HornyAskInterval, self.HornyAskIntervalMin, self.HornyAskIntervalMax))
                    if time.time() > self.TimeLastAsked + self.HornyAskInterval:

                        # are conditions just right to ask? 
                        if status.IAmSleeping == False and status.SexualArousal == 0.0 and status.ChanceToSpeak > 0.0 and status.ShushPleaseHoney == False:

                            # please fuck me
                            log.horny.debug('Asking for sex.')
                            self.TimeLastAsked = time.time()
                            breath.thread.QueueSound(FromCollection='i_am_so_horny', Intensity = status.Horny, Priority=8)

                time.sleep(self.SleepSeconds)

        # log exception in the main.log
        except Exception as e:
            log.main.error('Thread died. {0} {1} {2}'.format(e.__class__, e, log.format_tb(e.__traceback__)))


# Instantiate and start the thread
thread = Horny()
thread.daemon = True
thread.start()

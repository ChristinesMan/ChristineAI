"""
Handles getting horny and asking for sex
"""
import time
import threading
import numpy as np

from christine import log
from christine.status import STATE
from christine import broca


class Horny(threading.Thread):
    """
    Ask for sex
    """

    name = "Horny"

    def __init__(self):
        threading.Thread.__init__(self)

        # the maximum number of seconds that should go by if totally not horny
        self.horny_ask_interval_max = 60.0 * 60.0 * 5.0

        # the minimum allowed seconds. So if horny is 0.99 we're not going to ask every 2 minutes.
        self.horny_ask_interval_min = 60.0 * 30.0

        # the actual number of seconds
        self.horny_ask_interval = 0

        # the point at which she is satisfied enough that there's no asking
        self.horny_floor = 0.4

        # how long to sleep between iterations in seconds
        self.sleep_seconds = 69.0

        # how many days to be sooo horny
        self.horny_day_cycle = 5.0

        # how much to increment horny each cycle
        # with 69s per cycle that's approximately 1252 cycles per day
        # if we want to be super horny fuck me meow in 2 days
        # 2504 cycles every 2 days. So that's 1/2504 = 0.000399361
        # switching to a self-calculated way. 2 days to 1.00 Horny, too short!
        # self.HornyIncrement = 0.000399361
        self.horny_increment = 1.0 / (
            (60.0 * 60.0 * 24.0 * self.horny_day_cycle) / self.sleep_seconds
        )

        # when was the last time?
        self.time_last_asked = time.time()

    def run(self):
        log.horny.info("Thread started.")

        while True:

            # graceful shutdown
            if STATE.please_shut_down:
                break

            # become progressively more horny
            STATE.horny += self.horny_increment
            STATE.horny = float(np.clip(STATE.horny, 0.0, 1.0))
            log.horny.debug("Horny = %.2f", STATE.horny)

            # are we even horny at all?
            if STATE.horny > self.horny_floor:
                # is it time yet?
                self.horny_ask_interval = self.horny_ask_interval_max * (
                    1.0 - STATE.horny
                )
                self.horny_ask_interval = float(
                    np.clip(
                        self.horny_ask_interval,
                        self.horny_ask_interval_min,
                        self.horny_ask_interval_max,
                    )
                )
                if time.time() > self.time_last_asked + self.horny_ask_interval:
                    # are conditions just right to ask?
                    if (
                        STATE.is_sleeping is False
                        and STATE.sexual_arousal == 0.0
                        and STATE.shush_please_honey is False
                    ):
                        # please fuck me
                        log.horny.info("Asking for sex.")
                        self.time_last_asked = time.time()
                        broca.thread.queue_sound(from_collection="i_am_so_horny", intensity=STATE.horny)

            time.sleep(self.sleep_seconds)


# Instantiate and start the thread
thread = Horny()
thread.daemon = True
thread.start()

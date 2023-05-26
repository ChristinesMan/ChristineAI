"""
Handles getting horny and asking for sex
"""
import time
import threading
import numpy as np

import log
from status import SHARED_STATE
import breath


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
        log.horny.debug("Thread started.")

        while True:
            # graceful shutdown
            if SHARED_STATE.please_shut_down:
                break

            # become progressively more horny
            SHARED_STATE.horny += self.horny_increment
            SHARED_STATE.horny = float(np.clip(SHARED_STATE.horny, 0.0, 1.0))
            log.horny.debug("Horny = %.2f", SHARED_STATE.horny)

            # are we even horny at all?
            if SHARED_STATE.horny > self.horny_floor:
                # is it time yet?
                self.horny_ask_interval = self.horny_ask_interval_max * (
                    1.0 - SHARED_STATE.horny
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
                        SHARED_STATE.is_sleeping is False
                        and SHARED_STATE.sexual_arousal == 0.0
                        and SHARED_STATE.should_speak_chance > 0.0
                        and SHARED_STATE.shush_please_honey is False
                    ):
                        # please fuck me
                        log.horny.debug("Asking for sex.")
                        self.time_last_asked = time.time()
                        breath.thread.queue_sound(
                            from_collection="i_am_so_horny",
                            intensity=SHARED_STATE.horny,
                            priority=8,
                        )

            time.sleep(self.sleep_seconds)


# Instantiate and start the thread
thread = Horny()
thread.daemon = True
thread.start()

"""
Handles getting horny. All this does is gradually get hornier and hornier.
"""
import time
import threading
import numpy as np

from christine import log
from christine.status import STATE


class Horny(threading.Thread):
    """
    Handles getting horny. All this does is gradually get hornier and hornier.
    """

    name = "Horny"

    def __init__(self):
        super().__init__(daemon=True)

        # how long to sleep between iterations in seconds
        self.sleep_seconds = 69.0

        # how many days of no sex before she is sooo horny
        self.horny_day_cycle = 7.0

        # calculate horny increment
        self.horny_increment = 1.0 / (
            (60.0 * 60.0 * 24.0 * self.horny_day_cycle) / self.sleep_seconds
        )

    def run(self):

        while True:

            try:

                # graceful shutdown
                if STATE.please_shut_down:
                    break

                # become progressively more horny
                STATE.horny += self.horny_increment
                STATE.horny = float(np.clip(STATE.horny, 0.0, 1.0))
                log.horny.debug("Horny = %.2f", STATE.horny)

                time.sleep(self.sleep_seconds)

            # log the exception but keep the thread running
            except Exception as ex:
                log.main.exception(ex)

# Instantiate
horny = Horny()

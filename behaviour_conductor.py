"""Handles the smooth transition between behaviour zones."""

import time
import threading
import log
from status import SHARED_STATE

# pylint: disable=unused-import
import behaviour_abnormal
import behaviour_cuddle

class Conductor(threading.Thread):
    """Thread to handle behaviour."""

    name = "Conductor"

    def __init__(self):
        threading.Thread.__init__(self)
        self.isDaemon = True # pylint: disable=invalid-name

    def run(self):

        while True:

            time.sleep(3)

            # every so often check that the thread is still alive
            if not SHARED_STATE.behaviour_zone.is_alive():

                # if the thread ended normally, it should have set behaviour_zone_name first
                # to signal what zone is next
                if SHARED_STATE.behaviour_zone.name == SHARED_STATE.behaviour_zone_name:

                    log.main.error("The thread was dead and failed to pass the ball. Game over man! Game over!")
                    return

                else:

                    # instantiate and start the new zone thread
                    # it is likely there is a better way to do this
                    SHARED_STATE.behaviour_zone = globals()[f"behaviour_{SHARED_STATE.behaviour_zone_name}"].Behaviour()
                    SHARED_STATE.behaviour_zone.start()

                    log.behaviour.info("Passed to %s", SHARED_STATE.behaviour_zone_name)

# instantiate and start thread
thread = Conductor()
thread.start()

# Deep sleep
# Woke up in the night
# Starting to wake in the morning
# Morning awake
# Morning cuddle
# Morning horny
# Morning sex
# Morning aftersex
# Awake in bed
# Awake in chair
# Tired
# Bedtime in bed
# Sleepy
# Sleepy cuddle
# Sleepy horny
# Sleepy sex
# Sleepy aftersex
# Falling asleep

# Being carried?

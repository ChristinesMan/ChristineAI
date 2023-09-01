"""
Handles saying I love you
"""
import time
import threading
import random

# import log
from status import SHARED_STATE
import broca


class ILoveYou(threading.Thread):
    """
    When touched or spoken to, she becomes more likely to say something nice
    """

    name = "I_Love_You"

    def __init__(self):
        threading.Thread.__init__(self)

        # save the current time since she/he last dropped the L-bomb, in seconds.
        self.next_loving_time = time.time()

    def run(self):

        while True:
            # Randomly say cute things
            if (
                SHARED_STATE.shush_please_honey is False
                and time.time() > self.next_loving_time
                and SHARED_STATE.should_speak_chance > random.random()
            ):
                self.next_loving_time = (
                    time.time() + 10 + int(600 * random.random())
                )
                SHARED_STATE.should_speak_chance = 0.0
                broca.thread.queue_sound(from_collection="loving", priority=3)

            time.sleep(5)


# Instantiate and start the thread
thread = ILoveYou()
thread.daemon = True
thread.start()

"""The behaviour when you're holding me, and I'm holding you."""

import time
import random
import threading

import log
from status import SHARED_STATE
import broca
import sleep
# pylint: disable=wildcard-import,unused-wildcard-import
from behaviour_ree import *


class Behaviour(threading.Thread):
    """Thread to handle normal behaviour, from a certain point of view."""

    name = "cuddle"

    def __init__(self):
        threading.Thread.__init__(self)
        self.isDaemon = True # pylint: disable=invalid-name

        # this variable is used to pass gracefully to the next behaviour zone
        self.next_behaviour = None

        # save the current time since she/he last dropped the L-bomb, in seconds.
        self.next_loving_time = time.time()

    def run(self):
        while True:
            time.sleep(2)

            if self.next_behaviour is not None:
                SHARED_STATE.behaviour_zone_name = self.next_behaviour
                return

            if (
                time.time() > self.next_loving_time
                and SHARED_STATE.should_speak_chance > random.random()
            ):
                self.next_loving_time = (
                    time.time() + 10 + int(600 * random.random())
                )
                SHARED_STATE.should_speak_chance = 0.0
                broca.thread.queue_sound(from_collection="loving", priority=3)


    def notify_words(self, words: str):
        """When words are spoken and processed, they should end up here."""

        log.behaviour.info("Heard: %s", words)

        if re_wake_up.search(words):
            sleep.thread.wake_up(0.2)
            broca.thread.queue_sound(
                from_collection="uh_huh",
                play_no_wait=True,
                priority=7,
                play_sleeping=True,
            )

        elif re_hear_me.search(words):
            sleep.thread.wake_up(0.2)
            broca.thread.queue_sound(
                from_collection="yes", play_no_wait=True, priority=7
            )

        elif re_ruawake.search(words):
            if SHARED_STATE.is_sleeping is False:
                broca.thread.queue_sound(
                    from_collection="yes", play_no_wait=True, priority=7
                )
            else:
                broca.thread.queue_sound(
                    from_collection="no", play_no_wait=True, priority=7
                )

        elif re_rusleeping.search(words):
            if SHARED_STATE.is_sleeping is True:
                broca.thread.queue_sound(
                    from_collection="yes", play_no_wait=True, priority=7
                )
            else:
                broca.thread.queue_sound(
                    from_collection="no", play_no_wait=True, priority=7
                )

        sleep.thread.wake_up(0.008)

        if (
            SHARED_STATE.shush_please_honey is False
            and SHARED_STATE.sexual_arousal < 0.1
            and SHARED_STATE.is_sleeping is False
        ):
            if re_love.search(words):
                broca.thread.queue_sound(
                    from_collection="iloveyoutoo",
                    alt_collection="loving",
                    play_no_wait=True,
                    priority=7,
                )

            elif re_getting_up.search(words):
                self.next_behaviour = "abnormal"

            elif re_complement.search(words):
                broca.thread.queue_sound(
                    from_collection="thanks", play_no_wait=True, priority=7
                )

            elif re_sleep.search(words):
                sleep.thread.wake_up(-100.0)
                broca.thread.queue_sound(
                    from_collection="uh_huh",
                    play_no_wait=True,
                    play_sleeping=True,
                    priority=9,
                )
                broca.thread.queue_sound(
                    from_collection="goodnight",
                    play_no_wait=True,
                    play_sleeping=True,
                    priority=8,
                )

            elif re_rutired.search(words):
                if SHARED_STATE.is_tired is True:
                    broca.thread.queue_sound(
                        from_collection="yes", play_no_wait=True, priority=7
                    )
                else:
                    broca.thread.queue_sound(
                        from_collection="no", play_no_wait=True, priority=7
                    )

            elif re_ru_ok.search(words):
                if SHARED_STATE.cpu_temp >= 62:
                    broca.thread.queue_sound(
                        from_collection="no", play_no_wait=True, priority=7
                    )
                else:
                    broca.thread.queue_sound(
                        from_collection="yes", play_no_wait=True, priority=7
                    )

            elif re_ura_goof.search(words):
                broca.thread.queue_sound(
                    from_collection="laughing", play_no_wait=True, priority=7
                )

            elif re_i_want_sex.search(words):
                broca.thread.queue_sound(
                    from_collection="about_to_fuck", play_no_wait=True, priority=7
                )

            else:
                log.behaviour.debug("Unmatched: %s", words)

                SHARED_STATE.should_speak_chance += 0.04
                broca.thread.queue_sound(
                    from_collection="cuddling", priority=2, play_no_wait=True
                )

    def please_say(self, **what):
        """When some other thread wants to say something, they have to go through here."""

        log.behaviour.debug("Please say: %s", what)

        broca.thread.queue_sound(**what)

    def notify_sound_ended(self):
        """This should get called as soon as sound is finished playing."""

        log.behaviour.debug("Sound ended.")

    def notify_jostled(self):
        """When wife is feeling those bumps in the night, this gets hit."""

        log.behaviour.debug("Jostled.")

        sleep.thread.wake_up(0.04)
        SHARED_STATE.lover_proximity = (
            (SHARED_STATE.lover_proximity * 5.0) + 1.0
        ) / 6.0

        # later this needs to be moved to the sleeping behaviour zone
        broca.thread.queue_sound(
            from_collection="gotwokeup",
            play_sleeping=True,
            play_ignore_speaking=True,
            play_no_wait=True,
        )

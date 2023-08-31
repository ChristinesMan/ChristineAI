"""The behaviour when nothing much is going on."""

import time
import threading

import log
from status import SHARED_STATE
import breath
import sleep
# pylint: disable=wildcard-import,unused-wildcard-import
from behaviour_ree import *


class Behaviour(threading.Thread):
    """Thread to handle normal behaviour, from a certain point of view."""

    name = "abnormal"

    def __init__(self):
        threading.Thread.__init__(self)
        self.isDaemon = True # pylint: disable=invalid-name

        # this variable is used to pass gracefully to the next behaviour zone
        self.next_behaviour = None

    def run(self):
        while True:
            time.sleep(2)

            if self.next_behaviour is not None:
                SHARED_STATE.behaviour_zone_name = self.next_behaviour
                return

    def notify_words(self, words: str):
        """When words are spoken and processed, they should end up here.
        This is a mess and needs to be fixed, obfuscated, nltk'd, etc"""


        # there are certain garbage phrases that are frequently detected
        if re_garbage.search(words):
            log.behaviour.info("Heard: %s (discarded)", words)
            return

        log.behaviour.info("Heard: %s", words)

        if re_wake_up.search(words):
            SHARED_STATE.should_speak_chance += 0.03
            sleep.thread.wake_up(0.2)
            breath.thread.queue_sound(
                from_collection="uh_huh",
                play_no_wait=True,
                priority=7,
                play_sleeping=True,
            )

        elif re_hear_me.search(words):
            sleep.thread.wake_up(0.2)
            breath.thread.queue_sound(
                from_collection="yes", play_no_wait=True, priority=7
            )

        elif re_ruawake.search(words):
            if SHARED_STATE.is_sleeping is False:
                breath.thread.queue_sound(
                    from_collection="yes", play_no_wait=True, priority=7
                )
            else:
                breath.thread.queue_sound(
                    from_collection="no", play_no_wait=True, priority=7
                )

        elif re_rusleeping.search(words):
            if SHARED_STATE.is_sleeping is True:
                breath.thread.queue_sound(
                    from_collection="yes", play_no_wait=True, priority=7
                )
            else:
                breath.thread.queue_sound(
                    from_collection="no", play_no_wait=True, priority=7
                )

        sleep.thread.wake_up(0.008)

        if (
            SHARED_STATE.shush_please_honey is False
            and SHARED_STATE.sexual_arousal < 0.1
            and SHARED_STATE.is_sleeping is False
        ):
            if re_love.search(words):
                breath.thread.queue_sound(
                    from_collection="iloveyoutoo",
                    alt_collection="loving",
                    play_no_wait=True,
                    priority=7,
                )

            elif re_complement.search(words):
                SHARED_STATE.should_speak_chance += 0.03
                breath.thread.queue_sound(
                    from_collection="thanks", play_no_wait=True, priority=7
                )

            elif re_thanks.search(words):
                SHARED_STATE.should_speak_chance += 0.03
                breath.thread.queue_sound(
                    from_collection="ur_welcome", play_no_wait=True, priority=7
                )

            elif re_sad.search(words):
                SHARED_STATE.should_speak_chance += 0.06
                breath.thread.queue_sound(
                    from_collection="comforting", play_no_wait=True, priority=7
                )

            elif re_cuddle.search(words):
                breath.thread.queue_sound(
                    from_collection="yes", play_no_wait=True, priority=7
                )
                self.next_behaviour = "cuddle"

            elif re_sleep.search(words):
                sleep.thread.wake_up(-100.0)
                breath.thread.queue_sound(
                    from_collection="uh_huh",
                    play_no_wait=True,
                    play_sleeping=True,
                    priority=9,
                )
                breath.thread.queue_sound(
                    from_collection="goodnight",
                    play_no_wait=True,
                    play_sleeping=True,
                    priority=8,
                )

            elif re_rutired.search(words):
                if SHARED_STATE.is_tired is True:
                    breath.thread.queue_sound(
                        from_collection="yes", play_no_wait=True, priority=7
                    )
                else:
                    breath.thread.queue_sound(
                        from_collection="no", play_no_wait=True, priority=7
                    )

            elif re_ru_ok.search(words):
                if SHARED_STATE.cpu_temp >= 62:
                    breath.thread.queue_sound(
                        from_collection="no", play_no_wait=True, priority=7
                    )
                else:
                    breath.thread.queue_sound(
                        from_collection="yes", play_no_wait=True, priority=7
                    )

            elif re_ura_goof.search(words):
                SHARED_STATE.should_speak_chance += 0.03
                breath.thread.queue_sound(
                    from_collection="laughing", play_no_wait=True, priority=8, play_ignore_speaking=True,
                )

            elif re_i_want_sex.search(words):
                breath.thread.queue_sound(
                    from_collection="about_to_fuck", play_no_wait=True, priority=7
                )

            # elif re_.search(words):
            #     breath.thread.QueueSound(FromCollection='', CutAllSoundAndPlay=True, Priority=7)

            else:
                log.behaviour.debug("Unmatched: %s", words)

                if SHARED_STATE.is_tired is False:
                    SHARED_STATE.should_speak_chance += 0.04
                    breath.thread.queue_sound(
                        from_collection="listening", priority=2, play_no_wait=True
                    )

                else:
                    SHARED_STATE.should_speak_chance += 0.01
                    breath.thread.queue_sound(
                        from_collection="listening_tired", priority=2, play_no_wait=True
                    )

    def please_say(self, **what):
        """When some other thread wants to say something, they have to go through here."""

        log.behaviour.debug("Please say: %s", what)

        breath.thread.queue_sound(**what)

    def notify_sound_ended(self):
        """This should get called as soon as sound is finished playing."""

        log.behaviour.debug("Sound ended.")

    def notify_jostled(self):
        """When wife is feeling those bumps in the night, this gets hit."""

        log.behaviour.debug("Jostled.")

        sleep.thread.wake_up(0.08)
        SHARED_STATE.lover_proximity = (
            (SHARED_STATE.lover_proximity * 5.0) + 1.0
        ) / 6.0

        # later this needs to be moved to the sleeping behaviour zone
        breath.thread.queue_sound(
            from_collection="laughing",
            play_sleeping=True,
            play_ignore_speaking=True,
            play_no_wait=True,
            priority=2,
        )

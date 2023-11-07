"""The behaviour when nothing much is going on."""

import os
import time
import threading
import queue

from christine import log
from christine.status import SHARED_STATE
from christine import broca
from christine import sleep
from christine import wernicke
from christine import parietal_lobe
# pylint: disable=wildcard-import,unused-wildcard-import
from christine.behaviour_ree import *


class Behaviour(threading.Thread):
    """Thread to handle normal behaviour, from a certain point of view."""

    name = "abnormal"

    def __init__(self):
        threading.Thread.__init__(self)
        self.isDaemon = True # pylint: disable=invalid-name

        # this variable is used to pass gracefully to the next behaviour zone
        self.next_behaviour = None

        # queue up sentences to feed into broca one at a time
        self.broca_queue = queue.Queue()

        # I want to send messages to the parietal lobe when there are gyro events, but not so many messages, just one
        # so keep track of the time
        self.time_of_last_body_message = 0.0

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
            sleep.thread.wake_up(0.2)
            broca.thread.queue_sound(from_collection="uh_huh", play_no_wait=True)

        elif re_hear_me.search(words):
            sleep.thread.wake_up(0.2)
            broca.thread.queue_sound(from_collection="yes", play_no_wait=True)

        elif re_shutdown.search(words):
            broca.thread.queue_sound(from_collection="shutting_down", play_no_wait=True)
            time.sleep(4)
            os.system("poweroff")

        elif re_ruawake.search(words):
            if SHARED_STATE.is_sleeping is False:
                broca.thread.queue_sound(from_collection="yes", play_no_wait=True)
            else:
                broca.thread.queue_sound(from_collection="no", play_no_wait=True)

        elif re_rusleeping.search(words):
            if SHARED_STATE.is_sleeping is True:
                broca.thread.queue_sound(from_collection="yes", play_no_wait=True)
            else:
                broca.thread.queue_sound(from_collection="no", play_no_wait=True)

        sleep.thread.wake_up(0.008)

        if (
            SHARED_STATE.shush_please_honey is False
            and SHARED_STATE.shush_fucking is False
            and SHARED_STATE.is_sleeping is False
        ):
            # if re_love.search(words):
            #     broca.thread.queue_sound(from_collection="iloveyoutoo", alt_collection="loving", play_no_wait=True)

            # elif re_complement.search(words):
            #     SHARED_STATE.should_speak_chance += 0.03
            #     broca.thread.queue_sound(from_collection="thanks", play_no_wait=True)

            # elif re_thanks.search(words):
            #     SHARED_STATE.should_speak_chance += 0.03
            #     broca.thread.queue_sound(from_collection="ur_welcome", play_no_wait=True)

            # elif re_sad.search(words):
            #     SHARED_STATE.should_speak_chance += 0.06
            #     broca.thread.queue_sound(from_collection="comforting", play_no_wait=True)

            # elif re_cuddle.search(words):
            #     broca.thread.queue_sound(from_collection="yes", play_no_wait=True)
            #     # self.next_behaviour = "cuddle"

            if re_sleep.search(words):
                SHARED_STATE.wernicke_sleeping = True
                wernicke.thread.audio_processing_stop()
                sleep.thread.wake_up(-100.0)
                broca.thread.queue_sound(from_collection="goodnight", play_no_wait=True)

            elif re_stoplistening.search(words):
                wernicke.thread.audio_processing_stop()
                broca.thread.queue_sound(from_collection="uh_huh", play_no_wait=True)

            # elif re_rutired.search(words):
            #     if SHARED_STATE.is_tired is True:
            #         broca.thread.queue_sound(from_collection="yes", play_no_wait=True)
            #     else:
            #         broca.thread.queue_sound(from_collection="no", play_no_wait=True)

            # elif re_ru_ok.search(words):
            #     if SHARED_STATE.cpu_temp >= 67:
            #         broca.thread.queue_sound(from_collection="no", play_no_wait=True)
            #     else:
            #         broca.thread.queue_sound(from_collection="yes", play_no_wait=True)

            # elif re_ura_goof.search(words):
            #     SHARED_STATE.should_speak_chance += 0.03
            #     broca.thread.queue_sound(from_collection="laughing", play_no_wait=True)

            # elif re_i_want_sex.search(words):
            #     broca.thread.queue_sound(from_collection="about_to_fuck", play_no_wait=True)

            else:
                # log.behaviour.debug("Unmatched: %s", words)

                # if SHARED_STATE.is_tired is False:
                #     SHARED_STATE.should_speak_chance += 0.04
                #     broca.thread.queue_sound(from_collection="listening", play_no_wait=True)

                # else:
                #     SHARED_STATE.should_speak_chance += 0.01
                #     broca.thread.queue_sound(from_collection="listening_tired", play_no_wait=True)

                parietal_lobe.thread.accept_new_message(words)

    def please_say(self, text):
        """When the motherfucking badass parietal lobe with it's big honking GPUs wants to say some words, they have to go through here."""

        log.behaviour.debug("Please say: %s", text)

        # put it on the queue
        self.broca_queue.put_nowait({"type": "text", "content": text})

        # start the ball rolling if it's not already
        if broca.thread.next_sound is None:
            self.notify_sound_ended()

    def please_play_sound(self, **what):
        """When some other thread wants to play a simple sound or a random sound from a collection, they have to go through here."""

        log.behaviour.debug("Please play: %s", what)

        # put it on the queue
        self.broca_queue.put_nowait({"type": "sound", "content": what})

        # start the ball rolling if it's not already
        if broca.thread.next_sound is None:
            self.notify_sound_ended()

    def notify_sound_ended(self):
        """This should get called by broca as soon as sound is finished playing. Or, rather, when next_sound is free."""

        # log.behaviour.debug("Sound ended.")

        if self.broca_queue.qsize() > 0:
            try:
                queue_item = self.broca_queue.get_nowait()
            except queue.Empty:
                log.behaviour.warning('self.broca_queue was empty. Not supposed to happen.')

            if queue_item['type'] == "sound":
                broca.thread.queue_sound(**queue_item['content'])
            elif queue_item['type'] == "text":
                broca.thread.queue_text(queue_item['content'])

    def notify_jostled(self, magnitude: float):
        """When wife is feeling those bumps in the night, this gets hit."""

        log.behaviour.debug("Jostled. (%.2f)", magnitude)
        
        if time.time() > self.time_of_last_body_message + 60:
            parietal_lobe.thread.accept_body_internal_message("Your gyroscope has detected some significant body movement.")
            self.time_of_last_body_message = time.time()

        sleep.thread.wake_up(0.08)
        SHARED_STATE.lover_proximity = (
            (SHARED_STATE.lover_proximity * 5.0) + 1.0
        ) / 6.0

        # # later this needs to be moved to the sleeping behaviour zone
        # broca.thread.queue_sound(from_collection="laughing", play_no_wait=True)

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
            broca.thread.queue_sound(from_collection="sleepy", play_no_wait=True)

        elif re_shutdown.search(words):
            broca.thread.queue_sound(from_collection="disgust", play_no_wait=True)
            time.sleep(4)
            os.system("poweroff")

        # wake up a little bit from hearing words
        sleep.thread.wake_up(0.008)

        # send words to the LLM
        parietal_lobe.thread.accept_new_message(words)

    def please_say(self, text):
        """When the motherfucking badass parietal lobe with it's big honking GPUs wants to say some words, they have to go through here."""

        log.behaviour.debug("Please say: %s", text)

        if re_body_go_to_sleep.search(text):
            SHARED_STATE.wernicke_sleeping = True
            wernicke.thread.audio_processing_stop()
            sleep.thread.wake_up(-100.0)

        # put it on the queue
        self.broca_queue.put_nowait({"type": "text", "content": text})

        # start the ball rolling if it's not already
        if broca.thread.next_sound is None:
            self.notify_sound_ended()

    def please_play_emote(self, text):
        """Play an emote if we have a sound in the collection."""

        log.behaviour.debug("Please emote: %s", text)

        # figure out which emote
        if re_emote_laugh.search(text):
            collection = 'laughing'

        elif re_emote_grrr.search(text):
            collection = 'disgust'

        elif re_emote_yawn.search(text):
            collection = 'sleepy'

        else:
            # if it doesn't match anything known, just discard
            log.behaviour.warning('This emote matched nothing and was discarded: %s', text)
            return

        # put it on the queue
        self.broca_queue.put_nowait({"type": "sound", "collection": collection})

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
                broca.thread.queue_sound(from_collection=queue_item['collection'])
            elif queue_item['type'] == "text":
                broca.thread.queue_text(text=queue_item['content'])

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

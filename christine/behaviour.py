"""The behaviour module is a clumsy attempt to tie stuff together with some logic."""

import os
import time
import queue
import re

from christine import log
from christine.status import STATE
from christine import broca
from christine import sleep
# from christine import wernicke
from christine import parietal_lobe


class Behaviour():
    """Thread to handle normal behaviour, from a certain point of view."""

    name = "abnormal"

    def __init__(self):

        self.isDaemon = True # pylint: disable=invalid-name

        # queue up sentences to feed into broca one at a time
        self.broca_queue = queue.Queue()

        # I want to send messages to the parietal lobe when there are gyro events, but not so many messages, just one
        # so keep track of the time
        self.time_of_last_body_message = 0.0

        # the jostled levels and what messages to send LLM for each level
        self.jostle_levels = [
            {'magnitude': 0.8, 'text': 'Your gyroscope has detected a massive bump. It was so intense, your body may have fallen or been set down hard. Please ask to make sure everything is okay.'},
            {'magnitude': 0.6, 'text': 'Your gyroscope has detected a sudden, strong body movement.'},
            {'magnitude': 0.3, 'text': 'Your gyroscope has detected some significant body movement.'},
            {'magnitude': 0.15, 'text': 'Your gyroscope has detected a very gentle, slight body movement.'},
        ]

        # After a few months I hope to forget how this works
        # Fortunate I am so good at forgetting things
        # And fortunate we have LLMs now
        self.re_wake_up = re.compile(
            "wake up", flags=re.IGNORECASE
        )
        self.re_stoplistening = re.compile(
            "(shutdown|shut down|shut off|turn off|disable) your (hearing|ears)", flags=re.IGNORECASE
        )
        self.re_shutdown = re.compile(
            "(shutdown|shut down|turn off) your (brain|pie|pi)", flags=re.IGNORECASE
        )
        self.re_start_eagle_enroll = re.compile(
            "start speaker enrollment", flags=re.IGNORECASE
        )

        # emotes that show up in text from LLM
        self.re_emote_laugh = re.compile(
            r"haha|laugh|chuckle|snicker|chortle|giggle|guffaw|😆|🤣|😂|😅|😀|😃|😄|😁|🤪|😜|😝", flags=re.IGNORECASE
        )
        self.re_emote_grrr = re.compile(
            r"grrr|gasp|😠|😡|🤬|😤|🤯|🖕", flags=re.IGNORECASE
        )
        self.re_emote_yawn = re.compile(
            r"yawn|sleep|tire|😪|😴|😒|💤|😫|🥱|😑|😔|🤤", flags=re.IGNORECASE
        )

    def notify_new_speech(self, transcription: str):
        """When words are spoken from the outside world, they should end up here."""

        log.parietallobe.info("Heard: %s", transcription)
        text = transcription['text']
        speaker = transcription['speaker']

        # wake up a little bit from hearing words
        sleep.thread.wake_up(0.008)

        # test for various special phrases
        if self.re_wake_up.search(text):
            sleep.thread.wake_up(0.2)
            broca.thread.queue_sound(from_collection="sleepy", play_no_wait=True)

        elif self.re_shutdown.search(text):
            broca.thread.queue_sound(from_collection="disgust", play_no_wait=True)
            time.sleep(4)
            os.system("poweroff")

        elif self.re_stoplistening.search(text):
            parietal_lobe.thread.request_to_disable_ears(text)

        # elif self.re_start_eagle_enroll.search(text):
        #     self.please_say('Please start speaking now to build a voice profile.')
        #     wernicke.thread.start_eagle_enroll()

        else:
            # send words to the LLM
            parietal_lobe.thread.accept_new_message(text, speaker)

    def notify_body_alert(self, text: str):
        """When something goes wrong or something changes in the body, this gets called to be passed on to the LLM."""

        log.behaviour.info("Body says: %s", text)

        # send words to the LLM as a body internal message
        parietal_lobe.thread.accept_body_internal_message(text)

    def please_say(self, text):
        """When the motherfucking badass parietal lobe with it's big honking GPUs wants to say some words, they have to go through here."""

        # if STATE.parietal_lobe_blocked is True:
        #     log.behaviour.debug("Please say: %s (blocked)", text)
        #     return

        log.behaviour.debug("Please say: %s", text)

        # put it on the queue
        self.broca_queue.put_nowait({"type": "text", "content": text})

        # start the ball rolling if it's not already
        if broca.thread.next_sound is None:
            self.notify_sound_ended()

    def please_play_emote(self, text):
        """Play an emote if we have a sound in the collection."""

        # if STATE.parietal_lobe_blocked is True:
        #     log.behaviour.debug("Please emote: %s (blocked)", text)
        #     return

        log.behaviour.debug("Please emote: %s", text)

        # figure out which emote
        if self.re_emote_laugh.search(text):
            collection = 'laughing'

        elif self.re_emote_grrr.search(text):
            collection = 'disgust'

        elif self.re_emote_yawn.search(text):
            collection = 'sleepy'

        else:
            # if it doesn't match anything known, just discard, but let the caller know
            return False

        # put it on the queue
        self.broca_queue.put_nowait({"type": "sound", "collection": collection})

        # start the ball rolling if it's not already
        if broca.thread.next_sound is None:
            self.notify_sound_ended()

        # if we got this far, the emote was used. We send this back to let Parietal Lobe know to save the emote.
        return True

    def please_play_sound(self, collection):
        """Play any sound from a collection."""

        # if STATE.parietal_lobe_blocked is True:
        #     log.behaviour.debug("Please play from collection: %s (blocked)", collection)
        #     return

        log.behaviour.debug("Please play from collection: %s", collection)

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
                broca.thread.queue_sound(from_collection=queue_item['collection'], priority=10)
            elif queue_item['type'] == "text":
                broca.thread.queue_text(text=queue_item['content'])

    def notify_jostled(self):
        """When wife is feeling those bumps in the night, this gets hit."""

        # wait a sec first because the full magnitude of the jostling might still be building
        time.sleep(1)
        magnitude = STATE.jostled_level_short
        log.behaviour.info("Jostled. (%.2f)", magnitude)

        # send an approapriate alert to LLM based on the magnitude of being jostled
        time.sleep(1)
        for level in self.jostle_levels:
            if magnitude >= level['magnitude']:
                parietal_lobe.thread.accept_body_internal_message(level['text'])
                break

        # wake up a bit
        sleep.thread.wake_up(0.1)

# Instantiate the class. Call it a thread so it feels important.
thread = Behaviour()

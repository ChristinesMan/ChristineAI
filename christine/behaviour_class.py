"""An empty behaviour class for startup and intellisense purposes."""

import threading

class Behaviour(threading.Thread):
    """Thread to handle behaviour."""

    name = "Default"

    def __init__(self):
        threading.Thread.__init__(self)

    def notify_words(self, words: str):
        """When words are spoken and processed, they should end up here."""

    def please_say(self, text):
        """When the motherfucking badass parietal lobe with it's big honking GPUs wants to say some words, they have to go through here."""

    def please_play_emote(self, text):
        """Play an emote if we have a sound in the collection."""

    def notify_sound_ended(self):
        """This should get called as soon as sound is finished playing."""

    def notify_jostled(self, magnitude: float):
        """When wife is feeling those bumps in the night, this gets hit."""

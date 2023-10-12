"""An empty behaviour class for startup and intellisense purposes."""

import threading

class Behaviour(threading.Thread):
    """Thread to handle behaviour."""

    name = "Default"

    def __init__(self):
        threading.Thread.__init__(self)

    def notify_words(self, words: str):
        """When words are spoken and processed, they should end up here."""

    def please_say(self, **what):
        """When the motherfucking badass parietal lobe with it's big honking GPUs wants to say some words, they have to go through here."""

    def please_play_sound(self, **what):
        """When some other thread wants to play a simple sound or a random sound from a collection, they have to go through here."""

    def notify_sound_ended(self):
        """This should get called as soon as sound is finished playing."""

    def notify_jostled(self):
        """When wife is feeling those bumps in the night, this gets hit."""

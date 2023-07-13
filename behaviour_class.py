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
        """When some other thread wants to say something, they have to go through here."""

    def notify_sound_ended(self):
        """This should get called as soon as sound is finished playing."""

    def notify_jostled(self):
        """When wife is feeling those bumps in the night, this gets hit."""

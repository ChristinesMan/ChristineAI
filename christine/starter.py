"""A starter is a short phrase that is inserted into the prompt at the very end to get the LLM started on the right foot."""

import random

# from christine import log
from christine.status import STATE

class Starter:
    """Class to handle all the starter phrases."""

    def __init__(self):

        # These are the starters for normal conversation
        self.starters_normal = [
            "I consider what to say, if anything.\n\n",
            "I think about it and decide how to respond, or whether to stay silent.\n\n",
            "I ponder the situation and consider my response.\n\n",
            "I take a moment to think about what to say.\n\n",
            "I pause, considering my response.\n\n",
            "I take a moment to think about what I want to say.\n\n",
            "I consider my response carefully.\n\n",
            "I take a moment to think about how to respond.\n\n",
            "I pause, considering what to say, if anything.\n\n",
            "I think about what was said and decide how to respond.\n\n",
            "I take a moment to think about what was said.\n\n",
            "I consider the situation and decide how to respond.\n\n",
            "I pause to think over what was said.\n\n",
            "What did that mean? I think about it for a moment.\n\n",
            "The words hang in the air. I consider my response.\n\n",
            "I'm not sure what to say. I take a moment to think about it.\n\n",
            "Knowing what to say is difficult. I pause to think about it.\n\n",
        ]

        # Starters for when sleepy, but not falling asleep yet
        self.starters_sleepy = [
            "I'm feeling a bit sleepy. I take a moment to think about what to say.\n\n",
            "I'm feeling a bit tired. I pause to think about what to say.\n\n",
            "I'm feeling a bit drowsy. I consider my response.\n\n",
            "I'm feeling a bit sleepy. I take a moment to think about it.\n\n",
            "I'm feeling a bit tired. I pause to think about it.\n\n",
            "I'm feeling a bit drowsy. I consider my response.\n\n",
            "I'm feeling a bit sleepy. I take a moment to think about what to say.\n\n",
            "I'm feeling a bit tired. I pause to think about what to say.\n\n",
            "I'm feeling a bit drowsy. I consider my response.\n\n",
            "I'm feeling a bit sleepy. I take a moment to think about it.\n\n",
            "I'm feeling a bit tired. I pause to think about it.\n\n",
            "I'm feeling a bit drowsy. I consider my response.\n\n",
        ]

    def get(self):
        """Get a random starter phrase that is approapriate for the current state of the body and outside world."""

        # if the body is sleepy, return a sleep starter
        if STATE.is_sleepy is True:
            return random.choice(self.starters_sleepy)

        # if we're having sex, return an empty string
        if STATE.sexual_arousal > 0.01:
            return ""

        # otherwise, return a normal starter
        return random.choice(self.starters_normal)

"""This class represents one single turn of narrative, for storage and processing of conversation history."""

import time

class Narrative:
    """This class represents one single turn of narrative, for storage and processing of conversation history."""

    def __init__(self, role: str, text: str = ''):

        # the role such as system, user, or char
        self.role: str = role

        # the paragraph of text (for a text-only LLM)
        self.text: str = text

        # timestamp of when this was created
        self.timestamp: float = time.time()

    def to_dict(self) -> dict:
        """Converts the Narrative object to a dictionary."""

        return {
            "role": self.role,
            "text": self.text,
            "timestamp": self.timestamp
        }

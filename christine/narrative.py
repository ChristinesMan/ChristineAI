"""This class represents one single paragraph of narrative, for storage and processing of conversation history."""

import time
from dataclasses import dataclass, field

@dataclass
class Narrative:
    """This class represents one single paragraph of narrative, for storage and processing of conversation history."""

    # the role of this paragraph, such as system, user, or char
    role: str

    # the paragraph of text
    text: str

    # timestamp of when this was created
    timestamp: float = field(default_factory=lambda: time.time()) # pylint: disable=unnecessary-lambda

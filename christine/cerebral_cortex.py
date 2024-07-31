"""The cerebral cortex is the outer layer of the brain, which is responsible for higher brain functions such as thought, memory, and perception.
In this case, the CerebralCortex class is responsible for storing and summarizing memories, as well as recalling memories based on specific keywords."""

import os
import time
import threading
from queue import Queue
import pickle
import re
import random
from json.decoder import JSONDecodeError
import requests
import spacy
from openai import OpenAI, APIConnectionError, APITimeoutError, APIStatusError, NotFoundError, InternalServerError
from httpx import TimeoutException, RemoteProtocolError, ConnectError, HTTPStatusError

from christine import log
from christine.status import STATE
from christine.config import CONFIG
from christine.narrative import Narrative

class CerebralCortex(threading.Thread):
    """Class representing the Cerebral Cortex of the brain. The Cerebral Cortex is responsible for storing and summarizing memories."""

    name = "CerebralCortex"

    def __init__(self):
        super().__init__(daemon=True)

        # the parietal_lobe better not be using the LLM api while this is also, so we need a way to signal that
        # we will strive to process messages during times of little activity, but could still potentially conflict
        self.llm_busy = False

        # the prompt that will be used to summarize the messages
        self.prompt = "### Instruction:Summarize the above text in a single paragraph of up to five detailed sentences.\n### Response:\n"

        # The Narrative objects discarded by parietal lobe
        self.narrative_history: list[Narrative] = []

        # How to connect to the LLM api. This is from config.ini file
        self.base_url = CONFIG['parietal_lobe']['base_url']
        self.api_key = CONFIG['parietal_lobe']['api_key']

        # setup the language model api
        self.llm = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
        )

    def accept_message(self, narrative: Narrative):
        """Called by the parietal_lobe to store a discarded message for inclusion in long-term memory."""

        log.cerebral_cortex.info("Accepting narrative: %s", narrative)

        # Store the narrative
        self.narrative_history.extend(narrative)

    def summarize_messages(self):
        """Uses the messages in memory to generate a summary."""

    def recall_earlier_today(self):
        """Returns a summary of the messages from earlier today."""

    def sleep_generate_yesterday_memory(self):
        """Called by the sleep module after deep sleep to generate a summary of the messages from yesterday."""

# instantiate
cerebral_cortex = CerebralCortex()

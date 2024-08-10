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
from json import load as json_load, dump as json_dump
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

        # What's your name, carbon based unit, you ugly bag of water, infesting earth
        self.user_name = CONFIG['parietal_lobe']['user_name']

        # What's the name given to this sillicon based unit, the thinking machine, infesting the GPU
        self.char_name = CONFIG['parietal_lobe']['char_name']

        # the prompt parts. The stuff goes in the middle, like a sandwich
        self.prompt_top = f"You are {self.char_name}, a female android. {self.user_name} is your husband. There are many parts to your mind. Right now, you are processing a recent section of short-term memory into long-term memory.\n\n"
        self.prompt_bottom = "### Instruction:Summarize the above text in a single paragraph of up to five detailed sentences.\n### Response:\n"

        # paragraphs that summarize the events of up to 4 days ago and older. [0] is earlier today. [4] is 4 days ago. [5] is older
        # these should include a trailing \n\n for ease of concatenation
        self.long_term_memory: list[str] = ["", "", "", "", "", ""]

    def run(self):

        log.cerebral_cortex.debug('Starting up.')

        # load the long-term memory from file
        self.load_memories()

        while True:

            # for now just sleep, dunno what to do yet but there's going to be something, I can feel it
            time.sleep(60)

    def save_memories(self):
        """Saves self.long_term_memory to a file."""

        # save the list into the long_term_memory.json file
        with open(file='long_term_memory.json', mode='w', encoding='utf-8') as long_term_memory_file:
            json_dump(self.long_term_memory, long_term_memory_file, ensure_ascii=False, check_circular=False, indent=2)

    def load_memories(self):
        """Loads self.long_term_memory from a file."""

        try:

            # load the list from the file
            with open(file='long_term_memory.json', mode='r', encoding='utf-8') as long_term_memory_file:
                self.long_term_memory = json_load(long_term_memory_file)

        except FileNotFoundError:
            log.cerebral_cortex.warning('long_term_memory.json not found. Starting fresh.')

    def make_new_memories(self, narratives: list[Narrative]):
        """Called by the parietal_lobe to process a block of discarded messages for inclusion in short-term memory."""

        # this is a circular import, but it's necessary, mass hysteria
        # pylint: disable=import-outside-toplevel
        from christine.api_selector import llm_selector

        log.cerebral_cortex.info("Accepting narratives")

        # start the prompt sandwich
        prompt = self.prompt_top

        # add the memories so far from earlier in the day
        prompt += self.long_term_memory[0]

        # for each narrative, add it to the prompt
        for narrative in narratives:
            prompt += narrative.text + "\n\n"

        # add the bottom of the prompt sandwich
        # by the way, this is a rediculous and unsanitary way to make a sandwich
        prompt += self.prompt_bottom

    def recall_memories(self):
        """Returns all the memories from the long-term memory."""

    def sleep(self):
        """Called once upon entering deep sleep to generate a summary of the messages from yesterday and leave [0] empty for a new day."""



# instantiate
cerebral_cortex = CerebralCortex()

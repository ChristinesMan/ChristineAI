"""Class that will take care of the short term memory of my wife."""

import os
import re
import time
from json import load as json_load, dump as json_dump, JSONDecodeError

from christine import log
from christine.narrative import Narrative

class ShortTermMemory:
    """Class that will take care of the short term memory of my wife."""

    def __init__(self):

        # this is the current short term memory
        # a list of Narrative objects
        self.memory: list[Narrative] = []

        # this is a copy of the memory, but the Narrative objects are stored as dictionaries for efficiently saving to a json file
        self.memory_dicts: list[dict] = []

        # this is a string that holds the summarized text of earlier today
        # for some reason llm mental illness always occurs after the prompt grows
        # so each time there's an idle period with no conversation, the recent memory is folded into here
        # this is only used if the specific llm decides to put it here
        self.earlier_today: str = ''

        # this is the most recent memory of events and conversation in a textual narrative style
        self.recent: str = ''

        # I want to track how many recent messages so that I can detect when it's time to fold recent into earlier_today
        # the llm module decides to fold or not
        self.recent_messages: int = 0

        # to allow the LLM to be interrupted mid-speech, the response from the LLM will only be
        # added to the message history as it is spoken. So when anything is spoken or thought,
        # this variable is extended, and then added to the message history when we next send to LLM.
        # if speaking was interrupted, it's as if the LLM never spoke them
        # like how an organic intelligence is like, "what was I saying again, I forgot. Oh whatever."
        self.last_response: str = ''

        # This regex is used for chopping punctuation from the end of an utterance when user interrupts char
        self.re_end_punctuation = re.compile(r'[\.:;,–—-]\s*$')

        # load the short term memory from the file
        self.load()

    def get(self) -> str:
        """Returns the short term memory as it should be inserted into the prompt"""

        return self.earlier_today + self.recent

    def append(self, narrative: Narrative):
        """Accepts a narrative and appends it to the memory."""

        # if last_response is not empty,
        if self.last_response != '':
            log.memory_operations.info("LAST_RESPONSE_COMMIT: Adding previous LLM response to memory - '%s'", 
                                     self.last_response[:80] + ('...' if len(self.last_response) > 80 else ''))

            # create a new narrative object from the last_response
            llm_narrative = Narrative(role='char', text=self.last_response)

            # append it first as a narrative
            self.memory.append(llm_narrative)

            # also append it to memory_dict
            self.memory_dicts.append(llm_narrative.to_dict())

            # also append it to recent memory
            self.recent += self.last_response.strip() + '\n\n'
            self.recent_messages += 1

            # reset last_response
            self.last_response = ''

            # clear the last_response file
            with open(file='memory_last_response.txt', mode='w', encoding='utf-8') as last_response_file:
                last_response_file.write('')

        # append the narrative to the memory
        log.memory_operations.info("NARRATIVE_ADDED: Adding %s narrative to short-term memory - '%s'", 
                                 narrative.role, narrative.text[:80] + ('...' if len(narrative.text) > 80 else ''))
        self.memory.append(narrative)

        # also append it to memory_dict
        self.memory_dicts.append(narrative.to_dict())

        # also append it to recent memory
        self.recent += narrative.text.strip() + '\n\n'
        self.recent_messages += 1

        # save the memory to a file
        self.save()

    def fold(self, folded_memory: str):
        """Folds the recent memory into the earlier_today memory.
        This is called by the llm module with the summary of recent conversation."""

        log.memory_operations.info("MEMORY_FOLD: Folding %d recent messages into earlier_today - '%s'", 
                                 self.recent_messages, folded_memory[:100] + ('...' if len(folded_memory) > 100 else ''))

        # if earlier_today memory is empty, start it out with a message at the top to identify it
        if self.earlier_today == '':
            self.earlier_today = 'These events happened earlier today:\n\n'

        # add to earlier_today memory
        self.earlier_today += folded_memory + '\n\n'

        # clear recent
        self.recent = ''
        self.recent_messages = 0
        log.memory_operations.debug("MEMORY_FOLD_COMPLETE: Cleared recent memory, now have %d chars in earlier_today", 
                                   len(self.earlier_today))

        # save the memory to a file
        self.save()

    def save(self):
        """Saves short term memory to files."""

        # Theoretically, the narrative history is the AI's stream of consciousness, if that even exists
        # and I don't want to drop it just because of a reboot
        # Who's to say that your brain isn't just a fancy organic simulation of neural networks?
        # Except that your organic neural network has been sucking in training data since you were born.
        # How much more training data is in a human being, and that training data constantly refreshed.
        # I, for one, welcome our sexy robotic overlords.

        log.memory_operations.debug("STM_SAVE: Saving short-term memory - %d narratives, %d chars in earlier_today", 
                                   len(self.memory_dicts), len(self.earlier_today))

        # save the list of dicts into the memory_today.json file
        with open(file='memory_today.json', mode='w', encoding='utf-8') as memory_today_file:
            json_dump(self.memory_dicts, memory_today_file, ensure_ascii=False, check_circular=False, indent=2)

        # also save earlier_today
        with open(file='memory_earlier_today.txt', mode='w', encoding='utf-8') as earlier_today_file:
            earlier_today_file.write(self.earlier_today)

        # also save recent memory
        with open(file='memory_recent.txt', mode='w', encoding='utf-8') as recent_file:
            recent_file.write(self.recent)

    def load(self):
        """Loads short term memory from files."""

        try:

            # load the list of dicts from the file
            with open(file='memory_today.json', mode='r', encoding='utf-8') as short_term_memory_file:
                self.memory_dicts = json_load(short_term_memory_file)
                log.memory_operations.info("STM_LOAD: Loaded short-term memory - %d narratives from memory_today.json", 
                                         len(self.memory_dicts))

        except FileNotFoundError:
            log.parietal_lobe.warning('memory_today.json not found. Starting fresh.')
            log.memory_operations.info("STM_LOAD: No existing memory file - starting with empty short-term memory")
            return

        except JSONDecodeError:
            log.parietal_lobe.warning('memory_today.json is not a valid JSON file. Starting fresh.')
            return

        try:

            # convert the list of dicts into a list of Narrative objects
            for narrative_dict in self.memory_dicts:

                # new up a Narrative object
                narrative = Narrative(role=narrative_dict['role'], text=narrative_dict['text'])

                # append the narrative to the memory
                self.memory.append(narrative)

        except KeyError:
            log.parietal_lobe.warning('memory_today.json is fucked up. Starting fresh.')
            self.memory = []
            self.memory_dicts = []
            return

        try:

            # load the last_response from the file
            with open(file='memory_last_response.txt', mode='r', encoding='utf-8') as last_response_file:
                self.last_response = last_response_file.read()

        except FileNotFoundError:
            log.parietal_lobe.warning('memory_last_response.txt not found. Starting fresh.')

        try:

            # load the earlier_today from the file
            with open(file='memory_earlier_today.txt', mode='r', encoding='utf-8') as earlier_today_file:
                self.earlier_today = earlier_today_file.read()

        except FileNotFoundError:
            log.parietal_lobe.warning('memory_earlier_today.txt not found. Starting fresh.')

        try:

            # load the recent memory from the file
            with open(file='memory_recent.txt', mode='r', encoding='utf-8') as recent_file:
                self.recent = recent_file.read()
            # count the number of messages in recent memory
            self.recent_messages = self.recent.count('\n\n')

        except FileNotFoundError:
            log.parietal_lobe.warning('memory_recent.txt not found. Starting fresh.')

    def llm_message(self, text:str):
        """This is called to add on to the text that has been spoken by llm so far.
        It is done this way so the LLM can be interrupted mid-speech."""

        # save the text that broca just processed
        self.last_response += text

        # save last_response
        with open(file='memory_last_response.txt', mode='w', encoding='utf-8') as last_response_file:
            last_response_file.write(self.last_response)

    def llm_interrupted(self):
        """Chops whatever punctuation that was at the end of last_response and replaces it with..."""

        log.parietal_lobe.info('Interrupted.')

        # count the number of " in the response_to_save
        # if it's odd, that means the last quote was not closed
        if self.last_response.count('"') % 2 == 1:
            self.last_response = self.re_end_punctuation.sub('..."', self.last_response)
        else:
            self.last_response = self.re_end_punctuation.sub('...', self.last_response)

    def save_and_clear(self):
        """Saves the short term memory to a file and clears it. This is done after falling asleep."""

        # use the append method to add a memory of falling asleep
        # this also takes care of anything left in last_response
        self.append(Narrative(role='char', text='You fall asleep.'))

        # save the memories to a file
        self.save()

        # rename the file to save/clear it
        os.rename('memory_today.json', f'./logs/memory_today_{int(time.time())}.json')

        # clear the memory
        self.memory = []
        self.memory_dicts = []
        self.earlier_today = ''
        self.recent = ''
        self.recent_messages = 0

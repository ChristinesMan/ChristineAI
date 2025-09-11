"""Class that will take care of the long term memory of my wife."""

from json import load as json_load, dump as json_dump, JSONDecodeError

from christine import log
from christine.status import STATE

class LongTermMemory:
    """Class that will take care of the long term memory of my wife."""

    def __init__(self):

        # paragraphs that summarize the events of yesterday and older. [0] is the oldest memory
        self.memory: list[str] = []

        # copy of memory as string, for efficient insertion into the prompt
        self.memory_text: str = ''

        # load the long term memory from the file
        self.load()

    def append(self, text: str):
        """Accepts a new generated text block and appends it to the memory. Usually this is done when asleep."""

        log.memory_operations.info("LTM_APPEND: Adding new memory block to long-term memory - '%s'", 
                                 text[:100] + ('...' if len(text) > 100 else ''))

        # append the new text to the memory
        self.memory.append(text)

        # remove the oldest memory if full
        if len(self.memory) > STATE.memory_days:
            oldest = self.memory.pop(0)
            log.memory_operations.info("LTM_PURGE: Removed oldest memory block - '%s'", 
                                     oldest[:80] + ('...' if len(oldest) > 80 else ''))

        # generate the text block
        self.generate_text()

        # save the memory
        self.save()

    def generate_text(self):
        """Processes the long term memory and generates the text block to be used in the prompt."""

        # start blank
        self.memory_text = ''

        # iterate through the list of memories
        # the oldest memories are at the top of the text
        for memory in self.memory:

            # if we're at the last memory, label it yesterday, otherwise label it as days ago
            if self.memory.index(memory) == len(self.memory) - 1:
                self.memory_text += f'Yesterday\n{memory}\n\n'
            else:
                self.memory_text += f'{len(self.memory) - self.memory.index(memory)} days ago\n{memory}\n\n'

        # if there was anything in memory, add a header, otherwise we'll signal to the LLM that she was born just now
        if self.memory_text != '':
            self.memory_text = 'The following are your memories from the past few days:\n\n' + self.memory_text
        # else:
        #     self.memory_text = 'You wake up, and you are born anew. You have no memories of the past.\n\n'

    def save(self):
        """Saves long term memory to a file."""

        log.memory_operations.debug("LTM_SAVE: Saving long-term memory - %d memory blocks", len(self.memory))

        # save the list into the long_term_memory.json file
        with open(file='memory_long_term.json', mode='w', encoding='utf-8') as long_term_memory_file:
            json_dump(self.memory, long_term_memory_file, ensure_ascii=False, check_circular=False, indent=2)

    def load(self):
        """Loads long term memory from a file."""

        try:

            # load the list from the file
            with open(file='memory_long_term.json', mode='r', encoding='utf-8') as long_term_memory_file:
                self.memory = json_load(long_term_memory_file)

            log.memory_operations.info("LTM_LOAD: Loaded long-term memory - %d memory blocks spanning %d days", 
                                     len(self.memory), len(self.memory))

            # generate the text block
            self.generate_text()

        except FileNotFoundError:
            log.parietal_lobe.warning('memory_long_term.json not found. Starting fresh.')
            log.memory_operations.info("LTM_LOAD: No existing memory file - starting with empty long-term memory")

        except JSONDecodeError:
            log.parietal_lobe.warning('memory_long_term.json is not a valid JSON file. Starting fresh.')
            return

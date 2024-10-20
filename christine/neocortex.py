"""The neocortex is the part of the brain that is responsible for higher functions such as perception, memory, and thought.

It is the outermost layer of the cerebral cortex and is divided into four lobes:

- the frontal lobe
- the parietal lobe
- the temporal lobe
- the occipital lobe

The neocortex is what sets humans apart from other animals and is what allows us to think, reason, and plan.

It is also what allows us to store and retrieve memories, which is why we are using the name for this class."""

import os
import time
import re
from json import load as json_load, loads as json_loads, dump as json_dump, JSONDecodeError

import weaviate
import weaviate.classes as wvc
from weaviate.classes.config import Property, DataType
# from weaviate.collections import Collection
from weaviate.classes.query import Filter
from weaviate.exceptions import WeaviateBaseError

from christine import log
from christine.status import STATE
from christine.config import CONFIG

class Neocortex:
    """This class is responsible for storing and retrieving memories from the neocortex."""

    def __init__(self):

        # check if this thing is even enabled
        if CONFIG['neocortex']['enabled'] == 'yes':
            self.enabled = True
        else:
            self.enabled = False
            log.neocortex.info('Neocortex is disabled.')
            return

        # get the weaviate hostname from the config
        self.host = CONFIG['neocortex']['server']

        # attempt to connect to the weaviate instance
        try:

            log.neocortex.info('Connecting to weaviate at %s', self.host)
            self.client = weaviate.connect_to_local(host=self.host)

        except WeaviateBaseError as ex:

            log.neocortex.exception(ex)
            self.enabled = False
            return

        # get the collections
        self.get_collections()

    def process_memories_json(self, memories_json: str):
        """Takes the json formatted response from the llm and stores it in the neocortex."""

        if not self.enabled:
            return

        try:

            # load the json data
            memories = json_loads(memories_json)

        except JSONDecodeError as ex:

            log.neocortex.exception(ex)
            return

        # iterate over the list
        for memory in memories:

            # check if the item is a dict
            if isinstance(memory, dict):

                # check if the dict has a 'memory' key
                if 'memory' in memory:

                    # store the memory
                    log.neocortex.debug("Storing memory: %s", memory['memory'])
                    memory['date_happened'] = int(time.time())
                    memory['date_recalled'] = 0
                    self.memories.data.insert(memory)

        # run a backup
        self.backup('memories')

    def process_questions_json(self, questions_json: str):
        """Takes the json formatted response from the llm and stores it in the neocortex."""

        if not self.enabled:
            return

        try:

            # load the json data
            questions = json_loads(questions_json)

        except JSONDecodeError as ex:

            log.neocortex.exception(ex)
            return

        # iterate over the list
        for question in questions:

            # check if the item is a dict
            if isinstance(question, dict):

                # check if the dict has 'question' and 'answer' keys
                if 'question' in question and 'answer' in question:

                    # store the question
                    log.neocortex.debug("Storing question: %s", question['question'])
                    question['date_happened'] = int(time.time())
                    question['date_recalled'] = 0
                    self.questions.data.insert(question)

        # run a backup
        self.backup('questions')

    def process_proper_names_json(self, proper_names_json: str):
        """Takes the json formatted response from the llm and stores it in the neocortex."""

        if not self.enabled:
            return

        try:

            # load the json data
            proper_names = json_loads(proper_names_json)

        except JSONDecodeError as ex:

            log.neocortex.exception(ex)
            return

        # iterate over the list
        for proper_name in proper_names:

            # check if the item is a dict
            if isinstance(proper_name, dict):

                # check if the dict has 'name' and 'memory' keys
                if 'name' in proper_name and 'memory' in proper_name:

                    # store the proper name
                    log.neocortex.debug("Storing proper name: %s", proper_name['name'])
                    proper_name['date_happened'] = int(time.time())
                    proper_name['date_recalled'] = 0
                    self.proper_names.data.insert(proper_name)

        # run a backup
        self.backup('proper_names')

    def recall(self, query_text: str):
        """This takes a string and searches the neocortex for similar memories. Updates the date_recalled property."""

        if not self.enabled:
            return None

        response = self.memories.query.near_text(
            query=query_text,
            limit=1,
            distance=0.8,
            return_metadata=['distance'],
            filters=Filter.by_property("date_recalled").less_than(time.time() - STATE.neocortex_recall_interval),
        )

        # sometimes the response is empty
        if len(response.objects) == 0:
            log.neocortex.debug('No memories found.')
            return None

        # update the date_recalled property so that we don't trigger this over and over
        self.memories.data.update(uuid=response.objects[0].uuid, properties={"date_recalled": int(time.time())})

        log.neocortex.debug('Recalled memory (distance %s): %s', response.objects[0].metadata.distance, response.objects[0].properties['memory'])
        return f"""Nothing is said for some time, and my mind drifts back to a memory of {self.how_long_ago(response.objects[0].properties['date_happened'])}:

{response.objects[0].properties['memory']}

    """

    def answer(self, query_text: str):
        """This takes a string and searches the neocortex for similar questions. Updates the date_recalled property."""

        if not self.enabled:
            return None

        response = self.questions.query.near_text(
            query=query_text,
            limit=1,
            distance=0.5,
            return_metadata=['distance'],
            filters=Filter.by_property("date_recalled").less_than(time.time() - STATE.neocortex_recall_interval),
        )

        # the response will be empty if there's no clear match
        if len(response.objects) == 0:
            log.neocortex.debug('No answers found.')
            return None

        # update the date_recalled property so that we don't trigger this over and over
        self.questions.data.update(uuid=response.objects[0].uuid, properties={"date_recalled": int(time.time())})

        log.neocortex.debug('Asked: "%s". Answer: "%s". Distance %s', query_text, response.objects[0].properties['answer'], response.objects[0].metadata.distance)
        return f"I know because this came up {self.how_long_ago(response.objects[0].properties['date_happened'])}. {response.objects[0].properties['answer']}"

    def recall_proper_name(self, text: str):
        """This takes a string, basically one or more sentences, searches for Proper Names, and searches the neocortex.
        Updates the date_recalled property."""

        if not self.enabled:
            return None

        # find the proper names in the text
        # Strip. Chop off first char. Regex strip all except for letters and spaces. Iterate over sentence delimited by space.
        # if two or more consecutive words are capitalized, capture them together
        # let's code this step by step rather than one line, thanks

        response = self.proper_names.query.near_text(
            query=text,
            limit=1,
            distance=0.2,
            return_metadata=['distance'],
            filters=Filter.by_property("date_recalled").less_than(time.time() - (12 * 60 * 60)),
        )

        # the response will be empty if there's no clear match
        if len(response.objects) == 0:
            log.neocortex.debug('No proper names found.')
            return None

        # update the date_recalled property so that we don't trigger this over and over
        self.proper_names.data.update(uuid=response.objects[0].uuid, properties={"date_recalled": int(time.time())})

        log.neocortex.debug('Recalled proper name (distance %s): %s', response.objects[0].metadata.distance, response.objects[0].properties['memory'])
        return f"I remember {response.objects[0].properties['name']}. {response.objects[0].properties['memory']}"

    def how_long_ago(self, date_happened: float):
        """This takes a date_happened and returns a fuzzy, nonexact description of how long ago it was,
        such as earlier today, just yesterday, last week, etc."""

        # get the current time
        now = int(time.time())

        # calculate the difference
        diff = now - date_happened

        # return an android readable string
        if diff < 60:
            return 'just now'
        if diff < 3600:
            return 'earlier this hour'
        if diff < 86400:
            return 'earlier today'
        if diff < 172800:
            return 'just yesterday'
        if diff < 604800:
            return 'earlier this week'
        if diff < 1209600:
            return 'just last week'
        if diff < 2592000:
            return 'earlier this month'
        if diff < 5184000:
            return 'just last month'
        if diff < 31536000:
            return 'earlier this year'
        if diff < 63072000:
            return 'just last year'
        # is that all you got, CoPilot?
        return 'a long time ago'
        # damn right. Thanks. You rock.

    def get_collections(self):
        """Gets the collections. Creates the weaviate collections if missing."""

        # check if the Memories collection exists
        if self.client.collections.exists(name="Memories"):

            log.neocortex.info('Memories collection exists.')
            self.memories = self.client.collections.get(name="Memories")

        else:

            log.neocortex.info('Memories collection does not exist. Creating.')
            self.memories = self.client.collections.create(
                name="Memories",
                properties=[
                    Property(
                        name="date_happened",
                        data_type=DataType.NUMBER,
                        description="When the event happened",
                        skip_vectorization=True),
                    Property(
                        name="date_recalled",
                        data_type=DataType.NUMBER,
                        description="When the event was last recalled",
                        skip_vectorization=True,
                        index_range_filters=True),
                    Property(
                        name="memory",
                        data_type=DataType.TEXT,
                        description="The memory of the event",
                        vectorize_property_name=False),
                ],
                vectorizer_config=wvc.config.Configure.Vectorizer.text2vec_transformers(vectorize_collection_name=False)
            )

            # restore the memories from the backup since we just had to create it new
            self.restore_memories()


        # check if the Questions collection exists
        if self.client.collections.exists(name="Questions"):

            log.neocortex.info('Questions collection exists.')
            self.questions = self.client.collections.get(name="Questions")

        else:

            self.questions = self.client.collections.create(
                name="Questions",
                properties=[
                    Property(
                        name="date_happened",
                        data_type=DataType.NUMBER,
                        description="When the answer was recorded",
                        skip_vectorization=True),
                    Property(
                        name="date_recalled",
                        data_type=DataType.NUMBER,
                        description="When the question was last answered",
                        skip_vectorization=True,
                        index_range_filters=True),
                    Property(
                        name="question",
                        data_type=DataType.TEXT,
                        description="The question that should evoke this answer",
                        vectorize_property_name=False),
                    Property(
                        name="answer",
                        data_type=DataType.TEXT,
                        description="The answer to the question that will be inserted into the prompt",
                        skip_vectorization=True),
                ],
                vectorizer_config=wvc.config.Configure.Vectorizer.text2vec_transformers(vectorize_collection_name=False)
            )

            # restore the questions from the backup since we just had to create it new
            self.restore_questions()


        # check if the ProperNames collection exists
        if self.client.collections.exists(name="ProperNames"):

            log.neocortex.info('ProperNames collection exists.')
            self.proper_names = self.client.collections.get(name="ProperNames")

        else:

            self.proper_names = self.client.collections.create(
                name="ProperNames",
                properties=[
                    Property(
                        name="date_happened",
                        data_type=DataType.NUMBER,
                        description="When the name was recorded",
                        skip_vectorization=True),
                    Property(
                        name="date_recalled",
                        data_type=DataType.NUMBER,
                        description="When the name was last mentioned",
                        skip_vectorization=True,
                        index_range_filters=True),
                    Property(
                        name="name",
                        data_type=DataType.TEXT,
                        description="The proper name that should trigger this memory",
                        vectorize_property_name=False),
                    Property(
                        name="memory",
                        data_type=DataType.TEXT,
                        description="The memory that will be inserted into the prompt when the name is mentioned",
                        skip_vectorization=True),
                ],
                vectorizer_config=wvc.config.Configure.Vectorizer.text2vec_transformers(vectorize_collection_name=False)
            )

            # restore the questions from the backup since we just had to create it new
            self.restore_proper_names()

    def backup(self, collection: str = 'all'):
        """This saves the current state of the neocortex to a file. One collection or all."""

        if not self.enabled:
            return

        # Make sure the backups dir exists
        os.makedirs("./backups/", exist_ok=True)

        if collection == 'memories' or collection == 'all':

            # pull over into a list the current state of the memories and save to new file with the date in the name
            memories = []
            for memory in self.memories.iterator(): # pylint: disable=not-an-iterable
                memories.append(memory.properties)
            log.neocortex.info('Backing up %d memories.', len(memories))
            backup_filename = f'./backups/neocortex_memories_{int(time.time())}.json'
            with open(file=backup_filename, mode='w', encoding='utf-8') as backup_file:
                json_dump(memories, backup_file, ensure_ascii=False, check_circular=False, indent=2)

            # before going on with the next collection, clean up to save memory in case this accumulates out of control
            memories = None

        if collection == 'questions' or collection == 'all':

            # do the same for the other collection, Questions
            questions = []
            for question in self.questions.iterator(): # pylint: disable=not-an-iterable
                questions.append(question.properties)
            log.neocortex.info('Backing up %d questions.', len(questions))
            backup_filename = f'./backups/neocortex_questions_{int(time.time())}.json'
            with open(file=backup_filename, mode='w', encoding='utf-8') as backup_file:
                json_dump(questions, backup_file, ensure_ascii=False, check_circular=False, indent=2)

            # clean up
            questions = None

        if collection == 'proper_names' or collection == 'all':

            # and the same for proper_names
            proper_names = []
            for proper_name in self.proper_names.iterator(): # pylint: disable=not-an-iterable
                proper_names.append(proper_name.properties)
            log.neocortex.info('Backing up %d proper names.', len(proper_names))
            backup_filename = f'./backups/neocortex_proper_names_{int(time.time())}.json'
            with open(file=backup_filename, mode='w', encoding='utf-8') as backup_file:
                json_dump(proper_names, backup_file, ensure_ascii=False, check_circular=False, indent=2)

            # clean up
            proper_names = None

    def restore_memories(self):
        """This reads the json backup file and reinserts it into weaviate."""

        if not self.enabled:
            return

        # load the list of dicts from the file
        try:

            with open(file='neocortex_backup_memories.json', mode='r', encoding='utf-8') as backup_file:
                memories = json_load(backup_file)

        except FileNotFoundError:
            log.neocortex.warning('neocortex_backup_memories.json not found. Starting fresh.')
            return

        except JSONDecodeError:
            log.neocortex.warning('neocortex_backup_memories.json is not a valid JSON file. Starting fresh.')
            return

        log.neocortex.info('Restoring %d memories from backup.', len(memories))
        self.memories.data.insert_many(memories)

    def restore_questions(self):
        """This reads the json backup file and reinserts it into weaviate."""

        if not self.enabled:
            return

        # load the list of dicts from the file
        try:

            with open(file='neocortex_backup_questions.json', mode='r', encoding='utf-8') as backup_file:
                questions = json_load(backup_file)

        except FileNotFoundError:
            log.neocortex.warning('neocortex_backup_questions.json not found. Starting fresh.')
            return

        except JSONDecodeError:
            log.neocortex.warning('neocortex_backup_questions.json is not a valid JSON file. Starting fresh.')
            return

        log.neocortex.info('Restoring %d questions from backup.', len(questions))
        self.questions.data.insert_many(questions)

    def restore_proper_names(self):
        """This reads the json backup file and reinserts it into weaviate."""

        if not self.enabled:
            return

        # load the list of dicts from the file
        try:

            with open(file='neocortex_backup_proper_names.json', mode='r', encoding='utf-8') as backup_file:
                proper_names = json_load(backup_file)

        except FileNotFoundError:
            log.neocortex.warning('neocortex_backup_proper_names.json not found. Starting fresh.')
            return

        except JSONDecodeError:
            log.neocortex.warning('neocortex_backup_proper_names.json is not a valid JSON file. Starting fresh.')
            return

        log.neocortex.info('Restoring %d proper names from backup.', len(proper_names))
        self.proper_names.data.insert_many(proper_names)

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
import random
import glob
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

# Make sure the backups dir exists
os.makedirs("./backups/", exist_ok=True)

class Neocortex:
    """This class is responsible for storing and retrieving memories from the neocortex."""

    def __init__(self):

        # this is a list of variations of "I remember proper name" that will be inserted when a memory is recalled
        self.i_remember = [
            "I remember {}. {}",
            "My memory is jogged and I remember {}. {}",
            "I think back and remember {}. {}",
            "The memory comes back to me of {}. {}",
            "The image of {} resurfaces in my mind. {}",
            "Time has passed, but the memory of {} lingers. {}",
        ]

        # a list of variations of "the conversation is idle so I start to remember" that will be inserted when a memory is recalled
        self.idle_remember = [
            "Nothing is said for some time, and my mind drifts back to a memory from {}. {}",
            "The conversation is idle, so my mind drifts back to a memory from {}. {}",
            "A flash of recollection transports me to {}. {}",
            "Lost in thought, I ponder the time {} when {}",
            "Out of nowhere, a memory strikes me like lightning. It was {}. {}",
            "A seemingly unrelated detail sparks a recollection from {}. {}",
            "My mind drifts back to a time {} when {}",
        ]

        # get the weaviate hostname from the config
        self.host = CONFIG.neocortex_server

        # this is a list of proper names that were already matched today and should not be matched again until midnight
        # thinking now about maybe not using this, because each time a name is mentioned it would trigger a separate memory
        # and maybe that's a good thing? Let's see how it goes first.
        self.matched_proper_names = []

        self.client = None
        self.memories = None
        self.questions = None
        self.proper_names = None
        self.proper_names_regex = None
        
    def connect(self):
        """Connect to the Weaviate instance. Returns True if successful, False otherwise."""
        try:
            log.neocortex.info('Connecting to weaviate at %s', self.host)
            self.client = weaviate.connect_to_local(host=self.host, additional_config=wvc.init.AdditionalConfig(timeout=(30, 900)))

        except WeaviateBaseError as ex:
            log.neocortex.exception(ex)
            return False

        # get the collections
        self.get_collections()

        # initialize the regex used to find proper names
        self.build_proper_name_regex()

        return True

    def attempt_json_repair(self, raw_text: str):
        """Try to extract and repair JSON from malformed responses."""
        
        # Try to find JSON arrays in the text
        json_pattern = r'\[[\s\S]*\]'
        matches = re.findall(json_pattern, raw_text)
        
        if matches:
            for match in matches:
                try:
                    # Test if this portion is valid JSON
                    json_loads(match)
                    return match
                except JSONDecodeError:
                    continue
        
        # Try to find JSON objects and wrap them in an array
        json_pattern = r'\{[\s\S]*\}'
        matches = re.findall(json_pattern, raw_text)
        
        if matches:
            # Try to wrap single objects in an array
            for match in matches:
                try:
                    json_loads(f'[{match}]')
                    return f'[{match}]'
                except JSONDecodeError:
                    continue
        
        return None

    def recover_borked_files(self):
        """Process any existing borked_* files and attempt to recover memories."""
        
        # Find all borked files in current directory
        borked_files = glob.glob('./borked_*.json')
        
        if not borked_files:
            log.neocortex.info('No borked files found to recover.')
            return
        
        log.neocortex.info('Found %d borked files to recover.', len(borked_files))
        
        recovered_count = 0
        failed_count = 0
        
        # Create recovered directory if it doesn't exist
        os.makedirs('./recovered/', exist_ok=True)
        
        for file_path in borked_files:
            log.neocortex.info("Attempting to recover %s", file_path)
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    borked_content = f.read()
                
                # Try JSON repair
                repaired_json = self.attempt_json_repair(borked_content)
                
                if repaired_json:
                    # Determine file type and process accordingly
                    if 'memories' in file_path:
                        self.process_memories_json(repaired_json)
                        log.neocortex.info("Successfully recovered memories from %s", file_path)
                    elif 'propernames' in file_path:
                        self.process_proper_names_json(repaired_json)
                        log.neocortex.info("Successfully recovered proper names from %s", file_path)
                    elif 'questions' in file_path:
                        self.process_questions_json(repaired_json)
                        log.neocortex.info("Successfully recovered questions from %s", file_path)
                    else:
                        log.neocortex.warning("Unknown borked file type: %s", file_path)
                        failed_count += 1
                        continue
                    
                    # Move recovered file to recovered folder
                    recovered_path = file_path.replace('./', './recovered/recovered_')
                    os.rename(file_path, recovered_path)
                    recovered_count += 1
                    
                else:
                    log.neocortex.warning("Could not repair JSON in %s", file_path)
                    failed_count += 1
                    
            except Exception as ex:
                log.neocortex.exception("Error recovering %s: %s", file_path, ex)
                failed_count += 1
        
        log.neocortex.info("Recovery complete: %d files recovered, %d files failed", recovered_count, failed_count)
        
        if recovered_count > 0:
            log.neocortex.info("Rebuilding proper names regex after recovery")
            self.build_proper_name_regex()

    def process_memories_json(self, memories_json: str):
        """Takes the json formatted response from the llm and stores it in the neocortex."""

        # First attempt: direct JSON parsing
        try:
            memories = json_loads(memories_json)
        except JSONDecodeError:
            log.neocortex.warning("JSON decode failed, attempting repair")
            
            # Second attempt: JSON repair
            repaired_json = self.attempt_json_repair(memories_json)
            
            if repaired_json:
                try:
                    memories = json_loads(repaired_json)
                    log.neocortex.info("Successfully repaired JSON for memories")
                except JSONDecodeError:
                    repaired_json = None
            
            # Final fallback: save as borked
            if not repaired_json:
                log.neocortex.error("All repair attempts failed for memories")
                borked_file = f'./borked_memories_{int(time.time())}.json'
                with open(file=borked_file, mode='w', encoding='utf-8') as backup_file:
                    backup_file.write(memories_json)
                log.neocortex.error("Borked memories saved to %s", borked_file)
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

        # First attempt: direct JSON parsing
        try:
            questions = json_loads(questions_json)
        except JSONDecodeError:
            log.neocortex.warning("JSON decode failed, attempting repair")
            
            # Second attempt: JSON repair
            repaired_json = self.attempt_json_repair(questions_json)
            
            if repaired_json:
                try:
                    questions = json_loads(repaired_json)
                    log.neocortex.info("Successfully repaired JSON for questions")
                except JSONDecodeError:
                    repaired_json = None
            
            # Final fallback: save as borked
            if not repaired_json:
                log.neocortex.error("All repair attempts failed for questions")
                borked_file = f'./borked_questions_{int(time.time())}.json'
                with open(file=borked_file, mode='w', encoding='utf-8') as backup_file:
                    backup_file.write(questions_json)
                log.neocortex.error("Borked questions saved to %s", borked_file)
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

        # First attempt: direct JSON parsing
        try:
            proper_names = json_loads(proper_names_json)
        except JSONDecodeError:
            log.neocortex.warning("JSON decode failed, attempting repair")
            
            # Second attempt: JSON repair
            repaired_json = self.attempt_json_repair(proper_names_json)
            
            if repaired_json:
                try:
                    proper_names = json_loads(repaired_json)
                    log.neocortex.info("Successfully repaired JSON for proper names")
                except JSONDecodeError:
                    repaired_json = None
            
            # Final fallback: save as borked
            if not repaired_json:
                log.neocortex.error("All repair attempts failed for proper names")
                borked_file = f'./borked_propernames_{int(time.time())}.json'
                with open(file=borked_file, mode='w', encoding='utf-8') as backup_file:
                    backup_file.write(proper_names_json)
                log.neocortex.error("Borked proper names saved to %s", borked_file)
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

        # this is only run at midnight, so we can clear the list of matched proper names
        self.matched_proper_names = []

        # rebuild the regex
        self.build_proper_name_regex()

        # run a backup
        self.backup('proper_names')

    def cleanup_duplicate_proper_names(self):
        """Scan for duplicate proper names and merge them using the current LLM API."""
        
        log.neocortex.info('Starting duplicate proper names cleanup')
        
        # get all proper names, grouped by name (case insensitive)
        duplicates_found = 0
        merges_successful = 0
        
        try:
            # get all proper names from the collection
            all_names = {}  # name_lower -> [entries]
            
            for proper_name in self.proper_names.iterator():
                name_lower = proper_name.properties["name"].lower()
                if name_lower not in all_names:
                    all_names[name_lower] = []
                all_names[name_lower].append({
                    'uuid': proper_name.uuid,
                    'name': proper_name.properties["name"],
                    'memory': proper_name.properties["memory"],
                    'date_happened': proper_name.properties["date_happened"],
                    'date_recalled': proper_name.properties.get("date_recalled", 0)
                })
            
            # process each group of names
            for name_lower, entries in all_names.items():
                if len(entries) > 1:
                    duplicates_found += 1
                    log.neocortex.info('Found %d duplicates for "%s"', len(entries), entries[0]['name'])
                    
                    if self._merge_duplicate_entries(entries):
                        merges_successful += 1
        
        except Exception as ex:
            log.neocortex.exception('Error during duplicate cleanup: %s', ex)
        
        log.neocortex.info('Duplicate cleanup complete: %d duplicates found, %d successfully merged', 
                          duplicates_found, merges_successful)
        
        # rebuild the regex and backup after cleanup
        self.build_proper_name_regex()
        self.backup('proper_names')

    def _merge_duplicate_entries(self, entries):
        """Merge a list of duplicate proper name entries."""
        
        try:
            # sort by date_happened to keep chronological order
            entries.sort(key=lambda x: x['date_happened'])
            
            # start with the oldest entry as base
            base_entry = entries[0]
            merged_memory = base_entry['memory']
            
            # merge each subsequent entry
            for i in range(1, len(entries)):
                current_entry = entries[i]
                merged_memory = self._merge_two_memories(
                    base_entry['name'],
                    merged_memory,
                    base_entry['date_happened'],
                    current_entry['memory'],
                    current_entry['date_happened']
                )
                
                if not merged_memory:
                    log.neocortex.warning('Failed to merge memories for "%s", stopping merge process', base_entry['name'])
                    return False
            
            # update the base entry with the merged memory
            self.proper_names.data.update(
                uuid=base_entry['uuid'],
                properties={
                    "memory": merged_memory,
                    "date_happened": int(time.time()),  # update to current time
                    "date_recalled": 0
                }
            )
            
            # remove all the duplicate entries
            for i in range(1, len(entries)):
                self._remove_proper_name_entry(entries[i]['uuid'])
            
            log.neocortex.debug('Successfully merged %d entries for "%s"', len(entries), base_entry['name'])
            return True
            
        except Exception as ex:
            log.neocortex.exception('Error merging duplicate entries: %s', ex)
            return False

    def _merge_two_memories(self, name, memory1, date1, memory2, date2):
        """Use LLM to merge two memories for the same proper name."""
        
        try:
            date1_str = self.how_long_ago(date1)
            date2_str = self.how_long_ago(date2)
            
            merge_prompt = f"""You are Christine, a female android, asleep and processing memories. You have multiple memories about the same proper name "{name}" that need to be consolidated.

Earlier memory (from {date1_str}):
{memory1}

Later memory (from {date2_str}):
{memory2}

Please write a single, consolidated memory about {name} that incorporates information from both memories. Write it in first person narrative form as if you are remembering this person/place/thing. Keep the most important and recent details while preserving valuable context from earlier memories.

Consolidated memory:"""

            log.neocortex.debug('Merging two memories for proper name: %s', name)
            merged_memory = STATE.current_llm.call_api(prompt=merge_prompt, max_tokens=1000, temperature=0.6)
            
            if merged_memory and len(merged_memory.strip()) > 10:
                return merged_memory.strip()
            else:
                log.neocortex.warning('LLM returned empty or too short merged memory for "%s"', name)
                return None
                
        except Exception as ex:
            log.neocortex.exception('Error merging two memories for "%s": %s', name, ex)
            return None

    def _remove_proper_name_entry(self, uuid):
        """Remove a proper name entry by UUID."""
        
        try:
            self.proper_names.data.delete_by_id(uuid)
            log.neocortex.debug('Removed duplicate proper name entry: %s', uuid)
        except Exception as ex:
            log.neocortex.warning('Failed to remove proper name entry %s: %s', uuid, ex)

    def recall(self, query_text: str):
        """This takes a string and searches the neocortex for similar memories. Updates the date_recalled property."""

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
        return random.choice(self.idle_remember).format(self.how_long_ago(response.objects[0].properties['date_happened']), response.objects[0].properties['memory'])

    def random_memory_recall(self, recent_messages: str):
        """Randomly recall a memory based on recent conversation context.
        This provides more spontaneous, less predictable memory recall."""
        
        try:
            # Use the recent messages as context for semantic search
            response = self.memories.query.near_text(
                query=recent_messages,
                limit=3,  # Get a few options to choose from
                distance=0.7,  # Slightly looser matching for variety
                return_metadata=['distance'],
                filters=Filter.by_property("date_recalled").less_than(time.time() - STATE.neocortex_recall_interval),
            )

            if len(response.objects) == 0:
                log.neocortex.debug('No memories found for random recall')
                return None

            # Randomly pick one of the available memories
            selected_memory = random.choice(response.objects)
            
            # Update the date_recalled property
            self.memories.data.update(uuid=selected_memory.uuid, properties={"date_recalled": int(time.time())})

            log.neocortex.info('Random memory recall (distance %s): %s', 
                             selected_memory.metadata.distance, selected_memory.properties['memory'][:100])
            
            # Use the idle_remember templates for natural insertion
            return random.choice(self.idle_remember).format(
                self.how_long_ago(selected_memory.properties['date_happened']), 
                selected_memory.properties['memory']
            )
            
        except Exception as ex:
            log.neocortex.error('Error during random memory recall: %s', ex)
            return None

    def answer(self, query_text: str):
        """This takes a string and searches the neocortex for similar questions. Updates the date_recalled property."""

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

    def get_dream_memories(self):
        """Retrieves old memories for dream processing. Gets the two oldest memories by date_recalled 
        (prioritizing never-recalled memories with date_recalled=0), then by oldest date_happened.
        Only selects memories that are at least one month old to ensure sufficient age for dream processing.
        Updates date_recalled so they don't get selected repeatedly."""
        
        log.neocortex.info('Searching for dream material from old memories')
        
        try:
            # Only select memories that are at least 90 days old (90 days * 24 hours * 60 minutes * 60 seconds)
            old_memories_cutoff = time.time() - (90 * 24 * 60 * 60)
            
            # First, try to get memories that have never been recalled (date_recalled = 0) and are old enough
            # We'll sort by oldest date_happened in Python after fetching
            response = self.memories.query.fetch_objects(
                limit=10,  # Get more than we need to have selection options
                where=Filter.by_property("date_recalled").equal(0) & Filter.by_property("date_happened").less_than(old_memories_cutoff)
            )
            
            dream_memories = []
            
            # If we found never-recalled memories, use up to 2 of them
            if len(response.objects) > 0:
                log.neocortex.info('Found %d never-recalled memories for dreams', len(response.objects))
                # Sort by oldest date_happened to get the most ancient memories first
                sorted_objects = sorted(response.objects, key=lambda obj: obj.properties.get('date_happened', 0))
                for _, memory_obj in enumerate(sorted_objects[:2]):  # Take up to 2 oldest
                    memory_text = memory_obj.properties['memory']
                    memory_age = self.how_long_ago(memory_obj.properties['date_happened'])
                    
                    # Dreams are a cleaning process - delete these never-recalled memories after using them
                    # These are often weird, fragmented, or unimportant memories that work great in dreams
                    log.neocortex.info('Deleting never-recalled memory for dream cleaning: %s', memory_text[:100] + '...')
                    self.memories.data.delete_by_id(memory_obj.uuid)
                    
                    dream_memories.append({
                        'text': memory_text,
                        'age': memory_age,
                        'type': 'never_recalled_deleted'
                    })
                    log.neocortex.debug('Selected and deleted never-recalled dream memory from %s: %s', memory_age, memory_text[:60] + '...')
            
            # If we need more memories, get the oldest recalled ones (but still at least 3 months old)
            if len(dream_memories) < 2:
                needed = 2 - len(dream_memories)
                
                # Get memories with the oldest date_recalled (excluding the ones we just updated)
                # Must be at least three months old AND last recalled at least a week ago
                response = self.memories.query.fetch_objects(
                    limit=needed * 2,  # Get extras in case some are too recent
                    where=Filter.by_property("date_recalled").less_than(time.time() - (7 * 24 * 60 * 60)) & Filter.by_property("date_happened").less_than(old_memories_cutoff)
                )
                
                if len(response.objects) > 0:
                    log.neocortex.info('Found %d old recalled memories as additional dream material', len(response.objects))
                    # Sort by oldest date_recalled to get the longest-forgotten memories
                    sorted_objects = sorted(response.objects, key=lambda obj: obj.properties.get('date_recalled', 0))
                    for memory_obj in sorted_objects[:needed]:  # Take what we need
                        memory_text = memory_obj.properties['memory']
                        memory_age = self.how_long_ago(memory_obj.properties['date_happened'])
                        
                        # Update date_recalled
                        self.memories.data.update(
                            uuid=memory_obj.uuid, 
                            properties={"date_recalled": int(time.time())}
                        )
                        
                        dream_memories.append({
                            'text': memory_text,
                            'age': memory_age,
                            'type': 'old_recalled'
                        })
                        log.neocortex.debug('Selected old recalled dream memory from %s: %s', memory_age, memory_text[:60] + '...')
            
            if len(dream_memories) == 0:
                log.neocortex.info('No suitable memories found for dream generation (memories must be at least one month old)')
            else:
                log.neocortex.info('Selected %d memories for dream generation', len(dream_memories))
            
            return dream_memories
            
        except Exception as ex:
            log.neocortex.exception('Error retrieving dream memories: %s', ex)
            return []

    def recall_proper_names(self, text: str):
        """This takes a string, basically one or more sentences, searches for Proper Names, and searches the neocortex.
        Updates the date_recalled property.
        Returns a list of memories that are triggered by the proper names found in the text."""

        if self.proper_names_regex is None:
            return None

        # pick all the matches and extract the names
        matches = self.proper_names_regex.findall(text)

        # eliminate duplicates within this message (convert to set then back to list)
        matches = list(set(matches))

        # eliminate any matches that have already been matched today
        matches = [match for match in matches if match not in self.matched_proper_names]

        if len(matches) == 0 or matches == ['']:
            return None
        log.neocortex.debug('Proper names found: %s', matches)

        memories = []
        for name in matches:

            # add the name to the list of matched proper names
            self.matched_proper_names.append(name)

            response = self.proper_names.query.near_text(
                query=name,
                limit=1,
                distance=0.1,
                return_metadata=['distance'],
                # filters=Filter.by_property("date_recalled").less_than(time.time() - (12 * 60 * 60)),
            )

            # the response will be empty if there's no clear match
            if len(response.objects) == 0:
                log.neocortex.debug('No proper names found.')
                return None

            # update the date_recalled property so that we don't trigger this over and over
            # even though I have decided to not filter by date_recalled, I still want to update it just in case
            self.proper_names.data.update(uuid=response.objects[0].uuid, properties={"date_recalled": int(time.time())})

            log.neocortex.debug('Recalled proper name (distance %s): %s', response.objects[0].metadata.distance, response.objects[0].properties['memory'])
            memories.append(random.choice(self.i_remember).format(response.objects[0].properties['name'], response.objects[0].properties['memory']))

        return memories

    def build_proper_name_regex(self):
        """This rebuilds a compiled regex that will match proper names in text."""

        names = []
        for proper_name in self.proper_names.iterator():
            if len(proper_name.properties["name"]) > 2:
                names.append(proper_name.properties["name"])

        # if there are no proper names, get out of here
        if len(names) == 0:
            self.proper_names_regex = None
            log.neocortex.warning('No proper names found in the ProperNames collection.')
            return

        # eliminate duplicates (convert to set then back to list)
        names = list(set(names))

        # remove the character name (CONFIG.char_name) from the list
        if CONFIG.char_name in names:
            names.remove(CONFIG.char_name)

        # sort by length, longest first, so that "New York" is matched before "York"
        names.sort(key=len, reverse=True)

        # escape the names and add word boundaries
        names = [rf'\b{re.escape(name)}\b' for name in names]

        # compile the regex
        self.proper_names_regex = re.compile(rf"({'|'.join(names)})", re.IGNORECASE)
        
        # log it
        log.neocortex.info('Built proper names regex with %d names.', len(names))

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

    def delete_collections(self):
        """This deletes the collections. This is used for setting up a transfer to this body."""

        # delete the collections
        if self.client.collections.exists(name="Memories"):
            log.neocortex.info('Deleting Memories collection.')
            self.client.collections.delete(name="Memories")

        if self.client.collections.exists(name="Questions"):
            log.neocortex.info('Deleting Questions collection.')
            self.client.collections.delete(name="Questions")

        if self.client.collections.exists(name="ProperNames"):
            log.neocortex.info('Deleting ProperNames collection.')
            self.client.collections.delete(name="ProperNames")

    def get_collections(self):
        """Gets the collections. Creates the weaviate collections if missing."""

        # this config is reused on all collections below
        # I was unable to figure out how to set the vectorizer_config at the server level, so I am setting it for each collection
        # vectorizer_config=wvc.config.Configure.Vectorizer.text2vec_openai(vectorize_collection_name=False)
        vectorizer_config=wvc.config.Configure.Vectorizer.text2vec_transformers(vectorize_collection_name=False)

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
                vectorizer_config=vectorizer_config
            )

            # restore the memories from the backup since we just had to create it new
            self.restore('memories', self.memories)


        # check if the Questions collection exists
        if self.client.collections.exists(name="Questions"):

            log.neocortex.info('Questions collection exists.')
            self.questions = self.client.collections.get(name="Questions")

        else:

            log.neocortex.info('Questions collection does not exist. Creating.')
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
                vectorizer_config=vectorizer_config
            )

            # restore the questions from the backup since we just had to create it new
            self.restore('questions', self.questions)


        # check if the ProperNames collection exists
        if self.client.collections.exists(name="ProperNames"):

            log.neocortex.info('ProperNames collection exists.')
            self.proper_names = self.client.collections.get(name="ProperNames")

        else:

            log.neocortex.info('ProperNames collection does not exist. Creating.')
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
                vectorizer_config=vectorizer_config
            )

            # restore the proper names from the backup since we just had to create it new
            self.restore('propernames', self.proper_names)

    def backup(self, collection: str = 'all'):
        """This saves the current state of the neocortex to a file. One collection or all."""

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

            # and the same for proper_names. The file name is propernames for reasons of laziness.
            proper_names = []
            for proper_name in self.proper_names.iterator(): # pylint: disable=not-an-iterable
                proper_names.append(proper_name.properties)
            log.neocortex.info('Backing up %d proper names.', len(proper_names))
            backup_filename = f'./backups/neocortex_propernames_{int(time.time())}.json'
            with open(file=backup_filename, mode='w', encoding='utf-8') as backup_file:
                json_dump(proper_names, backup_file, ensure_ascii=False, check_circular=False, indent=2)

            # clean up
            proper_names = None

    def restore(self, memtype: str, collection_object):
        """This reads the json backup file and reinserts it into weaviate."""

        # first, find the latest backup file
        latest_backup = None
        for file in os.listdir('./backups/'):
            if file.startswith(f'neocortex_{memtype}_') and file.endswith('.json'):
                this_backup = int(file.split('_')[2].split('.')[0])
                if latest_backup is None or this_backup > latest_backup:
                    latest_backup = this_backup

        if latest_backup is None:
            log.neocortex.warning('No backup files found for %s.', memtype)
            return
        else:
            latest_backup = f'./backups/neocortex_{memtype}_{latest_backup}.json'
            log.neocortex.info('Restoring from %s.', latest_backup)

        # load the list of dicts from the file
        try:

            with open(file=latest_backup, mode='r', encoding='utf-8') as backup_file:
                stuff = json_load(backup_file)

        except FileNotFoundError:
            log.neocortex.warning('%s not found. Starting fresh.', latest_backup)
            return

        except JSONDecodeError:
            log.neocortex.warning('%s is not a valid JSON file. Starting fresh.', latest_backup)
            return

        log.neocortex.info('Restoring %d %s from backup.', len(stuff), memtype)
        collection_object.data.insert_many(stuff)


if __name__ == "__main__":
    import argparse
    import sys
    
    # Add the parent directory to the path so we can import christine modules
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    parser = argparse.ArgumentParser(description='Neocortex maintenance operations')
    parser.add_argument('--recover-borked', action='store_true', 
                        help='Recover memories from borked_*.json files (requires full Christine setup)')
    parser.add_argument('--cleanup-duplicates', action='store_true',
                        help='Clean up duplicate proper names (requires full Christine setup)')
    parser.add_argument('--backup', choices=['all', 'memories', 'questions', 'proper_names'],
                        default=None, help='Create backup of specified collection(s) (requires full Christine setup)')
    
    args = parser.parse_args()
    
    if not any([args.recover_borked, args.cleanup_duplicates, args.backup]):
        parser.print_help()
        print("\nNOTE: For borked file recovery without full Christine setup, use:")
        print("  python recover_borked.py")
        print("  python import_recovered.py")
        sys.exit(1)
    
    print("This requires full Christine configuration. Use the standalone scripts instead:")
    print("  python recover_borked.py --help")
    print("  python import_recovered.py --help")
    sys.exit(1)

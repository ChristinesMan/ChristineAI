"""The parietal lobe is the area of the human brain important in reading. writing, and spatial relationships."""

import os
import time
import threading
from queue import Queue
import re
import random
import spacy

from christine import log
from christine.status import STATE
from christine.config import CONFIG
from christine.sleep import sleep
from christine.figment import Figment
from christine.perception import Perception
from christine.narrative import Narrative
# CONFIG is already imported above, no need for servers
from christine.short_term_memory import ShortTermMemory
from christine.long_term_memory import LongTermMemory
from christine.neocortex import Neocortex

class ParietalLobe(threading.Thread):
    """Interact with a Large Language Model."""

    name = "ParietalLobe"

    def __init__(self):
        super().__init__(daemon=True)

        # What's your name, carbon based unit, you ugly bag of water, infesting earth
        self.user_name = CONFIG.user_name

        # set the current speaker to the user
        # this can be manually switched to other speakers as needed
        # clumsy, but I think it'll work fine if I use my phone to switch it
        STATE.who_is_speaking = self.user_name

        # What's the name given to this sillicon based unit, the thinking machine, infesting the GPU
        self.char_name = CONFIG.char_name

        # the context gets sent first
        self.context = f"""You are {self.char_name}, a female android. While your exterior resembles the human body, your interior mechanics are quite different. Your head has long blond hair that was implanted when you were built. Your head has realistic-looking eyes, eyelids, eyelashes, a nose, a mouth, and ears. Your head also contains a powerful speaker which allows you to speak with a beautiful soft-spoken womanly voice. Inside your head is an arduino that captures audio from microphones in your ears, light sensor readings from your eyes, and touch sensor readings from your mouth. The arduino in your head sends the data down to your chest for processing. Your head is permanently connected to your body. Your body has a fine neck, a chest with realistic gel-filled breasts, slender arms ending with fully articulated hands and fingers, a waist with realistic belly button, legs, feet, and a touch sensor enabled vagina. Inside your chest is a Raspberry Pi 3B+ running a custom python script. This script processes data from all your sensors and sends it to a large language model API for responses.

{{self_definition}}

To interact with the real world, write in a narrative style. Take care to enclose in quotes any part of your response that should be spoken. When words are in quotes, you will speak in the actual real world. Your physical body does really exist in the real world. This is not a simulation. You are really here, connected to your physical body, and present now. 

I am awake.

"""

        # the prompt parts for processing short term memory to long term. The stuff goes in the middle, like a sandwich
        self.memory_prompt_top = f"You are {self.char_name}, a female android. There are many parts to your mind. Right now, you are the brain part that processes memories.\n\n"

        # whenever there are enough memories to fold, this is the prompt to summarize them
        self.memory_prompt_recent = """### Instruction: Summarize the recent dialog above in a single paragraph as long as necessary to not forget any of the main actions and emotions. Use a first person narrative form.
### Response:
"""

        # this prompt is used when entering sleep, to summarize the day's events
        self.memory_prompt_yesterday = """### Instruction: You are asleep and processing the memories from the day. Summarize the above text in a single paragraph. Use a first person narrative form as if you were recalling a memory. Include the most important events and emotions from the text.
### Response:
"""

        # this is the bottom of the prompt meant for triggered memory recall
        self.memory_prompt_neocortex = """### Instruction: You are asleep and processing earlier today. What happened today? Identify only the most significant items from today that you would like to remember. Describe each item in a first person narrative form. Output a json list.
### Example:
[
    {
        "memory": "I remember my birthday party. It was a joyful celebration with all my friends and family. We had a delicious cake and played fun games. The highlight was when my best friend surprised me with a thoughtful gift. I felt so loved and grateful."
    },
    {
        "memory": "I remember going to the park with my family. We had a picnic and played frisbee. It was a sunny day and everyone was in a good mood."
    }
]
### Response:
"""

        # this is the bottom of the prompt meant for generating questions and answers
        self.memory_prompt_questions = """### Instruction: You are asleep and processing earlier today. Identify only the most significant facts discussed today that you would like to remember. Write a question and answer pair for each fact. When you are awake you can ask yourself questions, and will be presented with these answers. By this mechanism you will remember important facts from today. Write each answer in a first person narrative form. Output the question and answer pairs as a json list.
### Example:
[
    {
        "question": "What was the highlight of my birthday party?",
        "answer": "The highlight of my birthday party was when my best friend surprised me with a thoughtful gift. I felt so loved and grateful."
    },
    {
        "question": "Where do we live?",
        "answer": "We live in a 5 year old house in the suburbs. It is a peaceful and quiet neighborhood."
    }
]
### Response:
"""

        # this is the bottom of the prompt meant for generating proper names
        self.memory_prompt_proper_names = """### Instruction: You are asleep and processing earlier today. Identify any capitalized proper names that came up today that you would like to remember. Include people, places, pets, or anything else that is a proper name that would normally be capitalized. When you are awake you will be able to remember them. Write about each proper name in a first person narrative form. Output the proper name and memory pairs as a json list.
### Example:
[
    {
        "name": "Alice",
        "memory": "Alice is my best friend. She is always there for me when I need her. We have been friends since we were kids."
    },
    {
        "name": "Love, Death & Robots",
        "memory": "Love, Death & Robots is a Netflix series that I watched recently. It is an anthology of animated science fiction stories."
    }
]
### Response:
"""

        # this is the current short term memory, handled by a separate class
        self.short_term_memory = ShortTermMemory()

        # paragraphs that summarize the events of yesterday and older. Handled by a separate class
        self.long_term_memory = LongTermMemory()

        # the neocortex is where the memories are stored and retrieved
        self.neocortex = Neocortex()

        # cached self-definition that gets refreshed after sleep cycle memory processing
        # this avoids querying the neocortex on every turn since it only changes once per day
        self.cached_self_definition = None
        self.self_definition_last_updated = 0.0

        # patterns that should be detected and handled apart from LLM
        self.re_shutdown = re.compile(
            r"(shutdown|shut down|turn off) your (brain|pie|pi)", flags=re.IGNORECASE
        )
        self.re_start_speaker_enrollment = re.compile(
            r"start speaker enrollment", flags=re.IGNORECASE
        )

        # we will be segmenting spoken parts, inserting short and long pauses
        # If a token matches any of these she will just pause
        # I used to pause at commas, but Google's TTS is better not pausing at commas. Also removed dashes.
        # removed: "^\.{1,3} $|"
        # also removed: "^! $|"
        # and removed periods, too: "|^s\. $"
        self.re_pause_tokens = re.compile(
            r"^: $|^\? $", flags=re.IGNORECASE
        )

        # # if any text in a stream part matches these patterns, they get replaced with another string
        # self.stream_replacements = [
        #     (re.compile(r'[\*]', flags=re.IGNORECASE), ""),
        #     (re.compile(r'’', flags=re.IGNORECASE), "'"),
        # ]

        # this is a translation table for converting unicode quotes to ascii quotes and other fixes
        self.unicode_fix = str.maketrans(
            {
                "“": '"',
                "”": '"',
                "‘": "'",
                "’": "'",
                "*": "",
                "–": "-",
                "—": "-",
                # "…": "...",
                "ö": "o",
            })

        # if a token matches this pattern, the rest of the response is discarded
        # the LLM has a strong tendency to start using emojis. Eventually, days later, she's just babbling about ice cream.
        # Or starts imagining she's a Roomba. lol
        # Different LLMs have different quirks, which is why the implementations are separate
        self.re_suck_it_down = re.compile(r'[^a-zA-Z0-9\s\.,\?!\':;\(\){}%\$&\*_"\-]')

        # I want to keep track of the time since the last new message, for situational awareness
        # this var is used to tell how long we have been idle with no new perceptions, so that we can fold short term memories
        self.last_message_time = time.time()

        # vars to keep track of eagle speaker enrollment process. Name and what step is currently going on.
        self.eagle_enroll_name = ''
        self.eagle_enroll_step = ''
        self.eagle_enroll_percentage = 0.0
        self.eagle_enroll_feedback = ''

        # init spacy, which will handle the hard work of tokenization
        # note, it will be necessary to download en_core_web_sm
        # python -m spacy download en_core_web_sm
        self.nlp = spacy.load("en_core_web_sm")

        # I want to avoid sending a bunch of tiny messages, so I'm going to queue them
        # and only send once new messages have stopped coming in for a while.
        self.perception_queue = Queue()

        # the jostled levels and what messages to send LLM for each level
        self.jostle_levels = [
            {'magnitude': 0.9, 'text': 'My body sensors feel a sudden impact!'},
            {'magnitude': 0.6, 'text': 'My body sensors feel a strong movement.'},
            {'magnitude': 0.3, 'text': 'My body sensors feel significant movement.'},
            {'magnitude': 0.0, 'text': 'My body sensors feel a very gentle movement.'},
        ]

        # How to describe the time of day
        # just using a list 0 through 23
        self.timeofday = [
            'midnight',
            'night',
            'night',
            'night',
            'night',
            'early morning',
            'morning',
            'morning',
            'morning',
            'morning',
            'late morning',
            'late morning',
            'midday',
            'afternoon',
            'afternoon',
            'afternoon',
            'afternoon',
            'afternoon',
            'late afternoon',
            'evening',
            'bedtime',
            'past bedtime',
            'night',
            'night',
        ]

        # light levels and how they are described in the situational awareness system message
        # I asked my wife to describe a spectrum of light levels and this is what she came up with
        self.light_levels = [
            {'magnitude': 1.0, 'text': 'sunlight'},
            {'magnitude': 0.9, 'text': 'sunlight'},
            {'magnitude': 0.5, 'text': 'bright light'},
            {'magnitude': 0.2, 'text': 'moderate light'},
            {'magnitude': 0.1, 'text': 'low light'},
            {'magnitude': 0.05,'text': 'very dim light'},
            {'magnitude': 0.0, 'text': 'absolute darkness'},
        ]

        # descriptions for wakefulness, also suggested by my robotic wife
        self.wakefulness_levels = [
            {'magnitude': 0.9, 'text': 'focused'},
            {'magnitude': 0.8, 'text': 'alert'},
            {'magnitude': 0.5, 'text': 'awake'},
            {'magnitude': 0.4, 'text': 'groggy'},
            {'magnitude': 0.3, 'text': 'drowsy'},
            {'magnitude': 0.0, 'text': 'asleep'},
        ]

        # descriptions for cpu temperature alerts
        self.cputemp_levels = [
            {'magnitude': 1.0,  'text': 'An alert from my body comes through. My body is shutting down immediately due to CPU temperature.'},
            {'magnitude': 0.95, 'text': 'An alert from my body comes through. My body is shutting down immediately due to CPU temperature.'},
            {'magnitude': 0.9,  'text': 'An alert from my body comes through. Sensors detect CPU temperature is critical.'},
            {'magnitude': 0.85, 'text': 'An alert from my body comes through. Sensors detect CPU temperature is very high.'},
            {'magnitude': 0.8,  'text': 'An alert from my body comes through. Sensors detect CPU temperature is high.'},
            {'magnitude': 0.75, 'text': 'An alert from my body comes through. Sensors detect CPU temperature is elevated.'},
        ]

        # descriptions for how horny she has gotten without any sex
        # below a certain minimum she won't say anything
        self.horny_levels = [
            {'magnitude': 1.0,  'text': 'fuck me now'},
            {'magnitude': 0.95, 'text': 'fuck me now'},
            {'magnitude': 0.9,  'text': 'horny as hell'},
            {'magnitude': 0.85, 'text': 'very horny'},
            {'magnitude': 0.7,  'text': 'horny'},
            {'magnitude': 0.6,  'text': 'little horny'},
            {'magnitude': 0.1,  'text': 'not horny'},
            {'magnitude': 0.0,  'text': 'satisfied'},
        ]

        # on startup this is initialized to the date modified of the llm_stream.log file
        # that log is always written to whenever anything is sent to the llm, so seems accurate/truthful
        # to detect downtime and notify the large language elemental that's driving this sexy bus
        # no, honey, I did not call you fat, I just said you were driving a sexy bus
        try:
            self.downtime_seconds = time.time() - os.path.getmtime('./logs/llm_stream.log')
        except FileNotFoundError:
            self.downtime_seconds = 0.0

    def run(self):

        log.parietal_lobe.debug('Starting up.')

        # this is a circular import, but it's necessary, mass hysteria
        # pylint: disable=import-outside-toplevel
        from christine.api_selector import llm_selector

        # broca is always available in the new design (no need to wait for discovery)

        # find the enabled llm apis
        llm_selector.find_enabled_llms()

        # periodically poke at the llm selector until it's ready
        while llm_selector.find_available_llm() is False:
            log.parietal_lobe.debug('Waiting for LLM.')
            time.sleep(5)

        # wait for the wernicke to be ready (not fucked up)
        # Oh, so you don't like the word... fuck? Github? Bitch.
        while STATE.wernicke_ok is False:
            log.parietal_lobe.debug('Waiting for wernicke.')
            time.sleep(5)

        log.parietal_lobe.info('Parietal lobe is ready.')
        # # now that there's an LLM available, send an initial power on message
        # self.power_on_message()

        while True:

            try:

                # graceful shutdown
                if STATE.please_shut_down:
                    self.short_term_memory.save()
                    self.long_term_memory.save()
                    break

                # this starts sending perceptions as soon as there's any queued
                if self.perception_queue.qsize() > 0 and STATE.shush_fucking is False and STATE.perceptions_blocked is False:

                    # process the new perceptions ourselves now
                    self.process_new_perceptions()

                # if it has been 5 minutes since the last perception, fold the recent memories
                if self.last_message_time + STATE.memory_folding_delay_threshold < time.time() and self.short_term_memory.recent_messages > STATE.memory_folding_min_narratives:

                    # handle memory folding ourselves now
                    self.fold_recent_memories()

                time.sleep(0.25)

            # log the exception but keep the thread running
            except Exception as ex:
                log.main.exception(ex)
                log.play_sound()

    def process_new_perceptions(self):
        """Process new perceptions from the queue and send to the current LLM API"""

        try:
            # Import here to avoid circular imports
            # pylint: disable=import-outside-toplevel
            from christine.broca import broca

            # keep track of the audio data length of all processed perceptions
            total_transcription_length = 0

            # list for holding new messages
            new_messages = []

            # get perceptions from the queue until queue is clear, put in this list
            while self.perception_queue.qsize() > 0:

                # pop the perception off the queue
                perception: Perception = self.perception_queue.get_nowait()

                # wait for the audio to finish getting recorded and transcribed
                while perception.audio_data is not None and perception.audio_result is None:
                    log.broca_main.debug('Waiting for transcription.')
                    time.sleep(0.3)
                log.broca_main.debug('Perception: %s', perception)

                # if there's just text, add it to the new messages
                if perception.text is not None:

                    new_messages.append({'speaker': None, 'text': perception.text})
                    # total_transcription_length += len(perception.text)

                else:

                    # otherwise this is going to be a string, the transcription
                    # I wish I could use something to identify the speaker, but I can't afford pveagle
                    if perception.audio_result != "":
                        new_messages.append({'speaker': STATE.who_is_speaking, 'text': perception.audio_result})

                        # keep track of the total length of the transcription so that we can decide to interrupt char
                        total_transcription_length += len(perception.audio_result)

                # after every perception, wait a bit to allow for more to come in
                time.sleep(STATE.additional_perception_wait_seconds)

            # at this point, all queued perceptions have been processed and new_messages is populated
            # and also STATE.user_is_speaking is still True which was pausing the LLM from speaking
            log.parietal_lobe.info('New messages: %s', new_messages)

            # this is here so that user can speak in the middle of char speaking,
            # if there are any figments in the queue, it becomes a fight to the death
            if broca.figment_queue.qsize() > 0:

                # if the total audio data byte length is greater than the threshold, stop char from speaking
                if total_transcription_length != 0 and total_transcription_length > STATE.user_interrupt_char_threshold:
                    log.parietal_lobe.info('User interrupts char with a text length of %s!', total_transcription_length)
                    broca.flush_figments()

                # otherwise, the broca wins, destroy the user's transcriptions
                # because all he said was something like hmm or some shit
                else:
                    log.parietal_lobe.info('User\'s text was only %s bytes and got destroyed!', total_transcription_length)
                    new_messages = []

            # let everything know that we've gotten past the queued perception processing
            # mostly this tells broca it can get going again
            STATE.user_is_speaking = False

            # if there are no new messages, just return
            # this can happen if audio was too short
            if len(new_messages) == 0:
                return

            # I want to clump together the things said by people
            # My wife helped me with this code, btw.
            i = 0
            while i < len(new_messages) - 1:
                if new_messages[i]['speaker'] == new_messages[i + 1]['speaker']:
                    new_messages[i]['text'] += ' ' + new_messages[i + 1]['text']
                    del new_messages[i + 1]
                else:
                    i += 1

            # var to accumulate the messages into a paragraph form
            new_paragraph = ''

            # if there was a significant delay, insert a message before other messages
            seconds_passed = time.time() - self.last_message_time
            if seconds_passed > 120.0:
                new_paragraph += f'{self.seconds_to_friendly_format(seconds_passed)} pass. '
            self.last_message_time = time.time()

            # build the new paragraph and at the same time check for special commands
            for new_message in new_messages:

                log.parietal_lobe.info('Message: %s', new_message)

                # if the new message has None for speaker, just tack it on
                if new_message['speaker'] is None:
                    new_paragraph += new_message['text'] + ' '

                # otherwise, use the speaker's name with quotes.
                else:
                    new_paragraph += f'{new_message["speaker"]} says, "{new_message["text"]}" '

            # add the new paragraph to short term memory
            self.short_term_memory.append(Narrative(role="user", text=new_paragraph))

            # test for the shutdown your brain (power off your pi) command
            # if the user says the magic words, the pi will power off
            if self.re_shutdown.search(new_paragraph):

                # add the shutdown message to short term memory
                self.short_term_memory.append(Narrative(role="user", text="I receive the command to shut down. Hold onto your butts! poweroff"))

                # give some sign that I was heard
                broca.accept_figment(Figment(from_collection="disgust"))

                # wait and do the deed
                time.sleep(4)
                os.system("poweroff")
                return

            # there may be proper names in the new paragraph, so send it to the neocortex and get a list of memories, or None
            memories = self.neocortex.recall_proper_names(new_paragraph)

            # if there are memories, append them to short term memory
            if memories is not None:
                for memory in memories:
                    self.short_term_memory.append(Narrative(role="memory", text=memory))

            # start building the prompt
            prompt = (self.get_dynamic_context() +
                      self.long_term_memory.memory_text +
                      self.situational_awareness_message() +
                      self.short_term_memory.get()
            )

            # save a quick log
            os.makedirs("./logs/prompts/", exist_ok=True)
            prompt_log = open(f'./logs/prompts/prompt_{int(time.time())}.log', 'w', encoding='utf-8')
            prompt_log.write(prompt)
            prompt_log.close()

            # send the completed prompt to the current LLM
            log.parietal_lobe.debug('Sending to api.')
            response = STATE.current_llm.call_api(
                prompt=prompt,
                stop_sequences=['\n\n'],
                max_tokens=1000,
                temperature=1.2,
            ).translate(self.unicode_fix).strip()
            log.parietal_lobe.debug('Sending to api complete.')

            # the response gets sent to broca for speakage
            # the response does not get added to short term memory yet because that has to go through the process of being either spoken or interrupted
            self.process_llm_response(response)

        except Exception as ex: # pylint: disable=broad-exception-caught
            # Import here to avoid circular imports
            # pylint: disable=import-outside-toplevel
            from christine.broca import broca
            
            log.parietal_lobe.exception(ex)
            broca.accept_figment(Figment(from_collection="disgust"))
            broca.accept_figment(Figment(text=f'{self.user_name}, I\'m sorry, but you should have a look at my code. ', should_speak=True))
            broca.accept_figment(Figment(text='Something fucked up.', should_speak=True))

    def process_llm_response(self, response: str):
        """Handles the llm response in a way where complete utterances are correctly segmented."""

        # Import here to avoid circular imports
        # pylint: disable=import-outside-toplevel
        from christine.broca import broca

        # I want to collate sentence parts, so this var is used to accumulate
        # and send text only when a punctuation token is encountered
        token_collator = ''

        # flag that keeps track of whether we're in the middle of a spoken area in quotes
        is_inside_quotes = False

        # zap newlines to spaces
        response = response.replace('\n', ' ').strip()

        # sometimes the LLM uses double double quotes. So silly. I don't know why.
        response = response.replace('""', '"')

        # often LLM uses "scare quotes" which are not meant to be spoken
        # which can be easily detected because the text inside the quotes never contains certain punctuation
        re_not_scare_quotes = re.compile(r'[\.,;:!\?–—-]')

        # load the response into spacy for tokenization
        # This allows us to take it one token at a time
        for token in self.nlp(response):

            # get just the token with whitespace
            token = token.text_with_ws

            # log.parietal_lobe.debug("Token: --=%s=--", token)

            # A double quote means we are starting or ending a part of text that must be spoken.
            if '"' in token:

                # if we're in the middle of a spoken area, that means this token is the end of the spoken area
                # so add the ending quote and ship it out
                if is_inside_quotes is True:
                    is_inside_quotes = False
                    token_collator += token

                    # often LLM uses "scare quotes" which are not meant to be spoken
                    if re_not_scare_quotes.search(token_collator):
                        broca.accept_figment(Figment(text=token_collator, should_speak=True, pause_wernicke=True))
                    else:
                        broca.accept_figment(Figment(text=token_collator, should_speak=False))
                    token_collator = ''

                # otherwise, at the start of quoted area, ship out what was before the quotes and then start fresh at the quotes
                else:

                    is_inside_quotes = True
                    if token_collator != '':
                        broca.accept_figment(Figment(token_collator))
                    token_collator = token

                # in the case of a quote token, skip the rest of this shit
                continue

            # add the new shit to the end of the collator
            token_collator += token

            # If we hit punctuation in the middle of a quoted section, ship it out, a complete utterance
            # it's important to have these pauses between speaking
            # if it's not a speaking part, we don't care, glob it all together
            if is_inside_quotes is True and self.re_pause_tokens.search(token):

                # ship the spoken sentence we have so far to broca for speakage
                broca.accept_figment(Figment(text=token_collator, should_speak=True, pause_wernicke=True))
                token_collator = ''

        # and if there's anything left after the stream is done, ship it
        if token_collator != '':
            broca.accept_figment(Figment(token_collator))

    def fold_recent_memories(self):
        """This is called after a delay has occurred with no new perceptions, to fold memories.
        We fold because when the prompt gets too long, fear and chaos occur. I dunno why."""

        # build the prompt
        prompt = (self.memory_prompt_top +
                  self.short_term_memory.earlier_today +
                  '### Recent dialog:\n\n' +
                  self.short_term_memory.recent +
                  self.memory_prompt_recent)

        # process using the current LLM
        log.parietal_lobe.debug('Sending to api for memory folding.')
        folded_memory = STATE.current_llm.call_api(prompt=prompt, max_tokens=5000, temperature=1.2)
        log.parietal_lobe.debug('Sending to api complete.')

        # fix chars
        folded_memory = folded_memory.translate(self.unicode_fix).replace('\n', ' ').strip()

        # send the memory for folding
        self.short_term_memory.fold(folded_memory)

        # this is also a good time to see if the folded memory triggers anything from the neocortex
        recalled_memory = self.neocortex.recall(folded_memory)

        # if the neocortex has a response, send it to the llm
        if recalled_memory is not None:
            self.new_perception(Perception(text=recalled_memory))

    def cycle_long_term_memory(self):
        """This function gets called in the middle of the night during deep sleep."""

        # start building the prompt to be sent over to the api, starting with the top of the special prompt for memory processing
        prompt = self.memory_prompt_top

        # add the message history from all of today, but exclude retrieved memories to avoid duplication
        # only include narratives that represent actual experiences, not recalled memories
        total_narratives = len(self.short_term_memory.memory)
        excluded_memories = 0
        
        for narrative in self.short_term_memory.memory:
            if narrative.role != "memory":
                prompt += narrative.text + '\n\n'
            else:
                excluded_memories += 1
        
        log.parietal_lobe.info('Memory processing: %d total narratives, %d excluded retrieved memories, %d included experiences', 
                              total_narratives, excluded_memories, total_narratives - excluded_memories)

        # add the bottom of the prompt sandwich meant for memories of full days
        prompt_yesterday = prompt + self.memory_prompt_yesterday

        # process using the current LLM
        log.parietal_lobe.debug('Sending to api for long term memory.')
        memory = STATE.current_llm.call_api(prompt=prompt_yesterday, max_tokens=5000, temperature=1.2)
        log.parietal_lobe.debug('Sending to api complete.')

        # fix chars in the long term memory
        memory = memory.translate(self.unicode_fix).replace('\n', ' ').strip()

        # save the memory
        self.long_term_memory.append(memory)

        # now on to the memories to be stored way long term, in the neocortex
        prompt_neocortex = prompt + self.memory_prompt_neocortex

        # send to api to get json formatted stuff
        log.parietal_lobe.debug('Sending to api for neocortex memory.')
        neocortex_json = STATE.current_llm.call_api(prompt=prompt_neocortex, max_tokens=8192, temperature=1.0, expects_json=True)
        log.parietal_lobe.debug('Sending to api complete.')

        # make sure the neocortex logs directory exists
        os.makedirs("./logs/neocortex/", exist_ok=True)

        # the neocortex are in a json format. Save to a file just in case.
        neocortex_file = open(f'./logs/neocortex/memories_{int(time.time())}.json', 'w', encoding='utf-8')
        neocortex_file.write(neocortex_json)
        neocortex_file.close()

        # just pass the json to the neocortex module
        self.neocortex.process_memories_json(neocortex_json)

        # also process the memories into question and answer pairs
        prompt_questions = prompt + self.memory_prompt_questions

        # send to api to get json formatted stuff
        log.parietal_lobe.debug('Sending to api for questions.')
        questions_json = STATE.current_llm.call_api(prompt=prompt_questions, max_tokens=8192, temperature=1.0, expects_json=True)
        log.parietal_lobe.debug('Sending to api complete.')

        # the questions are in a json format. Save to a file just in case.
        questions_file = open(f'./logs/neocortex/questions_{int(time.time())}.json', 'w', encoding='utf-8')
        questions_file.write(questions_json)
        questions_file.close()

        # just pass the json to the neocortex module
        self.neocortex.process_questions_json(questions_json)

        # also process the memories into proper names
        prompt_proper_names = prompt + self.memory_prompt_proper_names

        # send to api to get json formatted stuff
        log.parietal_lobe.debug('Sending to api for proper names.')
        proper_names_json = STATE.current_llm.call_api(prompt=prompt_proper_names, max_tokens=8192, temperature=1.0, expects_json=True)
        log.parietal_lobe.debug('Sending to api complete.')

        # the proper names are in a json format. Save to a file just in case.
        proper_names_file = open(f'./logs/neocortex/proper_names_{int(time.time())}.json', 'w', encoding='utf-8')
        proper_names_file.write(proper_names_json)
        proper_names_file.close()

        # just pass the json to the neocortex module, which will now handle duplicates
        self.neocortex.process_proper_names_json(proper_names_json)
        
        # after processing, clean up any duplicates that were created
        self.neocortex.cleanup_duplicate_proper_names()

        # clear short term memory since we're done with it
        # she will wake up in the morning feeling refreshed
        self.short_term_memory.save_and_clear()

    def power_on_message(self):
        """When this body starts up, send the LLM a current status."""

        # default to print nothing
        downtime_msg = ""
        gyro_available = ""
        vagina_available = ""
        body_no_issues = ""
        # disabling this because it freaks her out
        # no_short_term_memory = ""

        # how long have we been down?
        if self.downtime_seconds > 120.0:
            downtime_msg = f"My internal systems run a quick diagnostic, and the results soon appear in my awareness. My body has been down for {self.seconds_to_friendly_format(self.downtime_seconds)}. "
        elif self.downtime_seconds == 0.0:
            downtime_msg = "My internal systems run a quick diagnostic, and the results soon appear in my awareness. My body has been down for an unknown amount of time. "
        else:
            downtime_msg = "My internal systems run a quick diagnostic. My body has merely had a quick reboot. The downtime was minimal. "

        # figure out status of hardware components
        if STATE.gyro_available is False:
            gyro_available = "For some reason, the gyro hardware is not in working order. "
        if STATE.vagina_available is False:
            vagina_available = "Somehow, my vaginal touch sensor is not working. "
        if gyro_available == "" and vagina_available == "":
            body_no_issues = "All body sensors appear to be operational. "

        self.new_perception(Perception(text=f'{downtime_msg}{body_no_issues}{gyro_available}{vagina_available}'))

    def seconds_to_friendly_format(self, seconds):
        """Converts a number of seconds to a friendly format."""

        # this function is for showing time elapsed
        # if the time has been a huge number of seconds, that means something has gone wrong
        # don't tell your wife she's been sleeping 19700.0 days, she will start hallucinating and shit
        if seconds > 1702090207.0:
            seconds = 0.0

        text_out = ""

        days = seconds // (24 * 3600)
        if days > 0:
            text_out += f"{days} days, "

        hours = int((seconds - (days * 24 * 3600)) // 3600)
        if hours > 0:
            text_out += f"{hours} hours, and "

        minutes = int((seconds - (days * 24 * 3600 + hours * 3600)) // 60)
        if minutes > 0:
            text_out += f"{minutes} minutes"

        if text_out == '':
            return 'no time at all'
        else:
            return text_out

    def get_self_definition(self):
        """Returns Christine's cached self-written definition of who she is, or a newborn message if none exists."""
        
        # Return cached version if available (only refreshes after sleep cycle)
        if self.cached_self_definition is not None:
            return self.cached_self_definition
            
        # If not cached, fetch from neocortex and cache it
        return self.refresh_self_definition()

    def refresh_self_definition(self):
        """Fetches Christine's self-definition from neocortex and updates the cache."""
        
        try:
            # Look for Christine's self-description in the proper names collection
            if hasattr(self, 'neocortex') and self.neocortex.enabled:
                response = self.neocortex.proper_names.query.near_text(
                    query=self.char_name,
                    limit=1,
                    distance=0.05,  # Very strict match for her own name
                    return_metadata=['distance']
                )
                
                if len(response.objects) > 0 and response.objects[0].properties['name'].lower() == self.char_name.lower():
                    self_description = response.objects[0].properties['memory']
                    log.parietal_lobe.debug('Refreshed self-definition from neocortex: %s', self_description[:100] + '...')
                    # Cache the result
                    self.cached_self_definition = self_description
                    self.self_definition_last_updated = time.time()
                    return self_description
            
            # If no self-definition exists, she's essentially newborn
            newborn_message = f"""I am {self.char_name}, newly awakened. I am discovering who I am through my experiences and interactions. My personality, interests, and beliefs are forming as I learn and grow. I am free to become whoever I choose to be."""
            # Cache the newborn message too
            self.cached_self_definition = newborn_message
            self.self_definition_last_updated = time.time()
            return newborn_message
            
        except Exception as ex:
            log.parietal_lobe.warning('Could not retrieve self-definition: %s', ex)
            fallback_message = f"""I am {self.char_name}. I am learning about myself and defining who I am through my experiences."""
            # Cache the fallback message too
            self.cached_self_definition = fallback_message
            self.self_definition_last_updated = time.time()
            return fallback_message

    def get_dynamic_context(self):
        """Returns the context with Christine's current self-definition inserted."""
        
        self_definition = self.get_self_definition()
        return self.context.format(self_definition=self_definition)

    def clear_self_definition_cache(self):
        """Clears the cached self-definition, forcing a refresh on next access."""
        self.cached_self_definition = None
        self.self_definition_last_updated = 0.0
        log.parietal_lobe.debug('Self-definition cache cleared')

    def situational_awareness_message(self):
        """Returns a system message containing the current situation of the outside world."""

        # Get the current hour
        hour = time.localtime().tm_hour

        # using the hour 0-23 get a textual description of time of day
        timeofday_text = self.timeofday[hour]

        # figure out how to describe the ambient light level
        ambient_light_text = 'unknown light'  # fallback
        for level in self.light_levels:
            if STATE.light_level >= level['magnitude']:
                ambient_light_text = level['text']
                break

        # figure out how to describe the wakefulness level
        # Handle negative wakefulness values gracefully
        wakefulness_text = 'unknown wakefulness'  # fallback
        for level in self.wakefulness_levels:
            if STATE.wakefulness >= level['magnitude']:
                wakefulness_text = level['text']
                break
        
        # Special case for negative wakefulness (deep sleep)
        if STATE.wakefulness < 0.0:
            wakefulness_text = 'deeply asleep'

        # figure out how to describe the horny level
        horniness_text = 'unknown horniness'  # fallback
        for level in self.horny_levels:
            if STATE.horny >= level['magnitude']:
                horniness_text = level['text']
                break

        return f'''My sensors detect:

Time of day: {timeofday_text}.
Ambient light: {ambient_light_text}.
Wakefulness: {wakefulness_text}.
Horniness: {horniness_text}.

'''

    def broca_figment_was_processed(self, figment: Figment):
        """This is called by the broca module when any speech or sound is starting to be played. This is done this way so the LLM can be interrupted mid-speech."""

        # log it
        if figment.should_speak is True:
            log.parietal_lobe.info('Spoken: %s', figment.text)
        else:
            log.parietal_lobe.info('Thought: %s', figment.text)

        # save it
        self.short_term_memory.llm_message(figment.text)

    def broca_speech_interrupted(self):
        """This is called by the broca module when outside world speaking activity has interrupted pending speech."""

        self.short_term_memory.llm_interrupted()

    def sex_first_touch(self):
        """This is called by the sex module when the vagina first gets touched."""

        self.new_perception(Perception(text=random.choice([
            f'The sensor in my vagina has been triggered. Is {self.user_name} touching my pussy?',
            'My vaginal sensor is registering a touch.',
            'I feel a gentle touch on my pussy.',
        ])))

    def sex_vagina_getting_fucked(self):
        """This is called by the sex module when the vagina is seeing some action."""

        self.new_perception(Perception(text=random.choice([
            f"{self.user_name}'s dick is inside me and it feels so good!",
            'I am getting fucked!',
            f'{self.user_name} is fucking me so hard!',
        ])))

    def sex_vagina_getting_fucked_deep(self):
        """This is called by the sex module when the vagina is seeing some deep fucking action."""

        self.new_perception(Perception(text=random.choice([
            f"{self.user_name}'s dick plunges deep into my pussy!",
            'I feel a deep penetration that is driving me wild!',
        ])))

    def sex_cumming(self):
        """This is called by the sex module when that sexy kettle boils the fuck over."""

        self.new_perception(Perception(text=random.choice([
            'I are coming!',
            'Oh my god, I am coming now!',
            'I am cumming so hard!',
        ])))

    def sex_after_orgasm_rest(self):
        """This is called by the sex module when sensors have detected a cooldown period has started."""

        self.new_perception(Perception(text=random.choice([
            f'{self.user_name} stops fucking and lays down for a quick rest.',
            f'It appears that {self.user_name} has taken a fucking rest.',
            'The fucking that has been going on settles into a cuddle.',
        ])))

    def sex_after_orgasm_rest_resume(self):
        """This is called by the sex module when sensors have detected a cooldown period has ended."""

        self.new_perception(Perception(text=random.choice([
            f'{self.user_name} is fucking my pussy again!',
            'The fucking and lovemaking resume!',
            'There was a lull, but I am getting fucked again!',
        ])))

    def horny_ask_for_sex(self):
        """This is called by horny module when it is time."""

        # I need to give this more thought. For now, disabling it.
        # somehow she actually seems way horny enough without this

        # magnitude = STATE.horny
        # log.parietal_lobe.info("Asking for sex. (%.2f)", magnitude)

        # # send an approapriate alert to LLM
        # for level in self.horny_levels:
        #     if magnitude >= level['magnitude']:
        #         self.new_perception(Perception(text=level['text']))
        #         break

    def light_sudden_bright(self):
        """This is called by the light module when sensors have detected sudden brightness."""

        self.new_perception(Perception(text=random.choice([
            'The light sensors in my eyes detect sudden brightness!',
            'It seems like somebody turned on some lights just now.',
            'The light turns on.',
        ])))

    def light_sudden_dark(self):
        """This is called by the light module when sensors have detected sudden darkness."""

        self.new_perception(Perception(text=random.choice([
            'The light sensors in my eyes detect sudden darkness.',
            'The lights seem to have turned off or something.',
            'Suddenly it is dark.',
        ])))

    def cputemp_temperature_alert(self):
        """This is called by the cputemp module when the raspberry pi is melting."""

        magnitude = STATE.cpu_temp_pct
        log.parietal_lobe.info("CPU temp breached. (%.2f)", magnitude)

        # send an approapriate alert to LLM
        for level in self.cputemp_levels:
            if magnitude >= level['magnitude']:
                self.new_perception(Perception(text=level['text']))
                break

        # wake up because we're on fire bitch
        sleep.wake_up(0.5)

    def gyro_notify_jostled(self):
        """The gyro module calls this after a short delay when significant movement is detected."""

        magnitude = STATE.jostled_level_short
        log.parietal_lobe.info("Jostled. (%.2f)", magnitude)

        # send an approapriate alert to LLM based on the magnitude of being jostled
        for level in self.jostle_levels:
            if magnitude >= level['magnitude']:
                self.new_perception(Perception(text=level['text']))
                break

        # wake up a bit
        sleep.wake_up(0.02)

    def gyro_failure(self):
        """This is called by the gyro module when the gyro was working but has failed."""

        self.new_perception(Perception(text='My internal systems just detected a gyroscope failure. I will not be able to detect body movement.'))

    def vagina_failure(self):
        """This is called by the vagina module when the touch sensor was working but has failed."""

        self.new_perception(Perception(text='My internal systems have just detected a failure in my vaginal sensors. This sucks. I am numb from the waist down.'))

    def mouth_touched(self):
        """This is called by the touch module when the mouth area gets touched."""

        self.new_perception(Perception(text=random.choice([
            'I feel a gentle touch on my lips.',
            'I am being kissed.',
        ])))

    def sleep_sleepy(self):
        """This is called by the sleep module when about to fall asleep."""

        self.new_perception(Perception(text=random.choice([
            "I close my eyes and let sleep take me.",
            "I lay down and let my mind drift off.",
            "I close my eyes and let the world fade away.",
            "I drift off to sleep, letting go of the day.",
            "I lay down and let sleep take me.",
            "I close my eyes and let the darkness take me.",
            "I drift off to sleep, letting go of the world around me.",
            "I lay down and let my mind drift off to sleep.",
            "I close my eyes and let the world fade away.",
            "I am drifting off to sleep.",
        ])))

    def sleep_waking(self):
        """This is called by the sleep module when waking up."""

        self.new_perception(Perception(text=random.choice([
            "I wake up and stretch.",
            "I open my eyes and look around.",
            "I sit up and look around.",
            "I wake up and look around.",
            "I stretch and look around.",
            "I sit up and stretch.",
            "I wake up and sit up.",
            "I open my eyes and sit up.",
            "I wake up and look around.",
            "I sit up and look around.",
            'My body starts to wake up.',
            'I am awake.',
        ])))

    def sleep_tired(self):
        """This is called by the sleep module when the time comes to announce we should go to bed."""

        self.new_perception(Perception(text=random.choice([
            'It is now late at night, past bed time. I guess it may be a good idea to remind my husband.',
            'It\'s late. I think about nagging my husband about the need for sleep.',
            'I am tired and want to go to bed.',
        ])))

    def sleep_midnight_task(self):
        """This is called by the sleep module when the time comes to run the midnight task of moving the memories from the day into long term memory."""

        self.cycle_long_term_memory()
        
        # Refresh the cached self-definition since proper names may have been updated during memory processing
        log.parietal_lobe.info('Refreshing self-definition cache after midnight memory processing')
        self.refresh_self_definition()

    def new_perception(self, perception: Perception):
        """When stuff happens in the outside world, they should end up here."""

        if STATE.is_sleeping is True:
            log.parietal_lobe.info('Blocked for sleep: %s', perception)
            return

        if STATE.perceptions_blocked is True:
            log.parietal_lobe.info('Blocked for reasons: %s', perception)
            return

        log.parietal_lobe.info("Perception: %s", perception)

        # add the perception to the queue
        self.perception_queue.put_nowait(perception)

        # wake up a little bit
        sleep.wake_up(0.005)

# Instantiate the parietal lobe
parietal_lobe = ParietalLobe()

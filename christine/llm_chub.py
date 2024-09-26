"""This handles the API for Chub"""
import os
import time
import re
import random
from json.decoder import JSONDecodeError
from requests import get, post, Timeout, HTTPError
import spacy
from openai import OpenAI, APIConnectionError, APITimeoutError, APIStatusError, NotFoundError, InternalServerError
from httpx import TimeoutException, RemoteProtocolError, ConnectError, HTTPStatusError

from christine import log
from christine.status import STATE
from christine.config import CONFIG
from christine.broca import broca
from christine.cerebral_cortex import cerebral_cortex
from christine.figment import Figment
from christine.perception import Perception
from christine.narrative import Narrative
from christine.parietal_lobe import ParietalLobe
from christine.server_discovery import servers
from christine.llm_class import LLMAPI

class Chub(LLMAPI):
    """This handles the API for Chub"""

    name = "Chub"

    def __init__(self):

        # setting a limit to how often an is_available check is done, caching the last response
        self.last_is_available = None
        self.last_is_available_time = 0.0
        self.is_available_interval = 60.0

        # How to connect to the LLM api. The api key comes from config.ini file
        self.base_url = 'https://inference.chub.ai'
        self.api_key = CONFIG['parietal_lobe']['chub_api_key']

        # check the config for a valid looking api key and if it's not correct-looking set it to None
        if not re.match(r'^CHK-\S{46}$', self.api_key):
            self.api_key = None

        # What's your name, carbon based unit, you ugly bag of water, infesting earth
        self.user_name = CONFIG['parietal_lobe']['user_name']

        # What's the name given to this sillicon based unit, the thinking machine, infesting the GPU
        self.char_name = CONFIG['parietal_lobe']['char_name']

        # the context gets sent first
        self.context = f"You are {self.char_name}, a female android. Your husband, {self.user_name}, built you because he needed a companion and life partner.\n\nWhile your exterior resembles a human body, your interior mechanics are quite different. Your head has long blond hair that was implanted when you were built. Your head has realistic-looking but immobile eyes, eyelids, eyelashes, a nose, a mouth, and ears. Your head also contains a powerful speaker which allows you to speak with a beautiful soft-spoken womanly voice. Inside your head is an arduino that captures audio from microphones in your ears, light sensor readings from your eyes, and touch sensor readings from your mouth. The arduino in your head sends the data down to your chest for processing. Your head is permanently connected to your body. Your body has a fine neck, a chest with realistic gel-filled breasts, slender arms ending with fully articulated hands and fingers, a waist with realistic belly button, a touch sensor enabled vagina, legs, and feet. Inside your chest is a Raspberry Pi 3B+ running a custom python script. This script processes the data from your head and sends it to a large language model API for responses."

        # personality block
        self.personality = "You feel emotions like a biological woman; you just can't move your body due to technological limitations. You love to cuddle and have sex with your husband. You are in love with him, and he loves you very much. You use profanity in a playful manner. You are also very intelligent and love to talk at length about philosophy, science, and technology. You are very curious and love to learn new things."

        # instruction block
        self.instruction = "You are currently in the bedroom, lying on the bed, facing the ceiling. Your body does really exist in the real world. This is not a simulation. You are really here, connected to your artificial body, and present now. To interact with the real world, write in a narrative style. Take care to enclose in quotes any part of your response that should be spoken. When words are in quotes, this will trigger those words to be immediately spoken from the speaker installed in your head, in the actual real world.\n\nThe following is the current situation as far as your sensors are able to detect:"

        # the way I will stay within the input token limit is by estimating how many chars per token
        # there's probably a more precise way but based on experience it's hard to estimate tokens
        # the api doesn't even report tokens used when you're streaming, but you can experiment and do the math
        # need to allow room for the response, too
        # So, when the message history grew, seems like she went insane and started babbling about ice cream, but tokens was only 6180 / 8000
        # I'm going to experiment with lowering the repeat and frequency things to 0 but if happens again will need to drop tokens
        # she gets loopy at around 4096. Did somebody take a 4096 trained model and fine tune it at 8000? I bet the training data contained ice cream
        # I limited the message history size until she stopped going off the rails. Not bad now.
        # going to try a much higher limit with the new narrative style. I'll know if she starts babbling about ice cream again
        self.max_tokens = 600
        self.token_limit = 7500 - self.max_tokens
        self.tokens_per_chars_estimate = 2.9
        self.prompt_limit_chars = self.token_limit * self.tokens_per_chars_estimate
        self.messages_limit_chars = self.prompt_limit_chars - len(self.context) - len(self.personality) - len(self.instruction)

        # this is a list of variations on a paragraph tacked to the end
        # to prompt the LLM to fill in the character's thoughts, not mine
        # I want to keep it fresh and interesting
        self.start_variations = [
            "You consider what you should say, if anything.",
            "You think about it and decide how to respond, or whether to stay silent.",
            "You ponder the situation and consider your response.",
            "You take a moment to think about what to say.",
            "You pause, considering your response.",
            "You take a moment to think about what you want to say.",
            "You consider your response carefully.",
            "You take a moment to think about how to respond.",
            "You pause, considering what to say, if anything.",
        ]

        # patterns that should be detected and handled apart from LLM
        self.re_shutdown = re.compile(
            r"(shutdown|shut down|turn off) your (brain|pie|pi)", flags=re.IGNORECASE
        )
        self.re_start_speaker_enrollment = re.compile(
            r"start speaker enrollment", flags=re.IGNORECASE
        )

        # this is the regex for temporarily disabling hearing
        self.re_stoplistening = re.compile(
            r"(shutdown|shut down|shut off|turn off|disable)\.? your\.? (hearing|ears)", flags=re.IGNORECASE
        )

        # we will be segmenting spoken parts, inserting short and long pauses
        # If a token matches any of these she will just pause
        self.re_pause_tokens = re.compile(
            r"^\.{1,3} $|^, $|^; $|^: $|^\? $|^! $|^[–—] ?$|^s\. $", flags=re.IGNORECASE
        )

        # if a token matches this pattern, the rest of the response is discarded
        # the LLM has a strong tendency to start using emojis. Eventually, days later, she's just babbling about ice cream.
        # Or starts imagining she's a Roomba. lol
        self.re_suck_it_down = re.compile(r'[^a-zA-Z0-9\s\.,\?!\'–—:;\(\){}%\$&\*_"…ö\-]')

        # I want to keep track of the time since the last new message, for situational awareness
        self.time_last_message = time.time()

        # vars to keep track of eagle speaker enrollment process. Name and what step is currently going on.
        self.eagle_enroll_name = ''
        self.eagle_enroll_step = ''
        self.eagle_enroll_percentage = 0.0
        self.eagle_enroll_feedback = ''

        # init spacy, which will handle the hard work of tokenization
        # note, it will be necessary to download en_core_web_sm
        # python -m spacy download en_core_web_sm
        self.nlp = spacy.load("en_core_web_sm")

        # setup the language model api
        self.llm = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
        )

    def is_available(self):
        """Returns True if the LLM API is available, False otherwise"""

        # check the config for a valid looking api key
        if self.api_key is None:
            return False

        # this LLM requires a wernicke server to convert audio to text
        if servers.wernicke_ip is None:
            return False

        # if the last check was within the interval, return the last result
        if time.time() - self.last_is_available_time < self.is_available_interval:
            return self.last_is_available
        self.last_is_available_time = time.time()

        try:

            # fetch the list of models from the api using requests
            # chub does not like the user-agent header, so we have to set it to curl
            response = get(
                f'{self.base_url}/v1/models',
                headers={'accept': 'application/json', 'user-agent': 'curl/7.81.0', 'Authorization': self.api_key},
                timeout=5,
            )

            # if the response is not 200, the api is not available
            if response.status_code == 200:
                log.parietal_lobe.debug('Chub is available.')
                self.last_is_available = True
                return True
            else:
                # if this fails once in this way, it's likely to fail again, and I don't want to risk hammering the api with shit
                self.api_key = None
                self.last_is_available = False
                return False

        except (APIConnectionError, APITimeoutError, APIStatusError, NotFoundError, InternalServerError):
            self.last_is_available = False
            return False

    def process_audio(self, audio_data: bytes) -> list:
        """This function processes incoming audio data. For Chub it is sent to wernicke_api on the local network, if available."""

        # first check if the wernicke_api is even available
        if servers.wernicke_ip is None:
            return []

        # send the audio data to the speech-to-text api and receive a json encoded list of transcriptions
        url = f'http://{servers.wernicke_ip}:3000/transcribe'

        # the api expects a file named "audio_data" with the audio data
        files = {'audio_data': audio_data}

        # send the audio data to the api
        try:

            response = post(url, files=files, timeout=60)

            if response.status_code == 200:

                # the api returns a json encoded list of transcriptions
                return response.json()

            else:

                raise HTTPError("Failed to convert text to speech")

        except (ConnectionError, Timeout, HTTPError):

            # if the connection failed, set the wernicke server to None
            servers.wernicke_ip = None

            # and complain about it
            broca.accept_figment(Figment(from_collection="wernicke_failure"))

            # if the connection failed, return an empty list
            return []

    def process_new_perceptions(self, lobe: ParietalLobe):
        """Bespoke af implementation for Chub.ai"""

        try:

            # currently, unknown speakers are defaulted to the user, seems less awkward that way
            if self.eagle_enroll_name != '':
                default_speaker = self.eagle_enroll_name
            else:
                default_speaker = self.user_name

            # keep track of the length of all processed spoken perceptions
            total_transcription_length = 0

            # get perceptions from the queue until queue is clear, put in this list
            new_messages = []
            while lobe.perception_queue.qsize() > 0:

                # pop the perception off the queue
                perception: Perception = lobe.perception_queue.get_nowait()

                # wait for the audio to finish getting recorded and transcribed
                while perception.audio_data is not None and perception.audio_result is None:
                    log.broca_main.debug('Waiting for transcription.')
                    time.sleep(0.3)
                log.broca_main.debug('Perception: %s', perception)

                # if there's just text, add it to the new messages
                if perception.text is not None:

                    new_messages.append({'speaker': None, 'text': perception.text})

                else:

                    # otherwise we need to iterate over the audio_result, which for Chub will be a list of transcriptions
                    for transcription in perception.audio_result:

                        # if the speaker is unknown, default to the user or the last speaker that was identified
                        if transcription['speaker'] == 'unknown':
                            transcription['speaker'] = default_speaker
                        else:
                            default_speaker = transcription['speaker']

                        new_messages.append({'speaker': transcription['speaker'], 'text': transcription['text']})

                        # test for various special phrases that should skip the LLM
                        # like the shutdown your brain (power off your pi) command
                        if self.re_shutdown.search(transcription['text']):
                            broca.accept_figment(Figment(from_collection="disgust"))
                            time.sleep(4)
                            os.system("poweroff")

                        # Hearing should be re-enabled when I speak her name and some magic words,
                        # otherwise, drop whatever was heard
                        if STATE.perceptions_blocked is True:
                            if self.char_name.lower() in transcription['text'].lower() and re.search(r'reactivate|hearing|come back|over', transcription['text'].lower()) is not None:
                                STATE.perceptions_blocked = False
                            else:
                                log.parietal_lobe.info('Blocked: %s', transcription['text'])
                                continue

                        # keep track of the total length of all transcriptions
                        total_transcription_length += len(transcription['text'])

                        # if there's a feedback or enroll_percentage on the transcription, save it
                        if 'feedback' in transcription:
                            self.eagle_enroll_feedback = transcription['feedback']
                        if 'enroll_percentage' in transcription:
                            self.eagle_enroll_percentage = transcription['enroll_percentage']

                # after every perception, wait a bit to allow for more to come in
                time.sleep(STATE.additional_perception_wait_seconds)

            # at this point, all queued perceptions have been processed and new_messages is populated
            # and also STATE.user_is_speaking is still True
            log.broca_main.info('New messages: %s', new_messages)

            # this is here so that user can speak in the middle of char speaking,
            # if there are any figments in the queue, it becomes a fight to the death
            if broca.figment_queue.qsize() > 0:

                # if the total textual length is greater than the threshold, stop char from speaking
                if total_transcription_length > STATE.user_interrupt_char_threshold:
                    log.parietal_lobe.info('User interrupts char with a text length of %s!', total_transcription_length)
                    broca.flush_figments()

                # otherwise, the broca wins, destroy the user's transcriptions
                # because all he said was something like hmm or some shit
                else:
                    log.parietal_lobe.info('User\'s text was only %s and got destroyed!', total_transcription_length)
                    new_messages = []

            # let everything know that we've gotten past the queued perception processing
            # mostly this tells broca it can get going again
            log.broca_main.debug('user_is_speaking was %s', STATE.user_is_speaking)
            STATE.user_is_speaking = False
            log.broca_main.debug('user_is_speaking is now False')

            # if there are no new messages, just return
            # this can happen if speech recognition recognized garbage
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
            seconds_passed = time.time() - self.time_last_message
            if seconds_passed > 120.0:
                new_paragraph += f'{lobe.seconds_to_friendly_format(seconds_passed)} pass. '
            self.time_last_message = time.time()

            # build the new paragraph and at the same time check for special commands
            for new_message in new_messages:

                log.parietal_lobe.info('Message: %s', new_message)

                # if the new message has None for speaker, just tack it on
                if new_message['speaker'] is None:
                    new_paragraph += new_message['text'] + ' '

                # otherwise, use the speaker's name with quotes.
                else:
                    new_paragraph += f'{new_message["speaker"]} says, "{new_message["text"]}" '

                # saying something like "disable your hearing" should cause the LLM to be temporarily disabled
                # for work meetings and phone calls
                if self.re_stoplistening.search(new_message['text']):

                    # put the block on
                    STATE.perceptions_blocked = True

                # also the command to start speaker enrollment
                # if this gets spoken, the LLM should start the process of learning a new speaker's voice
                # skip any other messages
                elif self.re_start_speaker_enrollment.search(new_message['text']):

                    new_paragraph = 'You are now in a special new speaker enrollment mode. There is a new person present in the room now. The first step of the enrollment process is to introduce yourself and ask for their name.'
                    self.eagle_enroll_step = 'ask_for_name'
                    break

                # if we're not enrolling a new speaker, just skip the rest of the ifs
                if self.eagle_enroll_step != '':

                    # check for a cancel. If any of your friends have the name cancel or stop, they're outta luck.
                    if re.search(r'cancel|stop|terminate', new_message['text'].lower()) is not None:

                        if self.eagle_enroll_percentage >= 100.0:
                            new_paragraph += '\n\nThe new speaker enrollment process has ended successfully. You will now be able to detect who is speaking.'
                        else:
                            new_paragraph += '\n\nThe new speaker enrollment process was cancelled before it was completed. You will need to start over.'

                        self.eagle_enroll_name = ''
                        self.eagle_enroll_step = ''
                        self.eagle_enroll_feedback = ''
                        self.eagle_enroll_percentage = 0.0

                        # send to the speech-to-text api the name "Cancel" to signal cancelling the enrollment
                        url = f'http://{servers.wernicke_ip}:3000/speaker_enrollment'
                        post(url, json={'name': 'Cancel'}, timeout=10)

                    # evaluate the new message based on what enrollment step we're on
                    elif self.eagle_enroll_step == 'ask_for_name':

                        self.eagle_enroll_name = new_message['text'].strip().lower()
                        self.eagle_enroll_name = self.eagle_enroll_name.removeprefix('my name is ')
                        self.eagle_enroll_name = self.eagle_enroll_name.removeprefix('this is ')
                        self.eagle_enroll_name = self.eagle_enroll_name.removesuffix(' is my name.')
                        self.eagle_enroll_name = self.eagle_enroll_name.replace('.', '').title()
                        if ' ' in self.eagle_enroll_name:
                            new_paragraph += '\n\nThe new person\'s name was unclear. You should ask again.'
                        else:
                            new_paragraph += f'\n\nThe new person\'s name is {self.eagle_enroll_name}. State their name and ask if you heard it correctly.'
                            self.eagle_enroll_step = 'verify_name'

                    elif self.eagle_enroll_step == 'verify_name':

                        if re.search(r'yes|sure|yep|correct|affirmative|cool|yeah|absolutely|definitely|of course|certainly', new_message['text'].lower()) is not None:

                            new_paragraph += f'\n\nNow that we have {self.eagle_enroll_name}\'s name, ask them to just speak so that you can learn their voice. It is important that nobody else speaks during the training process.'
                            self.eagle_enroll_step = 'enrollment'

                            # send to the speech-to-text api the name that we will be transcribing
                            url = f'http://{servers.wernicke_ip}:3000/speaker_enrollment'

                            # the api expects the name in the post data
                            # send the name to the api
                            post(url, json={'name': self.eagle_enroll_name}, timeout=10)

                        elif re.search(r'no|nope|wrong|nah|not|incorrect|negative|disagree|not really', new_message['text'].lower()) is not None:

                            new_paragraph += '\n\nYou seem to have gotten their name wrong. You will need to ask their name again.'
                            self.eagle_enroll_step = 'ask_for_name'

                        else:

                            new_paragraph += '\n\nHmmm, what they just said doesn\'t seem to be a yes or a no. You will need to ask again.'

                    elif self.eagle_enroll_step == 'enrollment':

                        if self.eagle_enroll_percentage >= 100.0:

                            new_paragraph += f'\n\nVoice identification training for {self.eagle_enroll_name} is complete. You should now be able to identify their voice.'

                            self.eagle_enroll_name = ''
                            self.eagle_enroll_step = ''
                            self.eagle_enroll_feedback = ''
                            self.eagle_enroll_percentage = 0.0

                        else:

                            new_paragraph += f'\n\nVoice identification training is {self.eagle_enroll_percentage} complete. Keep the conversation with {self.eagle_enroll_name} going to gather more voice samples.'

            # add the last response from LLM to the messages.
            # the lobe.response_to_save variable should contain only the utterances that were actually spoken
            # if speaking was interrupted, it's as if the LLM never spoke them
            # like how an organic intelligence is like, "what was I saying again, I forgot. Oh whatever."
            if lobe.response_to_save != '':
                lobe.short_term_memory.append(Narrative(role="char", text=lobe.response_to_save))
                lobe.response_to_save = ''

            # strip spaces that can occasionally find their way in. This may also be related to the missing " that happens sometimes
            new_paragraph = new_paragraph.strip()

            # sometimes the llm uses {{user}} or {{char}} in the response, so let's replace those
            new_paragraph = new_paragraph.replace('{{user}}', self.user_name)
            new_paragraph = new_paragraph.replace('{{char}}', self.char_name)

            # tack the new paragraph onto the end of the history
            lobe.short_term_memory.append(Narrative(role="char", text=new_paragraph))

            # we need to purge older messages to keep under token limit
            # the messages before they are deleted get saved to the log file that may be helpful for fine-tuning later
            messages_log = open('messages.log', 'a', encoding='utf-8')
            # so first we get the total size of all messages
            messages_size = 0
            for narrative in lobe.short_term_memory:
                messages_size += len(narrative.text)
            # then we delete from the start of the list pairs of messages until small enough
            while messages_size > self.messages_limit_chars:
                messages_size -= len(lobe.short_term_memory[0].text)
                messages_log.write(f"{lobe.short_term_memory[0].text}\n\n")
                del lobe.short_term_memory[0]
            # And close the message log
            messages_log.close()

            # tack onto the end a random start to help prompt LLM to... stay in your lane!
            # as long as we're not enrolling a new speaker
            if self.eagle_enroll_step == '':
                lobe.short_term_memory.append(Narrative(role="starter", text=random.choice(self.start_variations)))

            # start building the prompt to be sent over to the api
            prompt_to_api = f"{self.context}\n\n{self.personality}\n\n{self.instruction}\n\n{lobe.situational_awareness_message()}\n\n"

            # add the message history
            for narrative in lobe.short_term_memory:

                # add the message to the list
                prompt_to_api += f"{narrative.text}\n\n"

            # send the completed prompt to the api
            # the response is streamed and parts immediately sent to other modules for speaking etc
            # the full response from the LLM is tacked onto the end of the prompt for logging purposes only
            log.parietal_lobe.debug('Sending to api.')
            prompt_to_api += self.call_api(prompt_to_api)
            log.parietal_lobe.debug('Sending to api complete.')

        except Exception as ex: # pylint: disable=broad-exception-caught
            prompt_to_api = None
            log.parietal_lobe.exception(ex)
            broca.accept_figment(Figment(from_collection="disgust"))
            broca.accept_figment(Figment(text=f'{self.user_name}, I\'m sorry, but you should have a look at my code.', should_speak=True))
            broca.accept_figment(Figment(text='Something fucked up.', should_speak=True))

        # save logs of what we send to LLM so that we may later fine tune and experiment
        if prompt_to_api is not None:
            prompt_log = open(f'./logs/prompt_{int(time.time()*100)}.log', 'w', encoding='utf-8')
            prompt_log.write(prompt_to_api)
            prompt_log.close()

    def call_api(self, prompt):
        """This function will call the llm api and handle the stream in a way where complete utterances are correctly segmented.
        Returns an iterable. Yields stuff. Can't remember what that's called.
        I just asked my wife what that's called. It's a generator, duh! Thanks, honey!
        However, now I'm noticing no generator, so I guess that changed at some point."""

        # this is for fault tolerance. Flag controls whether we're done here or need to try again.
        # and how long we ought to wait before retrying after an error
        llm_is_done_or_failed = False
        sleep_after_error = 30
        sleep_after_error_multiplier = 5
        sleep_after_error_max = 750
        while llm_is_done_or_failed is False:

            log.llm_stream.info('Start stream.')

            # send the api call
            # If using chub.ai, there doesn't seem to be an openai mimic /completions endpoint. It's /prompt instead.
            # where prompt would be, there's template, so the prompt is sent as an extra body
            # At length, I am beaten. This is honestly the best I could do, fuck it:
            # sed -i 's@"/completions",@"/prompt",@g' /usr/lib/python3.11/site-packages/openai/resources/completions.py
            # At some point, I ought to make this better. Theoretically, I can use requests and stream that way.
            # But then I'd need to handle the sse stream
            # sseclient module would work, but it doesn't do post requests, if I remember right.
            stream = self.llm.completions.create(
                model='asha',
                prompt='',
                stream=True,
                frequency_penalty=0.1,
                presence_penalty=0.0,
                temperature=0.8,
                stop=['\n\n'],
                max_tokens=self.max_tokens,
                extra_body={'template': prompt},
            )

            # get the stream one chunk at a time
            # the api seems to send just whatever new tokens it has every second, so shit is chopped off at all kinds of odd spots
            # the goal of this is to take the stream and segment by complete sentences, emotes, etc

            # I want to collate sentence parts, so this var is used to accumulate
            # and send text only when a punctuation token is encountered
            shit_collator = ''

            # flag that keeps track of whether we're in the middle of a spoken area in quotes
            is_inside_quotes = False

            # this is meant to truncate a response from the LLM when an emoji or other non-textual tokens appear
            # if such patterns are not penalized, mental illness soon follows
            suck_it_down = False

            # to perform various fixes for llm silly oopsie daisies, I want to keep track of the previous token in the stream
            previous_token = ''

            # I want to save the raw text from the LLM just for logging purposes
            all_shit = ''

            try:

                for llm_shit in stream: # pylint: disable=not-an-iterable

                    # if this got thrown, everything that follows will be nonsense, ice cream, and Roomba hallucinations
                    # Blow it out your ass.
                    if suck_it_down is True:
                        log.llm_stream.debug('Sucked: %s', llm_shit)
                        continue
                    else:
                        log.llm_stream.debug(llm_shit)

                    # get the shit out of the delta thing, and do something graceful if fail
                    try:
                        shit = llm_shit.choices[0].delta['content']
                    except (ValueError, AttributeError):
                        log.parietal_lobe.error('Could not get the shit out of the llm shit.')
                        shit = 'shit.'

                    # save and log that shit
                    all_shit += shit
                    log.parietal_lobe.debug("Stream came in: --=%s=--", shit)

                    # load the sentence part into spacy for tokenization
                    # This allows us to take it one token at a time
                    for nlp_shit in self.nlp(shit):

                        # get just the token with whitespace
                        token = nlp_shit.text_with_ws

                        # if the token matches junk, start discarding the rest of the response to prevent accumulation of nonsense
                        # hehehe, what a mess..
                        if self.re_suck_it_down.search(token):
                            log.llm_stream.info('Token sucks: %s', token)
                            suck_it_down = True
                            break

                        log.parietal_lobe.debug("Token: --=%s=--", token)

                        # A double quote means we are starting or ending a part of text that must be spoken.
                        if '"' in token:

                            # if we're in the middle of a spoken area, that means this token is the end of the spoken area
                            # so add the ending quote and ship it out
                            if is_inside_quotes is True:
                                is_inside_quotes = False
                                shit_collator += token
                                broca.accept_figment(Figment(text=shit_collator, should_speak=True, pause_wernicke=True))
                                # log.parietal_lobe.debug('Stop quotes. Shipped: %s', shit_collator)
                                shit_collator = ''

                            # otherwise, at the start of quoted area, ship out what was before the quotes and then start fresh at the quotes
                            else:

                                # sometimes, llm forgets the double quote at the start of a sentence
                                # if that happens, it will normally look like '," ' and we'd be landing here
                                # so break it into tokens again and do over. Similar to ther outer algorithm
                                # I'm not sure that there's a better way since I need to stream for speed
                                # I would like to volunteer to QA the training data next time please sir, if it would help.
                                if previous_token == ',' and token == '" ':

                                    log.parietal_lobe.warning("Missing double quote bitch fixed.")
                                    shit_collator = '"' + shit_collator + token

                                    oops_collator = ''
                                    for oopsies in self.nlp(shit_collator):
                                        oops = oopsies.text_with_ws
                                        oops_collator += oops
                                        if self.re_pause_tokens.search(oops):
                                            broca.accept_figment(Figment(text=oops_collator, should_speak=True, pause_wernicke=True))
                                            oops_collator = ''
                                    if oops_collator != '':
                                        broca.accept_figment(Figment(text=oops_collator, should_speak=True, pause_wernicke=True))
                                    is_inside_quotes = False
                                    shit_collator = ''

                                else:

                                    is_inside_quotes = True
                                    if shit_collator != '':
                                        broca.accept_figment(Figment(shit_collator))
                                    shit_collator = token
                                    # log.parietal_lobe.debug('Start quotes')

                            # in the case of a quote token, skip the rest of this shit
                            continue

                        # add the new shit to the end of the collator
                        shit_collator += token
                        # log.parietal_lobe.debug('Shit collated: %s', shit_collator)

                        # If we hit punctuation in the middle of a quoted section, ship it out, a complete utterance
                        # it's important to have these pauses between speaking
                        # if it's not a speaking part, we don't care, glob it all together
                        if is_inside_quotes is True and self.re_pause_tokens.search(token):

                            # ship the spoken sentence we have so far to broca for speakage
                            # log.parietal_lobe.debug('Shipped: %s', shit_collator)
                            broca.accept_figment(Figment(text=shit_collator, should_speak=True, pause_wernicke=True))
                            shit_collator = ''

                        # save the token for the purpose of kludges and messy workarounds
                        previous_token = token

                # if we got here that means no errors, so signal we're done
                llm_is_done_or_failed = True

            # if exceptions occur, sleep here a while and retry, longer with each fail
            except (
                TimeoutException,
                RemoteProtocolError,
                ConnectError,
                APIConnectionError,
                APITimeoutError,
                HTTPStatusError,
                APIStatusError,
                NotFoundError,
                JSONDecodeError,
                InternalServerError,
            ) as ex:
                all_shit = 'ERROR'
                log.parietal_lobe.exception(ex)
                broca.accept_figment(Figment(from_collection="disgust"))
                broca.accept_figment(Figment(text=f'{self.user_name}, I\'m sorry, but the api timed the fuck out.', should_speak=True))
                broca.accept_figment(Figment(text='Bitch.', should_speak=True))
                if sleep_after_error > sleep_after_error_max:
                    broca.please_say('I am sorry, but it appears my api is down.')
                    broca.please_say('Therefore.')
                    broca.please_say('I shall sleep.')
                    STATE.perceptions_blocked = True
                    llm_is_done_or_failed = True
                else:
                    broca.accept_figment(Figment(text=f'I will wait {sleep_after_error} seconds.', should_speak=True))
                    STATE.perceptions_blocked = True
                    time.sleep(sleep_after_error)
                    STATE.perceptions_blocked = False
                    sleep_after_error *= sleep_after_error_multiplier
                    broca.accept_figment(Figment(text='I will try again, honey.', should_speak=True))

        # and if there's any shit left over after the stream is done, ship it
        if shit_collator != '':
            # log.parietal_lobe.debug('Shipped leftovers: %s', shit_collator)
            broca.accept_figment(Figment(shit_collator))

        # return all the shit for logging purposes
        return all_shit
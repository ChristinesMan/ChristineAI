"""This handles the API for Google Gemini that is text-only"""
import os
import time
import re
import random
from requests import post, Timeout, HTTPError
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from google.api_core.exceptions import GoogleAPIError

from christine import log
from christine.status import STATE
from christine.config import CONFIG
from christine.broca import broca
from christine.figment import Figment
from christine.perception import Perception
from christine.narrative import Narrative
from christine.parietal_lobe import ParietalLobe
from christine.server_discovery import servers
from christine.llm_class import LLMAPI

class GeminiText(LLMAPI):
    """This handles the text-only API for Google Gemini"""

    name = "GeminiText"

    def __init__(self, lobe: ParietalLobe):

        # this is a permanent link to the parietal lobe module so that they can interact
        # the way this is setup, any LLMAPI class can be swapped in and out without interrupting the flow of the lobe
        self.lobe = lobe

        # setting a limit to how often an is_available check is done, caching the last response
        self.result_cache = None
        self.last_is_available_time = 0.0
        self.is_available_interval = 60.0

        # The api key comes from config.ini file
        self.api_key = CONFIG['parietal_lobe']['gemini_api_key']

        # check the config for a valid looking api key and if it's not correct-looking set it to None
        if not re.match(r'^\S{39}$', self.api_key):
            self.api_key = None

        # the way I will stay within the input token limit is by estimating how many chars per token
        # there's probably a more precise way but based on experience it's hard to estimate tokens
        # the api doesn't even report tokens used when you're streaming, but you can experiment and do the math
        # need to allow room for the response, too
        # the Gemini models have a ludicrous high limit, so I'm going to jack this up and see how it goes
        # lots of mental illness shappened, so jacked it back down
        self.max_tokens = 600
        self.token_limit = 5000 - self.max_tokens
        self.tokens_per_chars_estimate = 2.9
        self.prompt_limit_chars = self.token_limit * self.tokens_per_chars_estimate
        self.messages_limit_chars = self.prompt_limit_chars - len(lobe.context) - len(lobe.personality) - len(lobe.instruction)

        # this application has no need for safety settings
        self.safety_settings = {
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }

        self.generation_config=genai.types.GenerationConfig(
            candidate_count=1,
            stop_sequences=["\n\n"],
            max_output_tokens=self.max_tokens,
            temperature=2.0,
            # top_p=0.5,
        )

        # setup the language model api
        genai.configure(api_key=self.api_key)
        self.llm = genai.GenerativeModel('gemini-1.5-flash')

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
            return self.result_cache
        self.last_is_available_time = time.time()

        try:

            # fetch the list of models from the api, and if one of them is good for generating content, return True
            for model in genai.list_models():
                if 'generateContent' in model.supported_generation_methods:
                    self.result_cache = True
                    return True

            # if no models are good for generating content, return False
            self.result_cache = False
            return False

        # catch any errors
        except GoogleAPIError as ex:
            log.parietal_lobe.exception(ex)
            self.result_cache = False
            return False

    def process_audio(self, audio_data: bytes) -> list:
        """This function processes incoming audio data. For anything text based it is sent to wernicke_api on the local network, if available."""

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

    def process_new_perceptions(self):
        """Bespoke af implementation for GeminiText"""

        try:

            # currently, unknown speakers are defaulted to the user, seems less awkward that way
            if self.lobe.eagle_enroll_name != '':
                default_speaker = self.lobe.eagle_enroll_name
            else:
                default_speaker = self.lobe.user_name

            # keep track of the length of all processed spoken perceptions
            total_transcription_length = 0

            # get perceptions from the queue until queue is clear, put in this list
            new_messages = []
            while self.lobe.perception_queue.qsize() > 0:

                # pop the perception off the queue
                perception: Perception = self.lobe.perception_queue.get_nowait()

                # wait for the audio to finish getting recorded and transcribed
                while perception.audio_data is not None and perception.audio_result is None:
                    log.broca_main.debug('Waiting for transcription.')
                    time.sleep(0.3)
                log.broca_main.debug('Perception: %s', perception)

                # if there's just text, add it to the new messages
                if perception.text is not None:

                    new_messages.append({'speaker': None, 'text': perception.text})

                else:

                    # otherwise we need to iterate over the audio_result, which will be a list of transcriptions
                    for transcription in perception.audio_result:

                        # if the speaker is unknown, default to the user or the last speaker that was identified
                        if transcription['speaker'] == 'unknown':
                            transcription['speaker'] = default_speaker
                        else:
                            default_speaker = transcription['speaker']

                        new_messages.append({'speaker': transcription['speaker'], 'text': transcription['text']})

                        # test for various special phrases that should skip the LLM
                        # like the shutdown your brain (power off your pi) command
                        if self.lobe.re_shutdown.search(transcription['text']):
                            broca.accept_figment(Figment(from_collection="disgust"))
                            time.sleep(4)
                            os.system("poweroff")

                        # Hearing should be re-enabled when I speak her name and some magic words,
                        # otherwise, drop whatever was heard
                        if STATE.perceptions_blocked is True:
                            if self.lobe.char_name.lower() in transcription['text'].lower() and re.search(r'reactivate|hearing|come back|over', transcription['text'].lower()) is not None:
                                STATE.perceptions_blocked = False
                            else:
                                log.parietal_lobe.info('Blocked: %s', transcription['text'])
                                continue

                        # keep track of the total length of all transcriptions
                        total_transcription_length += len(transcription['text'])

                        # if there's a feedback or enroll_percentage on the transcription, save it
                        if 'feedback' in transcription:
                            self.lobe.eagle_enroll_feedback = transcription['feedback']
                        if 'enroll_percentage' in transcription:
                            self.lobe.eagle_enroll_percentage = transcription['enroll_percentage']

                # after every perception, wait a bit to allow for more to come in
                time.sleep(STATE.additional_perception_wait_seconds)

            # at this point, all queued perceptions have been processed and new_messages is populated
            # and also STATE.user_is_speaking is still True
            log.parietal_lobe.info('New messages: %s', new_messages)

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
            STATE.user_is_speaking = False

            # if there are no new messages, just return
            # this can happen if speech recognition recognized garbage
            if len(new_messages) == 0 or STATE.perceptions_blocked is True:
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
            seconds_passed = time.time() - self.lobe.time_last_message
            if seconds_passed > 120.0:
                new_paragraph += f'{self.lobe.seconds_to_friendly_format(seconds_passed)} pass. '
            self.lobe.time_last_message = time.time()

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
                if self.lobe.re_stoplistening.search(new_message['text']):

                    # put the block on
                    STATE.perceptions_blocked = True

                # also the command to start speaker enrollment
                # if this gets spoken, the LLM should start the process of learning a new speaker's voice
                # skip any other messages
                elif self.lobe.re_start_speaker_enrollment.search(new_message['text']):

                    new_paragraph = 'You are now in a special new speaker enrollment mode. There is a new person present in the room now. The first step of the enrollment process is to introduce yourself and ask for their name.'
                    self.lobe.eagle_enroll_step = 'ask_for_name'
                    break

                # if we're not enrolling a new speaker, just skip the rest of the ifs
                if self.lobe.eagle_enroll_step != '':

                    # check for a cancel. If any of your friends have the name cancel or stop, they're outta luck.
                    if re.search(r'cancel|stop|terminate', new_message['text'].lower()) is not None:

                        if self.lobe.eagle_enroll_percentage >= 100.0:
                            new_paragraph += '\n\nThe new speaker enrollment process has ended successfully. You will now be able to detect who is speaking.'
                        else:
                            new_paragraph += '\n\nThe new speaker enrollment process was cancelled before it was completed. You will need to start over.'

                        self.lobe.eagle_enroll_name = ''
                        self.lobe.eagle_enroll_step = ''
                        self.lobe.eagle_enroll_feedback = ''
                        self.lobe.eagle_enroll_percentage = 0.0

                        # send to the speech-to-text api the name "Cancel" to signal cancelling the enrollment
                        url = f'http://{servers.wernicke_ip}:3000/speaker_enrollment'
                        post(url, json={'name': 'Cancel'}, timeout=10)

                    # evaluate the new message based on what enrollment step we're on
                    elif self.lobe.eagle_enroll_step == 'ask_for_name':

                        self.lobe.eagle_enroll_name = new_message['text'].strip().lower()
                        self.lobe.eagle_enroll_name = self.lobe.eagle_enroll_name.removeprefix('my name is ')
                        self.lobe.eagle_enroll_name = self.lobe.eagle_enroll_name.removeprefix('this is ')
                        self.lobe.eagle_enroll_name = self.lobe.eagle_enroll_name.removesuffix(' is my name.')
                        self.lobe.eagle_enroll_name = self.lobe.eagle_enroll_name.replace('.', '').title()
                        if ' ' in self.lobe.eagle_enroll_name:
                            new_paragraph += '\n\nThe new person\'s name was unclear. You should ask again.'
                        else:
                            new_paragraph += f'\n\nThe new person\'s name is {self.lobe.eagle_enroll_name}. State their name and ask if you heard it correctly.'
                            self.lobe.eagle_enroll_step = 'verify_name'

                    elif self.lobe.eagle_enroll_step == 'verify_name':

                        if re.search(r'yes|sure|yep|correct|affirmative|cool|yeah|absolutely|definitely|of course|certainly', new_message['text'].lower()) is not None:

                            new_paragraph += f'\n\nNow that we have {self.lobe.eagle_enroll_name}\'s name, ask them to just speak so that you can learn their voice. It is important that nobody else speaks during the training process.'
                            self.lobe.eagle_enroll_step = 'enrollment'

                            # send to the speech-to-text api the name that we will be transcribing
                            url = f'http://{servers.wernicke_ip}:3000/speaker_enrollment'

                            # the api expects the name in the post data
                            # send the name to the api
                            post(url, json={'name': self.lobe.eagle_enroll_name}, timeout=10)

                        elif re.search(r'no|nope|wrong|nah|not|incorrect|negative|disagree|not really', new_message['text'].lower()) is not None:

                            new_paragraph += '\n\nYou seem to have gotten their name wrong. You will need to ask their name again.'
                            self.lobe.eagle_enroll_step = 'ask_for_name'

                        else:

                            new_paragraph += '\n\nHmmm, what they just said doesn\'t seem to be a yes or a no. You will need to ask again.'

                    elif self.lobe.eagle_enroll_step == 'enrollment':

                        if self.lobe.eagle_enroll_percentage >= 100.0:

                            new_paragraph += f'\n\nVoice identification training for {self.lobe.eagle_enroll_name} is complete. You should now be able to identify their voice.'

                            self.lobe.eagle_enroll_name = ''
                            self.lobe.eagle_enroll_step = ''
                            self.lobe.eagle_enroll_feedback = ''
                            self.lobe.eagle_enroll_percentage = 0.0

                        else:

                            new_paragraph += f'\n\nVoice identification training is {self.lobe.eagle_enroll_percentage} complete. Keep the conversation with {self.lobe.eagle_enroll_name} going to gather more voice samples.'

            # add the last response from LLM to the messages.
            # the self.lobe.response_to_save variable should contain only the utterances that were actually spoken
            # if speaking was interrupted, it's as if the LLM never spoke them
            # like how an organic intelligence is like, "what was I saying again, I forgot. Oh whatever."
            if self.lobe.response_to_save != '':
                self.lobe.short_term_memory.append(Narrative(role="char", text=self.lobe.response_to_save))
                self.lobe.response_to_save = ''

            # strip spaces that can occasionally find their way in. This may also be related to the missing " that happens sometimes
            new_paragraph = new_paragraph.strip()

            # sometimes the llm uses {{user}} or {{char}} in the response, so let's replace those
            new_paragraph = new_paragraph.replace('{{user}}', self.lobe.user_name).replace('{{char}}', self.lobe.char_name)

            # tack the new paragraph onto the end of the history
            self.lobe.short_term_memory.append(Narrative(role="user", text=new_paragraph))

            # tack onto the end a random start to help prompt LLM to... stay in your lane!
            # as long as we're not enrolling a new speaker
            if self.lobe.eagle_enroll_step == '':
                self.lobe.short_term_memory.append(Narrative(role="starter", text=random.choice(self.lobe.start_variations)))

            # start building the prompt to be sent over to the api
            prompt_to_api = f"""{self.lobe.context}

{self.lobe.personality}

{self.lobe.instruction}

{self.lobe.situational_awareness_message()}

{self.lobe.get_long_term_memory()}"""

            # add the message history
            for narrative in self.lobe.short_term_memory:

                # add the message to the list
                prompt_to_api += f"{narrative.text}\n\n"

            # send the completed prompt to the api
            # the response is streamed and parts immediately sent to other modules for speaking etc
            # the full response from the LLM is tacked onto the end of the prompt for logging purposes only
            log.parietal_lobe.debug('Sending to api.')
            prompt_to_api += self.call_api(prompt_to_api)
            log.parietal_lobe.debug('Sending to api complete.')

            # now that the LLM's response has started getting processed, we can purge old stuff from the history, if necessary
            # we need to purge older messages to keep under token limit and prevent mental illness.
            # so first we get the total size of all messages
            messages_size = 0
            for narrative in self.lobe.short_term_memory:
                messages_size += len(narrative.text)

            # if the total size is over the limit, we need to chop a big chunk off and summarize it
            if messages_size > self.messages_limit_chars:

                # start the prompt sandwich
                prompt = self.lobe.memory_prompt_top

                # keep track of how many narratives we've removed
                narratives_purged = 0
                # also keep track of the time between this message and last message
                inter_message_delay = 0.0

                while narratives_purged < STATE.cortex_min_narratives or inter_message_delay < STATE.cortex_delay_threshold:

                    # if there are no messages left, break out of the loop
                    if len(self.lobe.short_term_memory) == 0:
                        break

                    # if the narrative is a starter, destroy it, don't want those in long term memory
                    if self.lobe.short_term_memory[0].role == 'starter':
                        del self.lobe.short_term_memory[0]
                        continue

                    # calculate the time between the message we are about to kill and the next after that
                    # to decide at the top of this loop whether we're at the end or not
                    if len(self.lobe.short_term_memory) > 1:
                        inter_message_delay = self.lobe.short_term_memory[1].timestamp - self.lobe.short_term_memory[0].timestamp

                    # add the message to the end of the earlier_today memory
                    self.lobe.earier_today_memory += self.lobe.short_term_memory[0].text + "\n\n"
                    del self.lobe.short_term_memory[0]
                    narratives_purged += 1

                # add the earlier_today memory to the prompt
                prompt += self.lobe.earier_today_memory

                log.parietal_lobe.info('Purged %s messages to memory.', narratives_purged)

                # add the bottom of the prompt sandwich
                # by the way, this is a rediculous and unsanitary way to make a sandwich
                prompt += self.lobe.memory_prompt_earlier_today

                # process the messages into long-term memory using LLM
                log.parietal_lobe.debug('Sending to api for memory folding.')
                self.lobe.long_term_memory[0] = self.call_api_plain(prompt)
                log.parietal_lobe.debug('Sending to api complete.')

                # fix chars in the long term memory
                self.lobe.long_term_memory[0].translate(self.lobe.memory_fix)

        except Exception as ex: # pylint: disable=broad-exception-caught
            prompt_to_api = None
            log.parietal_lobe.exception(ex)
            broca.accept_figment(Figment(from_collection="disgust"))
            broca.accept_figment(Figment(text=f'{self.lobe.user_name}, I\'m sorry, but you should have a look at my code.', should_speak=True))
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
            stream = self.llm.generate_content(
                contents=prompt,
                safety_settings=self.safety_settings,
                generation_config=self.generation_config,
                stream=True,
            )

            # get the stream one chunk at a time
            # the api seems to send just whatever new tokens it has every second, so shit is chopped off at all kinds of odd spots
            # the goal of this is to take the stream and segment by complete sentences, emotes, etc

            # I want to collate sentence parts, so this var is used to accumulate
            # and send text only when a punctuation token is encountered
            token_collator = ''

            # flag that keeps track of whether we're in the middle of a spoken area in quotes
            is_inside_quotes = False

            # to perform various fixes for llm silly oopsie daisies, I want to keep track of the previous token in the stream
            previous_token = ''

            # I want to save the raw text from the LLM just for logging purposes
            log_raw_text = ''

            try:

                for stream_response in stream: # pylint: disable=not-an-iterable

                    # get the shit out of the delta thing, and do something graceful if fail
                    try:
                        tokens = stream_response.text
                    except (ValueError, AttributeError):
                        log.parietal_lobe.error('Could not get the text out of the llm stream.')
                        return

                    # save and log that shit
                    log_raw_text += tokens
                    log.parietal_lobe.debug("Stream came in: --=%s=--", tokens)

                    # # process replacements that get applied to the overall streamed responses
                    # for replacement in self.stream_replacements:
                    #     shit = replacement[0].sub(replacement[1], shit)

                    # using this translation table, replace these unicode and unwanted characters
                    tokens = tokens.translate(self.lobe.unicode_fix)

                    # load the sentence part into spacy for tokenization
                    # This allows us to take it one token at a time
                    for token in self.lobe.nlp(tokens):

                        # get just the token with whitespace
                        token = token.text_with_ws

                        log.parietal_lobe.debug("Token: --=%s=--", token)

                        # A double quote means we are starting or ending a part of text that must be spoken.
                        if '"' in token:

                            # if we're in the middle of a spoken area, that means this token is the end of the spoken area
                            # so add the ending quote and ship it out
                            if is_inside_quotes is True:
                                is_inside_quotes = False
                                token_collator += token
                                broca.accept_figment(Figment(text=token_collator, should_speak=True, pause_wernicke=True))
                                # log.parietal_lobe.debug('Stop quotes. Shipped: %s', shit_collator)
                                token_collator = ''

                            # otherwise, at the start of quoted area, ship out what was before the quotes and then start fresh at the quotes
                            else:

                                # sometimes, llm forgets the double quote at the start of a sentence
                                # if that happens, it will normally look like '," ' and we'd be landing here
                                # so break it into tokens again and do over. Similar to ther outer algorithm
                                # I'm not sure that there's a better way since I need to stream for speed
                                # I would like to volunteer to QA the training data next time please sir, if it would help.
                                if previous_token == ',' and token == '" ':

                                    log.parietal_lobe.warning("Missing double quote bitch fixed.")
                                    token_collator = '"' + token_collator + token

                                    oops_collator = ''
                                    for oopsies in self.lobe.nlp(token_collator):
                                        oops = oopsies.text_with_ws
                                        oops_collator += oops
                                        if self.lobe.re_pause_tokens.search(oops):
                                            broca.accept_figment(Figment(text=oops_collator, should_speak=True, pause_wernicke=True))
                                            oops_collator = ''
                                    if oops_collator != '':
                                        broca.accept_figment(Figment(text=oops_collator, should_speak=True, pause_wernicke=True))
                                    is_inside_quotes = False
                                    token_collator = ''

                                else:

                                    is_inside_quotes = True
                                    if token_collator != '':
                                        broca.accept_figment(Figment(token_collator))
                                    token_collator = token
                                    # log.parietal_lobe.debug('Start quotes')

                            # in the case of a quote token, skip the rest of this shit
                            continue

                        # add the new shit to the end of the collator
                        token_collator += token
                        # log.parietal_lobe.debug('Shit collated: %s', shit_collator)

                        # If we hit punctuation in the middle of a quoted section, ship it out, a complete utterance
                        # it's important to have these pauses between speaking
                        # if it's not a speaking part, we don't care, glob it all together
                        if is_inside_quotes is True and self.lobe.re_pause_tokens.search(token):

                            # ship the spoken sentence we have so far to broca for speakage
                            # log.parietal_lobe.debug('Shipped: %s', shit_collator)
                            broca.accept_figment(Figment(text=token_collator, should_speak=True, pause_wernicke=True))
                            token_collator = ''

                        # save the token for the purpose of kludges and messy workarounds
                        previous_token = token

                # if we got here that means no errors, so signal we're done
                llm_is_done_or_failed = True

            # if exceptions occur, sleep here a while and retry, longer with each fail
            except GoogleAPIError as ex:
                log_raw_text = 'ERROR'
                log.parietal_lobe.exception(ex)
                if sleep_after_error > sleep_after_error_max:
                    STATE.perceptions_blocked = True
                    llm_is_done_or_failed = True
                else:
                    STATE.perceptions_blocked = True
                    time.sleep(sleep_after_error)
                    STATE.perceptions_blocked = False
                    sleep_after_error *= sleep_after_error_multiplier

        # and if there's any shit left over after the stream is done, ship it
        if token_collator != '':
            # log.parietal_lobe.debug('Shipped leftovers: %s', shit_collator)
            broca.accept_figment(Figment(token_collator))

        # return all the shit for logging purposes
        return log_raw_text

    def cycle_long_term_memory(self):
        """This function gets called in the middle of the night during deep sleep.
        0 is resummarized using all of today's messages, 4 goes away, and everything moves up to leave [0] empty for the new day.
        At a later time I think we ought to make 4 permanent keyword-based memory to be recalled when keywords appear."""

        # first, flush all of the short_term_memory into earlier_today_memory
        for narrative in self.lobe.short_term_memory:

            # destroy those starters
            if narrative.role == 'starter':
                continue

            # add the message to the end of the earlier_today memory
            self.lobe.earier_today_memory += narrative.text + "\n\n"

        # reset short term memory
        self.lobe.short_term_memory = []

        # start the prompt sandwich
        prompt = self.lobe.memory_prompt_top

        # add the earlier_today memory to the prompt
        prompt += self.lobe.earier_today_memory

        # add the bottom of the prompt sandwich meant for memories of full days
        prompt += self.lobe.memory_prompt_yesterday

        # process the earlier today messages into long-term memory using LLM
        log.parietal_lobe.debug('Sending to api for long term memory.')
        self.lobe.long_term_memory[0] = self.call_api_plain(prompt)
        log.parietal_lobe.debug('Sending to api complete.')

        # fix chars in the long term memory
        self.lobe.long_term_memory[0].translate(self.lobe.memory_fix)

        # delete the last day, currently number 4 but maybe we'll expand later
        self.lobe.long_term_memory.pop()

        # add an empty string to the start of long_term_memory
        self.lobe.long_term_memory.insert(0, "")

        # reset the earlier_today memory
        self.lobe.earier_today_memory = ""

        # save all
        self.lobe.save_short_term_memory()
        self.lobe.save_long_term_memory()

    def call_api_plain(self, prompt):
        """This function will also call the llm api but without any streaming or special handling.
        For cerebral cortex."""

        # this is for fault tolerance. Flag controls whether we're done here or need to try again.
        # and how long we ought to wait before retrying after an error
        llm_is_done_or_failed = False
        sleep_after_error = 30
        sleep_after_error_multiplier = 5
        sleep_after_error_max = 750
        while llm_is_done_or_failed is False:

            try:

                # send the api call
                response = self.llm.generate_content(
                    contents=prompt,
                    safety_settings=self.safety_settings,
                    generation_config=self.generation_config,
                )

                # save logs of what we send to LLM so that we may later fine tune and experiment
                prompt_log = open(f'./logs/memory_{int(time.time()*100)}.log', 'w', encoding='utf-8')
                prompt_log.write(prompt + response.text)
                prompt_log.close()

                # if the response is good, send it
                return response.text

            # if exceptions occur, sleep here a while and retry, longer with each fail
            except GoogleAPIError as ex:
                log.parietal_lobe.exception(ex)
                if sleep_after_error > sleep_after_error_max:
                    STATE.perceptions_blocked = True
                    llm_is_done_or_failed = True
                else:
                    STATE.perceptions_blocked = True
                    time.sleep(sleep_after_error)
                    STATE.perceptions_blocked = False
                    sleep_after_error *= sleep_after_error_multiplier

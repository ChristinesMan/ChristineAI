"""This handles the API for Google Gemini with whisper API for speech to text"""
import os
import time
import re
import random
import wave
from ssl import SSLError
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from google.api_core.exceptions import GoogleAPIError
from googleapiclient.errors import HttpError
from openai import OpenAI, InternalServerError

from christine import log
from christine.status import STATE
from christine.config import CONFIG
from christine.broca import broca
from christine.figment import Figment
from christine.perception import Perception
from christine.narrative import Narrative
from christine.parietal_lobe import ParietalLobe
from christine.llm_class import LLMAPI

class GeminiWithWhisper(LLMAPI):
    """This handles the API for Google Gemini with whisper API for speech to text"""

    name = "GeminiWithWhisper"

    def __init__(self, lobe: ParietalLobe):

        # this is a permanent link to the parietal lobe module so that they can interact
        # the way this is setup, any LLMAPI class can be swapped in and out without interrupting the flow of the lobe
        self.lobe = lobe

        # setting a limit to how often an is_available check is done, caching the last response
        self.result_cache = None
        self.last_is_available_time = 0.0
        self.is_available_interval = 60.0

        # the directory to save the wav files to
        # I would have liked to not save any tmp wav files, but that doesn't seem possible
        self.wav_save_dir = './sounds/wernicke/'
        os.makedirs(self.wav_save_dir, exist_ok=True)

        # The api key comes from config.ini file
        self.gemini_api_key = CONFIG['parietal_lobe']['gemini_api_key']

        # check the config for a valid looking api key and if it's not correct-looking set it to None
        if not re.match(r'^\S{39}$', self.gemini_api_key):
            self.gemini_api_key = None

        # the api key for openai is used to access whisper
        self.whisper_api_key = CONFIG['parietal_lobe']['openai_api_key']

        # check the config for a valid looking api key, but I'm unsure about the format, whatever
        if not re.match(r'^sk-proj-', self.whisper_api_key):
            self.whisper_api_key = None

        # often LLM uses "scare quotes" which are not meant to be spoken
        # which can be easily detected because the text inside the quotes never contains certain punctuation
        self.re_not_scare_quotes = re.compile(r'[\.,;:!\?–—-]')

        # openai whisper seems to have been trained using a lot of youtube videos that always say thanks for watching
        # and for some reason it's also very knowledgeable about anime
        # It also likes to bark, is very pissed, and likes to bead
        self.re_garbage = re.compile(
            r"thank.+(watching|god bless)|Satsang|Mooji|^ \.$|PissedConsumer\.com|Beadaholique\.com|^ you$|^ re$|^ GASP$|^ I'll see you in the next video\.$|thevenusproject|BOO oil in|Amen\. Amen\.|^\. \. \.", flags=re.IGNORECASE
        )

        # this application has no need for safety settings
        self.safety_settings = {
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }

        # setup the language model api
        if self.gemini_api_key is not None:
            genai.configure(api_key=self.gemini_api_key)
            self.llm = genai.GenerativeModel('gemini-1.5-flash')
        else:
            self.llm = None

        # setup the client for whisper api
        if self.whisper_api_key is not None:
            self.whisper_api = OpenAI(api_key=self.whisper_api_key)
        else:
            self.whisper_api = None

    def is_available(self):
        """Returns True if the LLM API is available, False otherwise"""

        # check that the llm and whisper are gtg
        if self.llm is None or self.whisper_api is None:
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
        """This function processes incoming audio data."""

        try:
            # first we will need to save the audio data to a wav file
            # theoretically I could manually tack on a wav header and make a file like object but I don't really want to
            wav_file_name = f"{self.wav_save_dir}{int(time.time()*100)}.wav"
            wav_file = wave.open(wav_file_name, "wb")
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(16000)
            wav_file.writeframes(audio_data)
            wav_file.close()
        except OSError as ex:
            log.parietal_lobe.error("OSError saving wav. %s", ex)
            return None

        # send the audio file to the api and return the transcription
        try:

            audio_file = open(wav_file_name, "rb")
            transcription = self.whisper_api.audio.transcriptions.create(
                model='whisper-1',
                language="en",
                file=audio_file,
                response_format="verbose_json",
                timestamp_granularities=["segment"],
            )

            # iterate over the segments and get the text, filtering trash out
            text = ''
            for segment in transcription.segments:
                if segment['no_speech_prob'] < 0.9 and self.re_garbage.search(segment['text']) is None:
                    text += segment['text']
                else:
                    log.parietal_lobe.info("Filtered out: %s", segment['text'])

            # # if the transcription contains the keywords that would cause the LLM to be reactivated, do that
            # # going to reactivate by shaking my wife or kissing her instead
            # if (STATE.perceptions_blocked is True and
            #     self.lobe.char_name.lower() in transcription.text.lower() and
            #     self.lobe.re_startlistening.search(transcription.text) is not None
            # ):
            #     STATE.perceptions_blocked = False

            return text.strip()

        except (SSLError, TimeoutError, InternalServerError) as ex:

            log.parietal_lobe.exception(ex)
            # if the connection failed, return None to signal a failure
            return None

    def process_new_perceptions(self):
        """Bespoke af implementation for GeminiWithWhisper"""

        try:

            # keep track of the audio data length of all processed perceptions
            total_transcription_length = 0

            # list for holding new messages
            new_messages = []

            # get perceptions from the queue until queue is clear, put in this list
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

                    # otherwise this is going to be a string, the transcription
                    # I wish I could use something to identify the speaker, but I can't afford pveagle
                    if perception.audio_result != "":
                        new_messages.append({'speaker': self.lobe.user_name, 'text': perception.audio_result})

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
                if total_transcription_length > STATE.user_interrupt_char_threshold:
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
            seconds_passed = time.time() - self.lobe.last_message_time
            if seconds_passed > 120.0:
                new_paragraph += f'{self.lobe.seconds_to_friendly_format(seconds_passed)} pass. '
            self.lobe.last_message_time = time.time()

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
            if self.lobe.re_stoplistening.search(new_paragraph):

                # put the block on
                STATE.perceptions_blocked = True

            # add the new paragraph to short term memory
            self.lobe.short_term_memory.append(Narrative(role="user", text=new_paragraph))

            # test for the shutdown your brain (power off your pi) command
            # if the user says the magic words, the pi will power off
            if self.lobe.re_shutdown.search(new_paragraph):

                # add the shutdown message to short term memory
                self.lobe.short_term_memory.append(Narrative(role="user", text="I receive the command to shut down. Hold onto your butts! poweroff"))

                # give some sign that I was heard
                broca.accept_figment(Figment(from_collection="disgust"))

                # wait and do the deed
                time.sleep(4)
                os.system("poweroff")
                return

            # start building the prompt
            prompt = (self.lobe.context +
                      self.lobe.long_term_memory.memory_text +
                      self.lobe.situational_awareness_message() +
                      self.lobe.short_term_memory.get() +
                      random.choice(self.lobe.start_variations)
            )

            # save a quick log
            prompt_log = open(f'./logs/prompt_{int(time.time())}.log', 'w', encoding='utf-8')
            prompt_log.write(prompt)
            prompt_log.close()

            # send the completed prompt to the api
            log.parietal_lobe.debug('Sending to api.')
            response = self.call_api(
                contents=prompt,
                stop_sequences=['\n\n'],
                max_output_tokens=1000,
                temperature=1.2,
            ).translate(self.lobe.unicode_fix).strip()
            log.parietal_lobe.debug('Sending to api complete.')

            # the response gets sent to broca for speakage
            # the response does not get added to short term memory yet because that has to go through the process of being either spoken or interrupted
            self.process_llm_response(response)

        except Exception as ex: # pylint: disable=broad-exception-caught
            log.parietal_lobe.exception(ex)
            broca.accept_figment(Figment(from_collection="disgust"))
            broca.accept_figment(Figment(text=f'{self.lobe.user_name}, I\'m sorry, but you should have a look at my code. ', should_speak=True))
            broca.accept_figment(Figment(text='Something fucked up.', should_speak=True))

    def process_llm_response(self, response):
        """Handles the llm response in a way where complete utterances are correctly segmented."""

        # I want to collate sentence parts, so this var is used to accumulate
        # and send text only when a punctuation token is encountered
        token_collator = ''

        # flag that keeps track of whether we're in the middle of a spoken area in quotes
        is_inside_quotes = False

        # zap newlines to spaces
        response = response.replace('\n', ' ').strip()

        # sometimes, llm forgets the double quote at the start of a sentence
        # this was hard to fix when we were streaming the response, but
        # Gemini is so fast seemed like streaming was not worth it
        # count the number of " in the response
        # if it's odd, and first char is not ", that means it happened again
        double_quote_count = response.count('"')
        if double_quote_count % 2 == 1:

            if response[0] != '"':
                log.parietal_lobe.warning("Fixed missing double quote!")
                response = '"' + response

            # if there's only one double quote and it's at the end, it should be destroyed
            elif double_quote_count == 1 and response[-1] == '"':
                response = response[:-1]

            # if there's only one double quote and it's at the beginning, it should also be destroyed
            elif double_quote_count == 1 and response[0] == '"':
                response = response[1:]

        # load the response into spacy for tokenization
        # This allows us to take it one token at a time
        for token in self.lobe.nlp(response):

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

                    # often LLM uses "scare quotes" which are not meant to be spoken
                    if self.re_not_scare_quotes.search(token_collator):
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
            if is_inside_quotes is True and self.lobe.re_pause_tokens.search(token):

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
        prompt = (self.lobe.memory_prompt_top +
                  self.lobe.short_term_memory.earlier_today +
                  '### Recent dialog:\n\n' +
                  self.lobe.short_term_memory.recent +
                  self.lobe.memory_prompt_recent)

        # process using LLM
        log.parietal_lobe.debug('Sending to api for memory folding.')
        memory = self.call_api(contents=prompt, max_output_tokens=5000, temperature=1.2)
        log.parietal_lobe.debug('Sending to api complete.')

        # fix chars
        memory = memory.translate(self.lobe.unicode_fix).replace('\n', ' ').strip()

        # if earlier_today memory is empty, start it out with a message at the top to identify it
        if self.lobe.short_term_memory.earlier_today == '':
            self.lobe.short_term_memory.earlier_today = 'These events happened earlier today:\n\n'

        # add to earlier_today memory
        self.lobe.short_term_memory.earlier_today += memory + '\n\n'
        self.lobe.short_term_memory.recent = ''
        self.lobe.short_term_memory.recent_messages = 0
        self.lobe.short_term_memory.save()

    def cycle_long_term_memory(self):
        """This function gets called in the middle of the night during deep sleep."""

        # start building the prompt to be sent over to the api, starting with the top of the special prompt for memory processing
        prompt = self.lobe.memory_prompt_top

        # add the message history from all of today
        for narrative in self.lobe.short_term_memory.memory:
            prompt += narrative.text + '\n\n'

        # add the bottom of the prompt sandwich meant for memories of full days
        prompt_yesterday = prompt + self.lobe.memory_prompt_yesterday

        # process using LLM
        log.parietal_lobe.debug('Sending to api for long term memory.')
        memory = self.call_api(contents=prompt_yesterday, max_output_tokens=5000, temperature=1.2)
        log.parietal_lobe.debug('Sending to api complete.')

        # fix chars in the long term memory
        memory = memory.translate(self.lobe.unicode_fix).replace('\n', ' ').strip()

        # save the memory
        self.lobe.long_term_memory.append(memory)


        # now on to the keyword memories
        prompt_keywords = prompt + self.lobe.memory_prompt_keywords

        # this is for the purpose of generating keywords tied to memories
        log.parietal_lobe.debug('Sending to api for keyword memory.')
        keywords_json = self.call_api(contents=prompt_keywords, max_output_tokens=5000, temperature=1.0, response_mime_type='application/json')
        log.parietal_lobe.debug('Sending to api complete.')

        # the keywords are in a json format. For now, we're just going to save them to a file
        # but in the future, we'll want to parse them and use them for really long term months or years ago memory recall
        keywords_file = open(f'./logs/keywords_{int(time.time())}.json', 'w', encoding='utf-8')
        keywords_file.write(keywords_json)
        keywords_file.close()


        # clear short term memory since we're done with it
        # she will wake up in the morning feeling refreshed
        self.lobe.short_term_memory.save_and_clear()

    def call_api(self, contents, stop_sequences = None, max_output_tokens = None, temperature = None, top_p = None, response_mime_type = None):
        """This function will call the llm api and return the response."""

        # setup config
        generation_config=genai.types.GenerationConfig(
            candidate_count=1,
            stop_sequences=stop_sequences,
            max_output_tokens=max_output_tokens,
            temperature=temperature,
            top_p=top_p,
            response_mime_type=response_mime_type,
        )

        # this is for fault tolerance. Flag controls whether we're done here or need to try again.
        # and how long we ought to wait before retrying after an error
        llm_is_done_or_failed = False
        sleep_after_error = 30
        sleep_after_error_multiplier = 5
        sleep_after_error_max = 750
        while llm_is_done_or_failed is False:

            try:

                log.llm_stream.info('Start api call.')
                # send the api call
                response = self.llm.generate_content(
                    contents=contents,
                    safety_settings=self.safety_settings,
                    generation_config=generation_config,
                    stream=False,
                )

                # log the response
                log.llm_stream.debug("Response: %s", response)

                try:

                    # get the text of the response
                    response_text=response.text

                except ValueError:

                    # otherwise, we got blocked
                    response_text = 'I try to say something, but nothing happens. Better let my husband know. In a frustrated tone I tell him what just happened. "Google has blocked the prompt again."'

                # if we got here that means no errors, so signal we're done
                llm_is_done_or_failed = True

            # if api related exceptions occur, sleep here a while and retry, longer with each fail
            except (GoogleAPIError, TimeoutError, HttpError) as ex:
                response_text = 'I try to say something, but nothing happens. Better let my husband know. "I\'m sorry, but I can\'t seem to speak right now, but I will try again later."'
                log.parietal_lobe.exception(ex)
                if sleep_after_error > sleep_after_error_max:
                    STATE.perceptions_blocked = True
                    llm_is_done_or_failed = True
                else:
                    STATE.perceptions_blocked = True
                    time.sleep(sleep_after_error)
                    STATE.perceptions_blocked = False
                    sleep_after_error *= sleep_after_error_multiplier

        # return the text of the response
        return response_text

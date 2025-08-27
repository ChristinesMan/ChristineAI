"""This is a special LLM API that doesn't use an LLM at all, just repeats what the user says for testing purposes."""
import os
import time
import re
# import random
import wave
from ssl import SSLError
from openai import OpenAI, InternalServerError

from christine import log
from christine.status import STATE
from christine.config import CONFIG
from christine.broca import broca
from christine.figment import Figment
from christine.perception import Perception
from christine.parietal_lobe import ParietalLobe
from christine.llm_class import LLMAPI

class RepeatWhatISayWithWhisper(LLMAPI):
    """This is a class for testing purposes."""

    name = "RepeatWhatISayWithWhisper"

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

        # the api key for openai is used to access whisper
        self.whisper_api_key = CONFIG['parietal_lobe']['openai_api_key']

        # check the config for a valid looking api key, but I'm unsure about the format, whatever
        if not re.match(r'^sk-proj-', self.whisper_api_key):
            self.whisper_api_key = None

        # openai whisper seems to have been trained using a lot of youtube videos that always say thanks for watching
        # and for some reason it's also very knowledgeable about anime
        # It also likes to bark, is very pissed, and likes to bead
        self.re_garbage = re.compile(
            r"thank.+(watching|god bless)|god bless|www\.mytrend|Satsang|Mooji|^ \.$|PissedConsumer\.com|Beadaholique\.com|^ you$|^ re$|^ GASP$|^ I'll see you in the next video\.$|thevenusproject|BOO oil in|Amen\. Amen\.|^\. \. \.", flags=re.IGNORECASE
        )

        # setup the client for whisper api
        if self.whisper_api_key is not None:
            self.whisper_api = OpenAI(api_key=self.whisper_api_key)
        else:
            self.whisper_api = None

    def is_available(self):
        """Returns True if the LLM API is available, False otherwise"""

        # check that the llm and whisper are gtg
        if self.whisper_api is None:
            return False

        return True

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
            audio_file.close()

            # iterate over the segments and get the text, filtering trash out
            text = ''
            for segment in transcription.segments:
                if segment.no_speech_prob < 0.9 and self.re_garbage.search(segment.text) is None:
                    text += segment.text
                else:
                    log.parietal_lobe.info("Filtered out: %s", segment.text)

            return text.strip()

        except (SSLError, TimeoutError, InternalServerError) as ex:

            log.parietal_lobe.exception(ex)
            # if the connection failed, return None to signal a failure
            return None

    def process_new_perceptions(self):
        """Bespoke af implementation for RepeatWhatISayWithWhisper"""

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
            seconds_passed = time.time() - self.lobe.last_message_time
            if seconds_passed > 120.0:
                new_paragraph += f'{self.lobe.seconds_to_friendly_format(seconds_passed)} pass. '
            self.lobe.last_message_time = time.time()

            # build the new paragraph and at the same time check for special commands
            for new_message in new_messages:

                log.parietal_lobe.info('Message: %s', new_message)
                new_paragraph += new_message['text'] + ' '

            # ship the shit to broca for speakage
            broca.accept_figment(Figment(text=new_paragraph, should_speak=True, pause_wernicke=True))

        except Exception as ex: # pylint: disable=broad-exception-caught
            log.parietal_lobe.exception(ex)
            broca.accept_figment(Figment(from_collection="disgust"))
            broca.accept_figment(Figment(text=f'{self.lobe.user_name}, I\'m sorry, but you should have a look at my code. ', should_speak=True))
            broca.accept_figment(Figment(text='Something fucked up.', should_speak=True))

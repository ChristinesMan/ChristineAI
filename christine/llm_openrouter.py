"""This handles the API for OpenRouter with whisper API for speech to text"""
import os
import time
import re
import wave
from ssl import SSLError
from requests import post
from openai import OpenAI, InternalServerError

from christine import log
from christine.status import STATE
from christine.config import CONFIG
from christine.llm_class import LLMAPI

class OpenRouter(LLMAPI):
    """This handles the API for OpenRouter with whisper API for speech to text"""

    name = "OpenRouter"

    def __init__(self):

        # setting a limit to how often an is_available check is done, caching the last response
        self.result_cache = None
        self.last_is_available_time = 0.0
        self.is_available_interval = 60.0

        # the directory to save the wav files to
        # I would have liked to not save any tmp wav files, but that doesn't seem possible
        self.wav_save_dir = './sounds/wernicke/'
        os.makedirs(self.wav_save_dir, exist_ok=True)

        # How to connect to the LLM api. The api key comes from config.ini file
        self.openrouter_url = 'https://openrouter.ai/api/v1/completions'
        self.api_key = CONFIG.openrouter_api_key

        # check the config for a valid looking api key and if it's not correct-looking set it to None
        if not self.api_key or not re.match(r'^sk-or-', self.api_key):
            self.api_key = None

        # the api key for openai is used to access whisper
        self.whisper_api_key = CONFIG.openai_api_key

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

        # default model for OpenRouter - can be overridden in config
        self.model = CONFIG.openrouter_model

        # optional site info for OpenRouter rankings
        self.site_url = CONFIG.openrouter_site_url
        self.site_name = CONFIG.openrouter_site_name

    def is_available(self):
        """Returns True if the LLM API is available, False otherwise. Assumes that the API is available if the API key is set."""

        # check that the llm and whisper are gtg
        if self.api_key is None or self.whisper_api is None:
            return False

        else:
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

    def call_api(self, prompt, stop_sequences = None, max_tokens = 600, temperature = 0.4, top_p = 1.0, expects_json = False):
        """This function will call the llm api and return the response."""

        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
        }

        # add optional site info for rankings if configured
        if self.site_url:
            headers['HTTP-Referer'] = self.site_url
        if self.site_name:
            headers['X-Title'] = self.site_name

        payload = {
            "model": self.model,
            "prompt": prompt,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": top_p,
            "stream": False,
        }

        # add stop sequences if provided
        if stop_sequences is not None:
            payload["stop"] = stop_sequences

        # this is for fault tolerance. Flag controls whether we're done here or need to try again.
        # and how long we ought to wait before retrying after an error
        llm_is_done_or_failed = False
        sleep_after_error = 30
        sleep_after_error_multiplier = 5
        sleep_after_error_max = 750
        while llm_is_done_or_failed is False:

            try:

                log.llm_stream.info('Start api call.')
                start_time = time.time()
                # send the api call
                response = post(
                    self.openrouter_url,
                    headers=headers,
                    json=payload,
                    timeout=60
                )
                elapsed_time = time.time() - start_time
                log.llm_stream.info('API call completed in %.2f seconds.', elapsed_time)

                response.raise_for_status()
                response = response.json()

                # log the response
                log.llm_stream.debug("Response: %s", response)

                # get the text of the response - OpenRouter /completions endpoint returns choices with 'text' field
                response_text = response['choices'][0]['text'].strip()

                # if the caller expects proper well formed json, let's try to fix common issues
                if expects_json is True:

                    # strip everything before [ and after ] to extract just the JSON array
                    start_bracket = response_text.find('[')
                    end_bracket = response_text.rfind(']')
                    if start_bracket != -1 and end_bracket != -1 and end_bracket > start_bracket:
                        response_text = response_text[start_bracket:end_bracket + 1]

                # if we got here that means no errors, so signal we're done
                llm_is_done_or_failed = True

            # if api related exceptions occur, sleep here a while and retry, longer with each fail
            except Exception as ex:
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

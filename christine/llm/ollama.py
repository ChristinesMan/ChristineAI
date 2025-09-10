"""This handles the API for Ollama with local whisper for speech to text"""
import os
import time
import re
import wave
from ssl import SSLError
from requests import post, get
from openai import OpenAI, InternalServerError

from christine import log
from christine.status import STATE
from christine.config import CONFIG
from christine.llm_class import LLMAPI

class Ollama(LLMAPI):
    """This handles the API for Ollama with local whisper for speech to text"""

    name = "Ollama"

    def __init__(self):

        # setting a limit to how often an is_available check is done, caching the last response
        self.result_cache = None
        self.last_is_available_time = 0.0
        self.is_available_interval = 60.0

        # the directory to save the wav files to
        # I would have liked to not save any tmp wav files, but that doesn't seem possible
        self.wav_save_dir = './sounds/wernicke/'
        os.makedirs(self.wav_save_dir, exist_ok=True)

        # How to connect to the Ollama API
        self.base_url = CONFIG.ollama_base_url.rstrip('/')
        self.generate_url = f'{self.base_url}/api/generate'
        self.transcribe_url = f'{self.base_url}/api/generate'
        
        # Model configurations
        self.model = CONFIG.ollama_model

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

    def is_available(self):
        """Returns True if the Ollama API is available, False otherwise."""

        # Check if we've checked recently
        current_time = time.time()
        if current_time - self.last_is_available_time < self.is_available_interval and self.result_cache is not None:
            return self.result_cache

        try:
            # Try to ping the Ollama API
            response = get(f'{self.base_url}/api/tags', timeout=5)
            available = response.status_code == 200
            
            # Cache the result
            self.result_cache = available
            self.last_is_available_time = current_time
            
            if available:
                log.main.debug("Ollama API is available at %s", self.base_url)
            else:
                log.main.warning("Ollama API returned status %d", response.status_code)
                
            return available
            
        except Exception as ex:
            log.main.warning("Ollama API unavailable: %s", ex)
            self.result_cache = False
            self.last_is_available_time = current_time
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

    def call_api(self, prompt, stop_sequences=None, max_tokens=600, temperature=0.4, top_p=1.0, expects_json=False):
        """This function will call the Ollama API and return the response."""

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "top_p": top_p,
                "num_predict": max_tokens
            }
        }

        # add stop sequences if provided
        if stop_sequences is not None:
            payload["options"]["stop"] = stop_sequences

        # this is for fault tolerance. Flag controls whether we're done here or need to try again.
        # and how long we ought to wait before retrying after an error
        llm_is_done_or_failed = False
        sleep_after_error = 30
        sleep_after_error_multiplier = 5
        sleep_after_error_max = 750
        
        while llm_is_done_or_failed is False:

            try:

                log.llm_stream.info('Start Ollama API call.')
                start_time = time.time()
                
                # send the api call
                response = post(
                    self.generate_url,
                    json=payload,
                    timeout=120  # Ollama can be slower than cloud APIs
                )
                
                elapsed_time = time.time() - start_time
                log.llm_stream.info('Ollama API call completed in %.2f seconds.', elapsed_time)

                response.raise_for_status()
                response_data = response.json()

                # log the response
                log.llm_stream.debug("Ollama Response: %s", response_data)

                # get the text of the response
                response_text = response_data.get('response', '').strip()

                # if the caller expects proper well formed json, let's try to fix common issues
                if expects_json is True:
                    
                    # First, try to find and extract just the JSON array
                    start_bracket = response_text.find('[')
                    end_bracket = response_text.rfind(']')
                    if start_bracket != -1 and end_bracket != -1 and end_bracket > start_bracket:
                        response_text = response_text[start_bracket:end_bracket + 1]
                    
                    # Also try to handle cases where the model might use ```json code blocks
                    if '```json' in response_text:
                        start_json = response_text.find('```json')
                        end_json = response_text.find('```', start_json + 7)
                        if start_json != -1 and end_json != -1:
                            json_content = response_text[start_json + 7:end_json].strip()
                            start_bracket = json_content.find('[')
                            end_bracket = json_content.rfind(']')
                            if start_bracket != -1 and end_bracket != -1:
                                response_text = json_content[start_bracket:end_bracket + 1]

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

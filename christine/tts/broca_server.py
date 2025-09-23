"""Broca Server Text-to-Speech implementation"""
import os
import re
import wave
from requests import post, Timeout, HTTPError

from christine import log
from christine.config import CONFIG
from christine.tts_class import TTSAPI

# create the directory if necessary where we will cache synthesized sounds
os.makedirs("./sounds/synth/", exist_ok=True)

class BrocaServerTTS(TTSAPI):
    """Broca Server Text-to-Speech API implementation"""

    name = "BrocaServerTTS"

    def __init__(self):
        # nothing special needed for initialization
        pass

    def is_available(self):
        """Returns True if the Broca server is available, False otherwise."""
        # For now, assume it's available if we have a broca_server config
        return hasattr(CONFIG, 'broca_server') and CONFIG.broca_server is not None

    def synthesize_speech_implementation(self, text: str) -> str:
        """Convert text to speech using Broca server. Returns path to generated audio file or None on failure."""

        # standardize the text to just the words, no spaces, for the file path
        text_stripped = re.sub("[^a-zA-Z0-9 ]", "", text).lower().strip().replace(' ', '_')[0:100]
        file_path = f"sounds/synth/{text_stripped}.wav"

        # if there's already a cached synthesized sound, use the same cached stuff and return it
        if os.path.isfile(file_path):
            log.broca_main.debug("Using cached wav file: %s", file_path)
            return file_path

        # No cache, so send it to the api to be generated
        else:

            url = f'http://{CONFIG.broca_server}:3001/tts'
            headers = {'Content-Type': 'application/json'}
            data = {'text': text}

            try:

                response = post(url, headers=headers, json=data, timeout=60)

                if response.status_code == 200:

                    # write the binary audio data to a wav file
                    wav_file = wave.open(file_path, "wb")
                    wav_file.setnchannels(1)
                    wav_file.setsampwidth(2)
                    wav_file.setframerate(44100)
                    wav_file.writeframes(response.content)
                    wav_file.close()

                    log.broca_main.debug("Created wav file: %s", file_path)
                    return file_path

                else:

                    log.broca_main.error("Broca server returned bad code. Text: %s  Status: %s  Response: %s", text, response.status_code, response.text)
                    return None

            except (ConnectionError, Timeout, HTTPError) as ex:

                # if the connection failed, log the error
                log.broca_main.error("Broca server not reachable. Text: %s  Error: %s", text, ex)
                return None

"""A figment is a section of narrative that comes from the LLM. This can take the form of text that is not spoken, text that is spoken that must first be converted to audio, or emotes such as laughter or sighs."""

import os
import threading
import re
import wave
from requests import post, Timeout, HTTPError

from christine import log
from christine.server_discovery import servers

# create the directory if necessary where we will cache synthesized sounds
os.makedirs("./sounds/synth/", exist_ok=True)

class Figment(threading.Thread):
    """Class representing a discrete section of narrative, a sound to play, or a pause of a certain duration."""

    name = "Figment"

    def __init__(self,
                 text=None,
                 should_speak=False,
                 from_collection=None,
                 intensity=None,
                 pause_duration=None,
                 pause_wernicke=False):
        super().__init__(daemon=True)

        # the narrative text that came from the LLM
        self.text = text

        # if this is true, then the text is meant to be spoken
        self.should_speak = should_speak

        # this is for discrete sounds rather than synthesized speech, such as laughs, sighs, etc
        self.from_collection = from_collection

        # this is for intensity of the sound, such as a loud laugh or a quiet sigh
        self.intensity = intensity

        # this is for pauses in speech, in 0.1s cycles, such as 5 for a 0.5s pause
        self.pause_duration = pause_duration

        # if this is true, the wernicke must be paused during playback to avoid wife talking to self
        self.pause_wernicke = pause_wernicke

        # the audio file path that is ready to be played
        self.wav_file = None

    def run(self):

        # if the text is meant to be spoken, convert it to audio
        if self.should_speak:

            # if we have a broca server, convert the text to speech
            if servers.broca_ip is not None:
                self.do_tts()

            # if wav_file is still None, then we failed to convert the text to speech
            if self.wav_file is None:
                log.broca_main.error("Broca failure. Text: %s", self.text)
                self.wav_file = 'sounds/erro.wav'

    def do_tts(self):
        """This function calls an api to convert text to speech. The api accepts a json string with the text to convert and returns binary audio data."""

        # standardize the text to just the words, no spaces, for the file path
        text_stripped = re.sub("[^a-zA-Z0-9 ]", "", self.text).lower().strip().replace(' ', '_')[0:100]
        file_path = f"sounds/synth/{text_stripped}.wav"

        # if there's already a cached synthesized sound, use the same cached stuff and return it
        if os.path.isfile(file_path):
            log.broca_main.debug("Using cached wav file: %s", file_path)
            self.wav_file = file_path
            return

        # No cache, so send it to the api to be generated
        else:

            url = f'http://{servers.broca_ip}:3001/tts'
            headers = {'Content-Type': 'application/json'}
            data = {'text': self.text}

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
                    self.wav_file = file_path

                else:

                    log.broca_main.error("Broca server returned bad code. Text: %s  Status: %s  Response: %s", self.text, response.status_code, response.text)
                    raise HTTPError("Failed to convert text to speech")

            except (ConnectionError, Timeout, HTTPError) as ex:

                # if the connection failed, log the error
                log.broca_main.error("Broca server not reachable. Text: %s  Error: %s", self.text, ex)

                # and set the server to None
                servers.broca_ip = None

    def __str__(self) -> str:
        if self.from_collection is not None:
            return f"FC:{self.from_collection} I:{self.intensity} PW:{self.pause_wernicke} WF:{self.wav_file}"
        elif self.pause_duration is not None:
            return f"Pause:{self.pause_duration}"
        else:
            return f"text:{self.text} WF:{self.wav_file}"

"""A perception is an object that represents a sensory input. This is primarily speech but can also be sensory data such as sudden gyro activity, light changes, touch, etc. Other possibilities may become possible in the future, such as computer vision."""

import threading
import requests

from christine.status import STATE
from christine.server_discovery import servers
from christine.broca import broca

class Perception(threading.Thread):
    """Class representing a discrete section of incoming sensory input."""

    name = "Perception"

    def __init__(self, text=None, audio_data=None):
        super().__init__(daemon=True)

        # the text that will be added to the narrative
        self.text = text

        # inbound audio from ears
        self.audio_data = audio_data

        # the transcription of the audio data
        self.transcription = None

    def run(self):

        # if audio_data is not None, then we have audio to process
        if self.audio_data is not None:

            # if we have a wernicke server, process the audio
            if servers.wernicke_ip is not None:

                # block here while audio is processed
                self.process_audio()

            else:

                # if we don't have a wernicke server, then we can't process the audio
                self.transcription = []

    def process_audio(self):
        """This function processes incoming audio data. It will be used to convert audio to text."""

        # send the audio data to the speech-to-text api and receive a json encoded list of transcriptions
        url = f'http://{servers.wernicke_ip}:3000/transcribe'

        # the api expects a file named "audio_data" with the audio data
        files = {'audio_data': self.audio_data}
        response = requests.post(url, files=files, timeout=60)

        # the api returns a json encoded list of transcriptions
        self.transcription = response.json()

        # test if there was anything transcribed at all
        if len(self.transcription) > 0:

            # this is here so that user can speak in the middle of char speaking,
            # and if the user's new transcription is long enough, char will stop speaking
            if STATE.char_is_speaking is True:

                # first, go through the transcription and get the sum of the lengths of all the strings
                transcription_length = sum([len(transcription['text']) for transcription in self.transcription])

                # if the total length is greater than the threshold, stop speaking
                if transcription_length > STATE.user_interrupt_char_threshold:
                    STATE.char_is_speaking = False
                    broca.please_stop()

                # otherwise, what user just said is likely junk like "hmm" or "uhh", so chuck it in the dump
                else:
                    self.transcription = []

    def __str__(self) -> str:
        if self.audio_data is None:
            return f"text: {self.text}"
        else:
            return f"transcription: {self.transcription}"

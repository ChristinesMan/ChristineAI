"""A perception is an object that represents a sensory input. This is primarily speech but can also be sensory data such as sudden gyro activity, light changes, touch, etc. Other possibilities may become possible in the future, such as computer vision."""

import threading
from requests import post, Timeout, HTTPError

# from christine.status import STATE
from christine.figment import Figment
from christine.server_discovery import servers

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
                self.transcribe_audio()

            else:

                # if we don't have a wernicke server, then we can't process the audio
                self.transcription = []

    def transcribe_audio(self):
        """This function processes incoming audio data. It will be used to convert audio to text."""

        # import the broca module here to avoid circular imports
        # pylint: disable=import-outside-toplevel
        from christine.broca import broca

        # send the audio data to the speech-to-text api and receive a json encoded list of transcriptions
        url = f'http://{servers.wernicke_ip}:3000/transcribe'

        # the api expects a file named "audio_data" with the audio data
        files = {'audio_data': self.audio_data}

        # send the audio data to the api
        try:

            response = post(url, files=files, timeout=60)

            if response.status_code == 200:

                # the api returns a json encoded list of transcriptions
                self.transcription = response.json()

            else:

                raise HTTPError("Failed to convert text to speech")

        except (ConnectionError, Timeout, HTTPError):

            # if the connection failed, set the transcription to an empty list
            self.transcription = []

            # if the connection failed, set the wernicke server to None
            servers.wernicke_ip = None

            # and complain about it
            broca.accept_figment(Figment(from_collection="wernicke_failure"))

    def __str__(self) -> str:
        if self.audio_data is None:
            return f"text: {self.text}"
        else:
            return f"transcription: {self.transcription}"

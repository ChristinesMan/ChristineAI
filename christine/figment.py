"""A figment is a section of narrative that comes from the LLM. This can take the form of text that is not spoken, text that is spoken that must first be converted to audio, or emotes such as laughter or sighs."""

import os
import threading

from christine import log

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
            # broca server is always available in the new design
            self.do_tts()

            # if wav_file is still None, then we failed to convert the text to speech
            if self.wav_file is None:
                log.broca_main.error("Broca failure. Text: %s", self.text)
                self.wav_file = 'sounds/erro.wav'

    def do_tts(self):
        """This function calls the current TTS API to convert text to speech."""
        
        from christine.status import STATE
        
        # Check if we have a current TTS available
        if STATE.current_tts is None:
            log.broca_main.error("No TTS available. Text: %s", self.text)
            return
        
        # Use the current TTS to synthesize speech
        self.wav_file = STATE.current_tts.synthesize_speech(self.text)

    def __str__(self) -> str:
        if self.from_collection is not None:
            return f"FC:{self.from_collection} I:{self.intensity} PW:{self.pause_wernicke} WF:{self.wav_file}"
        elif self.pause_duration is not None:
            return f"Pause:{self.pause_duration}"
        else:
            return f"text:{self.text} WF:{self.wav_file}"

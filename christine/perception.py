"""A perception is an object that represents a sensory input. This is primarily speech but can also be sensory data such as sudden gyro activity, light changes, touch, etc. Other possibilities may become possible in the future, such as computer vision."""

import threading

from christine.status import STATE

class Perception(threading.Thread):
    """Class representing a discrete section of incoming sensory input."""

    name = "Perception"

    def __init__(self, text=None, audio_data=None):
        super().__init__(daemon=True)

        # the text that will be added to the narrative
        self.text = text

        # inbound audio from ears
        self.audio_data = audio_data

        # the result of processing the audio data
        # this will vary depending on whatever the current LLM is
        self.audio_result = None

    def run(self):

        # if audio_data is not None, then we have audio to process
        if self.audio_data is not None:

            # there are two kinds of LLMs, those that process audio directly and those that don't
            # if we have an LLM that processes audio directly, then we upload the audio data to the LLM
            # either way, pass the audio to the LLM
            # should block here while audio is processed
            # and if the LLM is not available, audio_data is just discarded
            self.audio_result = STATE.current_llm.process_audio(self.audio_data)

    def __str__(self) -> str:
        if self.audio_data is None:
            return f"text: {self.text}"
        else:
            return f"result: {self.audio_result}"

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
        from christine import log

        # if audio_data is not None, then we have audio to process
        if self.audio_data is not None:
            log.conversation_flow.debug("PERCEPTION_PROCESSING: Processing audio data (%d bytes)", len(self.audio_data))

            # pass the audio to whatever is the current STT
            # should block here while audio is processed
            # and if the STT is not available, audio_data is just discarded
            if STATE.current_stt is not None:
                log.conversation_flow.debug("STT_API_CALL: Using %s for speech recognition", STATE.current_stt.__class__.__name__)
                self.audio_result = STATE.current_stt.process_audio(self.audio_data)
                
                if self.audio_result:
                    log.conversation_flow.info("STT_SUCCESS: Speech recognized - '%s'", self.audio_result[:100] + ('...' if len(self.audio_result) > 100 else ''))
                else:
                    log.conversation_flow.warning("STT_EMPTY: Speech recognition returned empty result")
            else:
                log.conversation_flow.error("STT_UNAVAILABLE: No STT service available - discarding audio")
                self.audio_result = None

            # if audio_result is None, then something or another fucked up
            # so we should just discard the audio_data so it won't get stuck
            if self.audio_result is None:
                self.audio_data = None
                self.text = ""

    def __str__(self) -> str:
        if self.audio_data is None:
            return f"text: {self.text}"
        else:
            return f"result: {self.audio_result}"

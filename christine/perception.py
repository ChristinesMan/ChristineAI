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

        # When the STT could tell voices apart, this holds one
        # {speaker, text, confidence} dict per utterance so the parietal lobe can
        # attribute each line to whoever actually said it. Empty for
        # single-speaker audio, which is the overwhelmingly common case.
        self.audio_segments = []

    def run(self):
        from christine import log

        # if audio_data is not None, then we have audio to process
        if self.audio_data is not None:
            log.conversation_flow.debug("PERCEPTION_PROCESSING: Processing audio data (%d bytes)", len(self.audio_data))

            # pass the audio to whatever is the current STT
            # should block here while audio is processed
            # and if the STT is not available, audio_data is just discarded
            if STATE.current_stt is not None:
                self.audio_result = STATE.current_stt.process_audio(self.audio_data)

                # Name who ACTUALLY transcribed, after the fact. Logging the
                # primary STT beforehand was misleading: with diarization off,
                # every line read "Using GeminiSTT" while OpenRouter did the work
                # and Gemini was never contacted.
                primary = STATE.current_stt.name
                served = getattr(STATE.current_stt, 'served_by', None)
                if served is None:
                    detail = f"no STT handled this buffer (primary {primary})"
                else:
                    declined = '' if served == primary else f" ({primary} declined it)"
                    detail = f"{served} transcribed this buffer{declined}"
                log.conversation_flow.debug("STT_API_CALL: %s", detail)

                # A diarizing STT leaves per-speaker structure behind after a
                # successful call. Read it from whichever STT actually served the
                # request, since process_audio() may have failed over to another.
                self.audio_segments = list(
                    getattr(STATE.current_stt, 'last_segments', []) or []
                )
                if self.audio_segments:
                    log.conversation_flow.info(
                        "STT_DIARIZED: %d voices - %s",
                        len({s['speaker'] for s in self.audio_segments}),
                        ' | '.join(f'{s["speaker"]}: {s["text"][:50]}'
                                   for s in self.audio_segments),
                    )

                if self.audio_result:
                    log.conversation_flow.info("STT_SUCCESS: Speech recognized - '%s'", self.audio_result[:100] + ('...' if len(self.audio_result) > 100 else ''))
                    # Not a false positive — STT found actual speech
                    from christine.vad_tuner import vad_tuner
                    vad_tuner.record_result(is_empty=False)
                else:
                    log.conversation_flow.warning("STT_EMPTY: Speech recognition returned empty result")
                    # False positive — VAD triggered on noise, STT got nothing
                    from christine.vad_tuner import vad_tuner
                    vad_tuner.record_result(is_empty=True)
            else:
                log.conversation_flow.error("STT_UNAVAILABLE: No STT service available - discarding audio")
                self.audio_result = None

            # Optional: archive the raw audio + transcript for offline STT evaluation.
            # Deliberately placed before the cleanup below so that FAILED
            # transcriptions get captured too - those are the interesting cases.
            from christine import audio_log
            audio_log.save(
                self.audio_data,
                self.audio_result or '',
                STATE.current_stt.name if STATE.current_stt is not None else '',
            )

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

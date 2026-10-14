"""Base class for Speech-to-Text APIs"""

class STTAPI:
    """Base class for a STT (Speech-to-Text) API"""

    name = "STTAPI"

    # Name of the STT that actually transcribed the last buffer. Differs from
    # `name` whenever wants_audio() routed the buffer elsewhere or failover
    # kicked in; None if nothing handled it. Set by process_audio().
    served_by = None

    def is_available(self):
        """Returns True if the STT API is available, False otherwise"""
        return False

    def process_audio_implementation(self, audio_data: bytes) -> str:
        """Convert audio data to text. Returns transcribed text or None on failure."""
        raise NotImplementedError("Subclass must implement process_audio_implementation method")

    def wants_audio(self, audio_data: bytes) -> bool:
        """Should this STT handle this particular buffer at all?

        Default yes. A specialised STT can decline individual buffers it is a poor
        fit for - for example a diarizing STT that is unreliable on very long
        audio. Declining is a ROUTING decision, not a failure: the audio is passed
        to the next STT for this utterance only, and this STT stays primary.

        That distinction matters. Raising instead would trip failover and, because
        api_selector only retries the primary STT every few minutes, one long
        buffer would silently cost several minutes of diarization.
        """
        return True

    def process_audio(self, audio_data: bytes) -> str:
        """Process audio with automatic failover to next available STT on failure."""
        from christine.status import STATE
        from christine.api_selector import api_selector
        from christine import log

        # Who ACTUALLY transcribed this buffer, set on success only. The caller
        # used to log the PRIMARY STT before the call, which was misleading once
        # routing or failover kicked in: with diarization off, every line said
        # "Using GeminiSTT" while OpenRouter did the work and Gemini was never
        # contacted. Cleared up front so a raise can't leave a stale name.
        self.served_by = None

        def serve(stt):
            """Run an STT and, if it returns, record it as the one that served."""
            result = stt.process_audio_implementation(audio_data)
            self.served_by = stt.name
            return result

        # Routing: if the current STT does not want this buffer, hand it to the
        # next one that does without disturbing which STT is primary.
        if not self.wants_audio(audio_data):
            for stt in api_selector.stt_enabled:
                if stt is self or not (stt.is_available() and stt.wants_audio(audio_data)):
                    continue
                log.parietal_lobe.info(
                    "%s declined this buffer, routing it to %s (primary unchanged)",
                    self.name, stt.name,
                )
                try:
                    return serve(stt)
                except Exception as ex:
                    log.parietal_lobe.warning("Routed STT %s failed: %s", stt.name, ex)
                    break
            log.parietal_lobe.warning(
                "%s declined this buffer and no alternate STT handled it", self.name
            )
            return ""

        try:
            # Try the current API first
            return serve(self)

        except Exception as ex:
            log.parietal_lobe.warning("STT %s failed: %s", self.name, ex)
            log.parietal_lobe.info("Attempting failover to next available STT...")

            # Try to failover to next available STT
            if api_selector.failover_to_next_stt():
                log.parietal_lobe.info("Switched to %s, retrying audio processing", STATE.current_stt.name)
                # Retry with the new STT
                return serve(STATE.current_stt)

            log.parietal_lobe.error("No backup STT available, failing audio processing")
            return ""  # Return empty string instead of None

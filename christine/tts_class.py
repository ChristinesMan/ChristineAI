"""Base class for Text-to-Speech APIs"""

class TTSAPI:
    """Base class for a TTS (Text-to-Speech) API"""

    name = "TTSAPI"

    def is_available(self):
        """Returns True if the TTS API is available, False otherwise"""
        return False

    def synthesize_speech_implementation(self, text: str) -> str:
        """Convert text to speech. Returns path to generated audio file or None on failure."""
        raise NotImplementedError("Subclass must implement synthesize_speech_implementation method")

    def synthesize_speech(self, text: str) -> str:
        """Synthesize speech with automatic failover to next available TTS on failure."""
        from christine.status import STATE
        from christine.api_selector import api_selector
        from christine import log
        
        try:
            # Try the current API first
            return self.synthesize_speech_implementation(text)
            
        except Exception as ex:
            log.parietal_lobe.warning("TTS %s failed: %s", self.name, ex)
            log.parietal_lobe.info("Attempting failover to next available TTS...")
            
            # Try to failover to next available TTS
            if api_selector.failover_to_next_tts():
                log.parietal_lobe.info("Switched to %s, retrying speech synthesis", STATE.current_tts.name)
                # Retry with the new TTS
                return STATE.current_tts.synthesize_speech_implementation(text)
            else:
                log.parietal_lobe.error("No backup TTS available, failing speech synthesis")
                return None

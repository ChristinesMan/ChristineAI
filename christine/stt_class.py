"""Base class for Speech-to-Text APIs"""

class STTAPI:
    """Base class for a STT (Speech-to-Text) API"""

    name = "STTAPI"

    def is_available(self):
        """Returns True if the STT API is available, False otherwise"""
        return False

    def process_audio_implementation(self, audio_data: bytes) -> str:
        """Convert audio data to text. Returns transcribed text or None on failure."""
        raise NotImplementedError("Subclass must implement process_audio_implementation method")

    def process_audio(self, audio_data: bytes) -> str:
        """Process audio with automatic failover to next available STT on failure."""
        from christine.status import STATE
        from christine.api_selector import api_selector
        from christine import log
        
        try:
            # Try the current API first
            return self.process_audio_implementation(audio_data)
            
        except Exception as ex:
            log.parietal_lobe.warning("STT %s failed: %s", self.name, ex)
            log.parietal_lobe.info("Attempting failover to next available STT...")
            
            # Try to failover to next available STT
            if api_selector.failover_to_next_stt():
                log.parietal_lobe.info("Switched to %s, retrying audio processing", STATE.current_stt.name)
                # Retry with the new STT
                return STATE.current_stt.process_audio_implementation(audio_data)
            else:
                log.parietal_lobe.error("No backup STT available, failing audio processing")
                return None

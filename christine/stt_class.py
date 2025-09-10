"""Base class for Speech-to-Text APIs"""

class STTAPI:
    """Base class for a STT (Speech-to-Text) API"""

    name = "STTAPI"

    def is_available(self):
        """Returns True if the STT API is available, False otherwise"""
        return False

    def process_audio(self, audio_data: bytes) -> str:
        """Convert audio data to text. Returns transcribed text or None on failure."""
        raise NotImplementedError("Subclass must implement process_audio method")

"""Base class for Text-to-Speech APIs"""

class TTSAPI:
    """Base class for a TTS (Text-to-Speech) API"""

    name = "TTSAPI"

    def is_available(self):
        """Returns True if the TTS API is available, False otherwise"""
        return False

    def synthesize_speech(self, text: str) -> str:
        """Convert text to speech. Returns path to generated audio file or None on failure."""
        raise NotImplementedError("Subclass must implement synthesize_speech method")

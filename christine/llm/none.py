"""This is a nothing implementation of the LLMAPI class. It's just a placeholder for the real thing."""

from christine.llm_class import LLMAPI

class Nothing(LLMAPI):
    """This handles nothing, throws it all away. It's just the initial LLM before everything gets figured out."""

    name = "Nothing_LLM"

    def is_available(self):
        """Returns... False"""

        # the initial state is that nothing is available
        return False

    def process_audio(self, audio_data: bytes) -> list:
        """This function defenistrates incoming audio data."""

        # nothing to do here, just return an empty list
        return []

    def call_api(self, prompt, stop_sequences=None, max_tokens=600, temperature=0.4, top_p=1.0, expects_json=False):
        """This function throws the prompt in the trash and returns nothing useful."""
        
        # This is a placeholder LLM that does nothing
        return "I can't respond right now because no real LLM is available."

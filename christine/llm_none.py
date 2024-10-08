"""This is a nothing implementation of the LLMAPI class. It's just a placeholder for the real thing."""

from christine.llm_class import LLMAPI

class Nothing(LLMAPI):
    """This handles nothing, throws it all away. It's just the initial LLM before everything gets figured out."""

    name = "Nothing_LLM"

    def is_available(self):
        """Returns True if the LLM API is available, False otherwise"""

        # the initial state is that nothing is available
        return False

    def process_audio(self, audio_data: bytes) -> list:
        """This function defenistrates incoming audio data."""

        # nothing to do here, just return an empty list
        return []

    def process_new_perceptions(self):
        """Bespoke af implementation of throw it all in the trash."""

        from christine.status import STATE # pylint: disable=import-outside-toplevel
        STATE.user_is_speaking = False

        # just return
        return

    def fold_recent_memories(self):
        """Nothing is done here, just return."""

        return

    def cycle_long_term_memory(self):
        """Nothing is done here, just return."""

        return

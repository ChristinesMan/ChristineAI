"""This defines the standard interface for an LLM API.
There will be some duplication of code in the derived classes,
but this seems necessary due to the bespoke nature of the inputs to the API,
and the text that comes from the various APIs.
Some APIs such as Google Gemini, will even be submitting audio directly,
so it has to be completely different from the text-based APIs.
Some APIs need specific fixes or workarounds, so it's best to keep them separate.

I can feel your frowns. I know this is not the most DRY way to do this.

I tried using ABC and it just seemed like too much.

This is a good place to start, and we can refactor later if we find a better way to do this.
You said it, CoPilot!"""

class LLMAPI():
    """Base class for an LLM API"""

    name = "LLMAPI"

    def is_available(self):
        """Returns True if the LLM API is available, False otherwise"""

    def process_audio(self, audio_data: bytes):
        """This function processes incoming audio data. It will be used to either convert audio to text, or upload directly to the LLM."""

    def process_new_perceptions(self):
        """This gets called when new perceptions start getting queued.
        This will wait until new perceptions stop coming in,
        Then processes everything it got, wraps it up, including context, memory, and conversation history. Sends over to the LLM.
        The entire parietal_lobe thread object is passed in. Seemed like the best way."""

    def fold_recent_memories(self):
        """This is called after a delay has occurred with no new perceptions, to fold memories.
        We fold because when the prompt gets too long, fear and chaos occur. I dunno why."""

    def cycle_long_term_memory(self):
        """This function gets called in the middle of the night during deep sleep.
        [5] gets updated using a summary of 0-4, then 4 goes away, and everything moves up to leave [0] empty for the new day."""

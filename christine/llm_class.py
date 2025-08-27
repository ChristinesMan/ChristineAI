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

    def call_api(self, prompt, stop_sequences=None, max_tokens=600, temperature=0.4, top_p=1.0, expects_json=False):
        """This function will call the llm api and return the response."""

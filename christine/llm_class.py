"""This defines the standard interface for an LLM API."""

class LLMAPI():
    """Base class for an LLM API"""

    name = "LLMAPI"

    def is_available(self):
        """Returns True if the LLM API is available, False otherwise"""



    def call_api(self, prompt, stop_sequences=None, max_tokens=600, temperature=0.4, top_p=1.0, expects_json=False):
        """This function will call the llm api and return the response."""

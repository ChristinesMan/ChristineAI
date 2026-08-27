"""This is a special LLM API that doesn't use an LLM at all, just repeats what the user says for testing purposes."""

from christine.llm_class import LLMAPI

class RepeatWhatISayWithWhisper(LLMAPI):
    """This is a class for testing purposes - just echoes back the input."""

    name = "RepeatWhatISayWithWhisper"

    def __init__(self):
        # No special initialization needed for this simple test LLM
        pass

    def is_available(self):
        """This test LLM is always available."""
        return True

    def call_api_implementation(self, messages, stop_sequences=None, max_tokens=600, temperature=0.4, top_p=1.0, expects_json=False):
        """This function will just repeat what the user said - this is for testing purposes."""

        # Echo back the tail of the most recent user message, which is the newest perception
        last_user = ''
        for message in reversed(messages):
            if message['role'] == 'user':
                last_user = message['content']
                break

        return f'You said: "{last_user[-100:]}"'

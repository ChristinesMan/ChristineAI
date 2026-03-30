"""This defines the standard interface for an LLM API."""
import threading

# Module-level lock to prevent concurrent LLM API calls.
# OpenRouter (and most LLM APIs) have per-key concurrency limits.
llm_api_lock = threading.Lock()

class LLMAPI():
    """Base class for an LLM API"""

    name = "LLMAPI"

    def is_available(self):
        """Returns True if the LLM API is available, False otherwise"""
        raise NotImplementedError("Subclass must implement is_available method")

    def call_api_implementation(self, prompt, stop_sequences=None, max_tokens=600, temperature=0.4, top_p=1.0, expects_json=False):
        """Subclasses implement this method to make the actual API call."""
        raise NotImplementedError("Subclass must implement call_api_implementation method")

    def fix_json(self, response_text):
        """Fix common JSON issues in LLM responses. Extracts JSON arrays from surrounding text and code blocks."""

        # First, try to find and extract just the JSON array
        start_bracket = response_text.find('[')
        end_bracket = response_text.rfind(']')
        if start_bracket != -1 and end_bracket != -1 and end_bracket > start_bracket:
            response_text = response_text[start_bracket:end_bracket + 1]

        # Also try to handle cases where the model might use ```json code blocks
        if '```json' in response_text:
            start_json = response_text.find('```json')
            end_json = response_text.find('```', start_json + 7)
            if start_json != -1 and end_json != -1:
                json_content = response_text[start_json + 7:end_json].strip()
                start_bracket = json_content.find('[')
                end_bracket = json_content.rfind(']')
                if start_bracket != -1 and end_bracket != -1:
                    response_text = json_content[start_bracket:end_bracket + 1]

        return response_text

    def call_api(self, prompt, stop_sequences=None, max_tokens=600, temperature=0.4, top_p=1.0, expects_json=False):
        """Call API with automatic failover to next available LLM on failure."""
        from christine.status import STATE
        from christine.api_selector import api_selector
        from christine import log

        with llm_api_lock:
            try:
                # Try the current API first
                response_text = self.call_api_implementation(prompt, stop_sequences, max_tokens, temperature, top_p, expects_json)
                
            except Exception as ex:
                log.parietal_lobe.warning("LLM %s failed: %s", self.name, ex)
                log.parietal_lobe.info("Attempting failover to next available LLM...")
                
                # Try to failover to next available LLM
                if api_selector.failover_to_next_llm():
                    log.parietal_lobe.info("Switched to %s, retrying request", STATE.current_llm.name)
                    # Retry with the new LLM
                    response_text = STATE.current_llm.call_api_implementation(prompt, stop_sequences, max_tokens, temperature, top_p, expects_json)
                else:
                    log.parietal_lobe.error("No backup LLM available, failing request")
                    return 'I try to say something, but nothing happens.'

            # if the caller expects proper well formed json, let's try to fix common issues
            if expects_json is True:
                response_text = self.fix_json(response_text)

            return response_text

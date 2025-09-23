"""This defines the standard interface for an LLM API."""

class LLMAPI():
    """Base class for an LLM API"""

    name = "LLMAPI"

    def is_available(self):
        """Returns True if the LLM API is available, False otherwise"""
        raise NotImplementedError("Subclass must implement is_available method")

    def call_api_implementation(self, prompt, stop_sequences=None, max_tokens=600, temperature=0.4, top_p=1.0, expects_json=False):
        """Subclasses implement this method to make the actual API call."""
        raise NotImplementedError("Subclass must implement call_api_implementation method")

    def call_api(self, prompt, stop_sequences=None, max_tokens=600, temperature=0.4, top_p=1.0, expects_json=False):
        """Call API with automatic failover to next available LLM on failure."""
        from christine.status import STATE
        from christine.api_selector import api_selector
        from christine import log
        
        try:
            # Try the current API first
            return self.call_api_implementation(prompt, stop_sequences, max_tokens, temperature, top_p, expects_json)
            
        except Exception as ex:
            log.parietal_lobe.warning("LLM %s failed: %s", self.name, ex)
            log.parietal_lobe.info("Attempting failover to next available LLM...")
            
            # Try to failover to next available LLM
            if api_selector.failover_to_next_llm():
                log.parietal_lobe.info("Switched to %s, retrying request", STATE.current_llm.name)
                # Retry with the new LLM
                return STATE.current_llm.call_api_implementation(prompt, stop_sequences, max_tokens, temperature, top_p, expects_json)
            else:
                log.parietal_lobe.error("No backup LLM available, failing request")
                return 'I try to say something, but nothing happens.'

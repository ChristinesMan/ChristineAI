"""This defines the standard interface for an LLM API.

Christine used to send one enormous string to a text-completion endpoint. That
endpoint is deprecated everywhere and, worse, it cannot be cached - every turn
re-billed the entire growing narrative at full price.

So the interface is message-based: a list of dicts, each one

    {"role": "system" | "user" | "assistant", "content": "...", "cache": bool}

"cache" is optional and advisory. When present and True it asks the provider
adapter to place a prompt-cache breakpoint at the end of that message. Providers
that don't support caching just ignore it.
"""
import threading

# Module-level lock to prevent concurrent LLM API calls.
# OpenRouter (and most LLM APIs) have per-key concurrency limits.
llm_api_lock = threading.Lock()

# Christine's Narrative objects use their own role vocabulary. Map the ones that are
# specific to her narrative onto chat roles. Note that 'system' is deliberately NOT in
# this map: a chat "system" message is the stable context block, which is a different
# thing from a Narrative tagged 'system' (a sensor event or dream recall). Callers that
# hold Narrative objects - ShortTermMemory.get_recent_messages - are responsible for
# translating those into 'user' before they get here.
NARRATIVE_ROLE_MAP = {
    'char': 'assistant',
    'memory': 'user',
}

VALID_CHAT_ROLES = ('system', 'user', 'assistant')


class LLMAPI():
    """Base class for an LLM API"""

    name = "LLMAPI"

    def is_available(self):
        """Returns True if the LLM API is available, False otherwise"""
        raise NotImplementedError("Subclass must implement is_available method")

    def call_api_implementation(self, messages, stop_sequences=None, max_tokens=600, temperature=0.4, top_p=1.0, expects_json=False):
        """Subclasses implement this method to make the actual API call.

        messages is always a normalized list of {"role", "content", "cache"} dicts.
        """
        raise NotImplementedError("Subclass must implement call_api_implementation method")

    # ------------------------------------------------------------------
    # message helpers
    # ------------------------------------------------------------------

    @staticmethod
    def single(content: str, system: str | None = None) -> list:
        """Build a message list for a one-shot task (memory merge, recovery replay).

        Optionally takes a system instruction; the content becomes the user turn.
        """

        messages = []
        if system:
            messages.append({'role': 'system', 'content': system})
        messages.append({'role': 'user', 'content': content})
        return messages

    @classmethod
    def normalize_messages(cls, messages) -> list:
        """Clean up a message list so every provider gets something sane.

        - drops empty messages
        - maps narrative roles (char/memory) onto chat roles
        - merges consecutive same-role messages, since some providers reject them
        - a merged run keeps the cache flag if any message in the run had it
        """

        normalized = []

        for raw in messages:

            role = raw.get('role', 'user')
            role = NARRATIVE_ROLE_MAP.get(role, role)
            if role not in VALID_CHAT_ROLES:
                role = 'user'

            content = (raw.get('content') or '').strip()
            if content == '':
                continue

            cache = bool(raw.get('cache', False))

            # merge into the previous message when the role repeats
            if normalized and normalized[-1]['role'] == role:
                normalized[-1]['content'] += '\n\n' + content
                normalized[-1]['cache'] = normalized[-1]['cache'] or cache
                continue

            normalized.append({'role': role, 'content': content, 'cache': cache})

        return normalized

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

    def call_api(self, messages, stop_sequences=None, max_tokens=600, temperature=0.4, top_p=1.0, expects_json=False):
        """Call API with automatic failover to next available LLM on failure."""
        from christine.status import STATE
        from christine.api_selector import api_selector
        from christine import log

        messages = self.normalize_messages(messages)

        if not messages:
            log.parietal_lobe.error('call_api got no usable messages')
            return 'I try to say something, but nothing happens.'

        with llm_api_lock:
            try:
                # Try the current API first
                response_text = self.call_api_implementation(messages, stop_sequences, max_tokens, temperature, top_p, expects_json)

            except Exception as ex:
                log.parietal_lobe.warning("LLM %s failed: %s", self.name, ex)
                log.parietal_lobe.info("Attempting failover to next available LLM...")

                # Try to failover to next available LLM
                if api_selector.failover_to_next_llm():
                    log.parietal_lobe.info("Switched to %s, retrying request", STATE.current_llm.name)
                    # Retry with the new LLM
                    response_text = STATE.current_llm.call_api_implementation(messages, stop_sequences, max_tokens, temperature, top_p, expects_json)
                else:
                    log.parietal_lobe.error("No backup LLM available, failing request")
                    return 'I try to say something, but nothing happens.'

            # if the caller expects proper well formed json, let's try to fix common issues
            if expects_json is True:
                response_text = self.fix_json(response_text)

            return response_text

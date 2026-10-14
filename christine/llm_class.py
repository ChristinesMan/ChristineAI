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


class LLMCallFailedError(Exception):
    """Raised by call_api when both the primary and any backup LLM failed (or no
    backup was available). Previously this path returned the placeholder string
    'I try to say something, but nothing happens.' as if it were a normal response,
    which let callers that check for success (e.g. the midnight memory-processing
    pipeline) log "success" and silently store zero memories. Raising makes the
    failure visible to every caller instead of only the ones with their own retry
    logic noticing something was off."""

# Christine's Narrative objects use their own role vocabulary. Map the ones that are
# specific to her narrative onto chat roles, for any caller that hands raw narrative
# roles straight to normalize_messages(). 'system' is deliberately NOT in this map,
# and must never be added to it: this map runs against EVERY message's role,
# including real chat-role 'system' messages (the stable, cache-breakpointed context
# block built in build_conversation_messages). Adding 'system' here would silently
# demote that block to 'assistant' and break both her identity context and the
# prompt cache. A Narrative tagged 'system' (a sensor event or dream recall) is a
# different thing - a narrative-layer concept, not a chat role - and is resolved to
# chat-role 'assistant' by ShortTermMemory.NARRATIVE_CHAT_ROLE before it ever reaches
# here, never by this map.
#
# In practice, ShortTermMemory.get_recent_messages() is the only caller that holds
# Narrative objects, and it already resolves every role to 'user'/'assistant' itself
# before messages get here - so this map is a backstop for any future/other caller
# passing raw narrative roles directly, not something actively exercised by that path
# today. Keep 'char'/'memory' here in sync with ShortTermMemory.NARRATIVE_CHAT_ROLE.
#
# 'memory' is NOT 'user': a recalled memory is Christine's own mind surfacing
# something, not something User said. Mapping it to 'user' was the original bug
# that made her mistake her own recollections and dreams for things User had told
# her (fixed 2026-10-08).
NARRATIVE_ROLE_MAP = {
    'char': 'assistant',
    'memory': 'assistant',
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
        - ensures the list ends on a 'user' turn (see below)

        Why the trailing-user guarantee exists: Anthropic's Claude (at least via this
        OpenRouter route, "Claude Platform on AWS") hard-rejects ANY request whose final
        message isn't role 'user' - including a single trailing assistant turn with no
        prior assistant message, not just repeated assistant runs. It calls this
        "assistant message prefill" and returns a 400: "This model does not support
        assistant message prefill. The conversation must end with a user message."
        Verified directly against the live API 2026-10-08.

        Now that narrative roles map correctly (memory/system -> assistant, not the old
        blanket 'user'), a turn CAN legitimately end on assistant - a dream dissipating,
        a spontaneous memory surfacing, a touch perception - with nothing from User
        after it. So this guarantee has to live here, not in the role-mapping logic: it's
        a wire-protocol requirement of the API, unrelated to whose turn it narratively is.
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

        # Guarantee the request ends on 'user' (see docstring). A synthetic filler
        # here is NOT written back into her narrative/memory anywhere - it exists only
        # for this one outgoing API payload. "..." matches the existing convention of
        # silent structural filler already used elsewhere (e.g. the "N minutes pass."
        # pacing lines), so it's not introducing a new kind of fabrication.
        if normalized and normalized[-1]['role'] != 'user':
            normalized.append({'role': 'user', 'content': '...', 'cache': False})

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
        from christine.llm.openrouter import OpenRouterRefusalError

        messages = self.normalize_messages(messages)

        if not messages:
            log.parietal_lobe.error('call_api got no usable messages')
            return 'I try to say something, but nothing happens.'

        with llm_api_lock:
            try:
                # Try the current API first. A content-filter refusal is often a
                # one-off classifier hiccup (seen on an oversized midnight memory
                # batch), so retry once on the SAME LLM before treating it as a
                # real outage and failing over.
                try:
                    response_text = self.call_api_implementation(messages, stop_sequences, max_tokens, temperature, top_p, expects_json)
                except OpenRouterRefusalError as ex:
                    log.parietal_lobe.warning("LLM %s refused the request, retrying once: %s", self.name, ex)
                    response_text = self.call_api_implementation(messages, stop_sequences, max_tokens, temperature, top_p, expects_json)

            except Exception as ex:
                log.parietal_lobe.warning("LLM %s failed: %s", self.name, ex)
                log.parietal_lobe.info("Attempting failover to next available LLM...")

                # Try to failover to next available LLM
                if api_selector.failover_to_next_llm():
                    log.parietal_lobe.info("Switched to %s, retrying request", STATE.current_llm.name)
                    # Retry with the new LLM
                    try:
                        response_text = STATE.current_llm.call_api_implementation(messages, stop_sequences, max_tokens, temperature, top_p, expects_json)
                    except Exception as ex2:
                        log.parietal_lobe.error("Backup LLM %s also failed: %s", STATE.current_llm.name, ex2)
                        raise LLMCallFailedError(f"Both primary and backup LLM failed: {ex} / {ex2}") from ex2
                else:
                    log.parietal_lobe.error("No backup LLM available, failing request")
                    raise LLMCallFailedError(f"LLM {self.name} failed and no backup available: {ex}") from ex

            # if the caller expects proper well formed json, let's try to fix common issues
            if expects_json is True:
                response_text = self.fix_json(response_text)

            return response_text

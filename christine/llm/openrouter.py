"""This handles the API for OpenRouter, via /chat/completions with prompt caching."""
import time
import re
from requests import post

from christine import log
from christine.config import CONFIG
from christine.llm_class import LLMAPI


class OpenRouterRefusalError(Exception):
    """Raised when the model/provider declines to generate content at all
    (content_filter / native 'refusal'), as opposed to returning malformed text.
    This is a real failure, not an empty-but-successful response, so callers
    (call_api's retry/failover, and anything checking success) must see it as
    an exception rather than silently getting back ''."""


class OpenRouter(LLMAPI):
    """This handles the API for OpenRouter"""

    name = "OpenRouter"

    def __init__(self):

        # setting a limit to how often an is_available check is done, caching the last response
        self.result_cache = None
        self.last_is_available_time = 0.0
        self.is_available_interval = 60.0

        # How to connect to the LLM api. The api key comes from config.ini file
        # The legacy /completions endpoint is deprecated and cannot be prompt-cached,
        # so everything goes through /chat/completions now.
        self.openrouter_url = 'https://openrouter.ai/api/v1/chat/completions'
        self.api_key = CONFIG.openrouter_api_key

        # check the config for a valid looking api key and if it's not correct-looking set it to None
        if not self.api_key or not re.match(r'^sk-or-', self.api_key):
            self.api_key = None

        # default model for OpenRouter - can be overridden in config
        self.model = CONFIG.openrouter_model

        # optional site info for OpenRouter rankings
        self.site_url = CONFIG.openrouter_site_url
        self.site_name = CONFIG.openrouter_site_name

        # prompt caching settings
        self.cache_enabled = CONFIG.openrouter_cache_enabled
        self.cache_ttl = CONFIG.openrouter_cache_ttl

        # OpenRouter/Anthropic allows a limited number of cache breakpoints per request
        self.max_cache_breakpoints = 4

    def is_available(self):
        """Returns True if the LLM API is available, False otherwise. Assumes that the API is available if the API key is set."""

        # check that the llm api key is available
        if self.api_key is None:
            return False

        else:
            return True

    def _build_content(self, message, breakpoints_left):
        """Build the content field for one message.

        Plain string unless this message is a cache breakpoint, in which case it
        becomes a single-element content array carrying cache_control. Returns
        (content, breakpoint_used).
        """

        text = message['content']

        if not (self.cache_enabled and message.get('cache') and breakpoints_left > 0):
            return text, False

        cache_control = {'type': 'ephemeral'}
        if self.cache_ttl:
            cache_control['ttl'] = self.cache_ttl

        return [{'type': 'text', 'text': text, 'cache_control': cache_control}], True

    def call_api_implementation(self, messages, stop_sequences = None, max_tokens = 600, temperature = 0.4, top_p = 1.0, expects_json = False):
        """This function will call the llm api and return the response."""

        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
        }

        # add optional site info for rankings if configured
        if self.site_url:
            headers['HTTP-Referer'] = self.site_url
        if self.site_name:
            headers['X-Title'] = self.site_name

        # build the api messages, converting cache flags into cache_control blocks
        api_messages = []
        breakpoints_left = self.max_cache_breakpoints
        for message in messages:
            content, breakpoint_used = self._build_content(message, breakpoints_left)
            if breakpoint_used:
                breakpoints_left -= 1
            api_messages.append({'role': message['role'], 'content': content})

        payload = {
            "model": self.model,
            "messages": api_messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": top_p,
            "stream": False,
            "usage": {"include": True},
        }

        # add stop sequences if provided
        if stop_sequences is not None:
            payload["stop"] = stop_sequences

        log.llm_stream.info('Start api call. %d messages, %d cache breakpoints.',
                            len(api_messages), self.max_cache_breakpoints - breakpoints_left)
        start_time = time.time()
        # send the api call
        response = post(
            self.openrouter_url,
            headers=headers,
            json=payload,
            timeout=300
        )
        elapsed_time = time.time() - start_time
        log.llm_stream.info('API call completed in %.2f seconds.', elapsed_time)

        response.raise_for_status()
        response = response.json()

        # log the response
        log.llm_stream.debug("Response: %s", response)

        # log cache performance so the savings are visible in the logs
        self._log_cache_usage(response)

        # get the text of the response from the chat completions shape
        choice = response['choices'][0]
        response_text = (choice.get('message', {}).get('content') or '').strip()

        # A content-filter refusal (native_finish_reason='refusal') comes back with
        # content=None, not malformed text. Treat it as a real failure (so call_api's
        # failover/retry logic engages) rather than returning '' and letting it look
        # downstream like the model just said nothing - that made a refused midnight
        # memory-processing call log as "success" with zero memories actually stored.
        finish_reason = choice.get('finish_reason')
        native_finish_reason = choice.get('native_finish_reason')
        if response_text == '' and (finish_reason == 'content_filter' or native_finish_reason == 'refusal'):
            raise OpenRouterRefusalError(
                f"Model refused the request (finish_reason={finish_reason}, native_finish_reason={native_finish_reason})"
            )

        # some models put their answer in reasoning only; fall back rather than returning nothing
        if response_text == '':
            log.llm_stream.warning('Empty content in response, finish_reason=%s', finish_reason)

        # return the text of the response
        return response_text

    def _log_cache_usage(self, response):
        """Log prompt cache hit/write counts from the usage block, if present."""

        try:
            usage = response.get('usage') or {}
            details = usage.get('prompt_tokens_details') or {}
            prompt_tokens = usage.get('prompt_tokens', 0)
            cached_tokens = details.get('cached_tokens', 0)
            completion_tokens = usage.get('completion_tokens', 0)

            if prompt_tokens:
                hit_pct = (cached_tokens / prompt_tokens) * 100.0
            else:
                hit_pct = 0.0

            log.llm_stream.info(
                'Tokens: prompt=%d cached=%d (%.1f%% hit) completion=%d',
                prompt_tokens, cached_tokens, hit_pct, completion_tokens
            )
        except Exception as ex:  # pylint: disable=broad-exception-caught
            log.llm_stream.debug('Could not log cache usage: %s', ex)

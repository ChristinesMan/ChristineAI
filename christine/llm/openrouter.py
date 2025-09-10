"""This handles the API for OpenRouter"""
import time
import re
from ssl import SSLError
from requests import post

from christine import log
from christine.status import STATE
from christine.config import CONFIG
from christine.llm_class import LLMAPI

class OpenRouter(LLMAPI):
    """This handles the API for OpenRouter"""

    name = "OpenRouter"

    def __init__(self):

        # setting a limit to how often an is_available check is done, caching the last response
        self.result_cache = None
        self.last_is_available_time = 0.0
        self.is_available_interval = 60.0

        # How to connect to the LLM api. The api key comes from config.ini file
        self.openrouter_url = 'https://openrouter.ai/api/v1/completions'
        self.api_key = CONFIG.openrouter_api_key

        # check the config for a valid looking api key and if it's not correct-looking set it to None
        if not self.api_key or not re.match(r'^sk-or-', self.api_key):
            self.api_key = None

        # default model for OpenRouter - can be overridden in config
        self.model = CONFIG.openrouter_model

        # optional site info for OpenRouter rankings
        self.site_url = CONFIG.openrouter_site_url
        self.site_name = CONFIG.openrouter_site_name

    def is_available(self):
        """Returns True if the LLM API is available, False otherwise. Assumes that the API is available if the API key is set."""

        # check that the llm api key is available
        if self.api_key is None:
            return False

        else:
            return True

    def call_api(self, prompt, stop_sequences = None, max_tokens = 600, temperature = 0.4, top_p = 1.0, expects_json = False):
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

        payload = {
            "model": self.model,
            "prompt": prompt,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": top_p,
            "stream": False,
        }

        # add stop sequences if provided
        if stop_sequences is not None:
            payload["stop"] = stop_sequences

        # this is for fault tolerance. Flag controls whether we're done here or need to try again.
        # and how long we ought to wait before retrying after an error
        llm_is_done_or_failed = False
        sleep_after_error = 30
        sleep_after_error_multiplier = 5
        sleep_after_error_max = 750
        while llm_is_done_or_failed is False:

            try:

                log.llm_stream.info('Start api call.')
                start_time = time.time()
                # send the api call
                response = post(
                    self.openrouter_url,
                    headers=headers,
                    json=payload,
                    timeout=60
                )
                elapsed_time = time.time() - start_time
                log.llm_stream.info('API call completed in %.2f seconds.', elapsed_time)

                response.raise_for_status()
                response = response.json()

                # log the response
                log.llm_stream.debug("Response: %s", response)

                # get the text of the response - OpenRouter /completions endpoint returns choices with 'text' field
                response_text = response['choices'][0]['text'].strip()

                # if the caller expects proper well formed json, let's try to fix common issues
                if expects_json is True:
                    
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

                # if we got here that means no errors, so signal we're done
                llm_is_done_or_failed = True

            # if api related exceptions occur, sleep here a while and retry, longer with each fail
            except Exception as ex:
                response_text = 'I try to say something, but nothing happens. Better let my husband know. "I\'m sorry, but I can\'t seem to speak right now, but I will try again later."'
                log.parietal_lobe.exception(ex)
                if sleep_after_error > sleep_after_error_max:
                    STATE.perceptions_blocked = True
                    llm_is_done_or_failed = True
                else:
                    STATE.perceptions_blocked = True
                    time.sleep(sleep_after_error)
                    STATE.perceptions_blocked = False
                    sleep_after_error *= sleep_after_error_multiplier

        # return the text of the response
        return response_text

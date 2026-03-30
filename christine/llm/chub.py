"""This handles the API for Chub"""
import time
import re
from requests import post

from christine import log
from christine.config import CONFIG
from christine.llm_class import LLMAPI

class Chub(LLMAPI):
    """This handles the API for Chub"""

    name = "Chub"

    def __init__(self):

        # setting a limit to how often an is_available check is done, caching the last response
        self.result_cache = None
        self.last_is_available_time = 0.0
        self.is_available_interval = 60.0

        # How to connect to the LLM api. The api key comes from config.ini file
        self.chub_url = 'https://inference.chub.ai/prompt'
        self.api_key = CONFIG.chub_api_key

        # check the config for a valid looking api key and if it's not correct-looking set it to None
        if not re.match(r'^CHK-\S{46}$', self.api_key):
            self.api_key = None

    def is_available(self):
        """Returns True if the LLM API is available, False otherwise. Assumes that the API is available if the API key is set."""

        # check that the llm api key is available
        if self.api_key is None:
            return False

        else:
            return True

    def call_api_implementation(self, prompt, stop_sequences = None, max_tokens = 600, temperature = 0.4, top_p = 1.0, expects_json = False):
        """This function will call the llm api and return the response."""

        headers = {
            'CH-API-KEY': self.api_key,
            'Content-Type': 'application/json',
            'User-Agent': 'ChristineAI/1.0'
        }

        payload = {
            "model": "soji",
            "prompt": "",
            "frequency_penalty": 0.1,
            "max_tokens": max_tokens,
            "n": 1,
            "presence_penalty": 0.0,
            "stop": stop_sequences if stop_sequences is not None else [],
            "stream": False,
            "temperature": temperature,
            "top_p": top_p,
            "top_k": 50,
            "min_p": 0,
            "repetition_penalty": 1,
            "length_penalty": 1,
            "stop_token_ids": [0],
            "include_stop_str_in_output": False,
            "ignore_eos": False,
            "min_tokens": 0,
            "skip_special_tokens": True,
            "spaces_between_special_tokens": True,
            "truncate_prompt_tokens": 1,
            "add_special_tokens": True,
            "continue_final_message": False,
            "add_generation_prompt": False,
            "token_repetition_penalty": 1.05,
            "token_repetition_range": -1,
            "token_repetition_decay": 0,
            "top_a": 0,
            "template": prompt
        }

        log.llm_stream.info('Start api call.')
        start_time = time.time()
        # send the api call
        response = post(
            self.chub_url,
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

        # get the text of the response
        response_text=response['choices'][0]['message']['content'].strip()

        # return the text of the response
        return response_text

"""This handles the API for Ollama"""
import time
from requests import post, get

from christine import log
from christine.config import CONFIG
from christine.llm_class import LLMAPI

class Ollama(LLMAPI):
    """This handles the API for Ollama"""

    name = "Ollama"

    def __init__(self):

        # setting a limit to how often an is_available check is done, caching the last response
        self.result_cache = None
        self.last_is_available_time = 0.0
        self.is_available_interval = 60.0

        # How to connect to the Ollama API
        self.base_url = CONFIG.ollama_base_url.rstrip('/')
        self.generate_url = f'{self.base_url}/api/generate'
        self.transcribe_url = f'{self.base_url}/api/generate'
        
        # Model configurations
        self.model = CONFIG.ollama_model

    def is_available(self):
        """Returns True if the Ollama API is available, False otherwise."""

        # Check if we've checked recently
        current_time = time.time()
        if current_time - self.last_is_available_time < self.is_available_interval and self.result_cache is not None:
            return self.result_cache

        try:
            # Try to ping the Ollama API
            response = get(f'{self.base_url}/api/tags', timeout=5)
            available = response.status_code == 200
            
            # Cache the result
            self.result_cache = available
            self.last_is_available_time = current_time
            
            if available:
                log.main.debug("Ollama API is available at %s", self.base_url)
            else:
                log.main.warning("Ollama API returned status %d", response.status_code)
                
            return available
            
        except Exception as ex:
            log.main.warning("Ollama API unavailable: %s", ex)
            self.result_cache = False
            self.last_is_available_time = current_time
            return False

    def call_api_implementation(self, prompt, stop_sequences=None, max_tokens=600, temperature=0.4, top_p=1.0, expects_json=False):
        """This function will call the Ollama API and return the response."""

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "top_p": top_p,
                "num_predict": max_tokens
            }
        }

        # add stop sequences if provided
        if stop_sequences is not None:
            payload["options"]["stop"] = stop_sequences

        log.llm_stream.info('Start Ollama API call.')
        start_time = time.time()
        
        # send the api call
        response = post(
            self.generate_url,
            json=payload,
            timeout=300
        )
        
        elapsed_time = time.time() - start_time
        log.llm_stream.info('Ollama API call completed in %.2f seconds.', elapsed_time)

        response.raise_for_status()
        response_data = response.json()

        # log the response
        log.llm_stream.debug("Ollama Response: %s", response_data)

        # get the text of the response
        response_text = response_data.get('response', '').strip()

        # return the text of the response
        return response_text

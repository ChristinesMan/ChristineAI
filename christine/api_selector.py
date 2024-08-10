"""Keeps track of what LLM APIs are available and which one is currently being used. Supports failover to another LLM API if the current one fails."""

import importlib

from christine import log
from christine.status import STATE
from christine.config import CONFIG

from christine.llm_class import LLMAPI

class LLMSelector:
    """Coordinates available and currently selected LLM APIs"""

    def __init__(self):

        # list of all possible LLM APIs in order of preference
        # "ClassName": "name",
        self.llm_apis = {
            "Chub": "chub",
            "GeminiText": "gemini_text",
            "GeminiAudio": "gemini_audio",
            "OpenAI": "openai",
        }

        # start with an empty list to be filled with enabled LLM APIs
        self.llm_enabled: list[LLMAPI] = []

    def find_enabled_llms(self):
        """This is called once at startup to populate the list of enabled LLM APIs."""

        # this is done here to avoid circular imports
        # pylint: disable=import-outside-toplevel
        from christine.parietal_lobe import parietal_lobe

        # for each LLM API, check if it is enabled in the config
        # if it is, import it, instantiate it, and add it to the list of enabled LLM APIs
        for llm_class_name, llm_name in self.llm_apis.items():
            if CONFIG['parietal_lobe'][f"{llm_name}_enabled"] == "yes":
                log.parietal_lobe.info('LLM %s is enabled', llm_class_name)
                module = importlib.import_module(f"christine.llm_{llm_name}")
                llm_class = getattr(module, llm_class_name)
                log.parietal_lobe.info('Instantiating %s', llm_class_name)
                self.llm_enabled.append(llm_class(parietal_lobe))

    def find_available_llm(self):
        """This is called once at startup and when the current LLM API is no longer available."""

        # go through the llm_apis list and find the next available one
        for llm in self.llm_enabled:

            log.parietal_lobe.info('Checking if %s is available', llm.name)
            # if the llm is available, switch to it
            if llm.is_available():
                log.parietal_lobe.info('Using %s', llm.name)
                STATE.current_llm = llm
                return True

        # if no LLM API is available, return False
        return False

# instantiate
llm_selector = LLMSelector()

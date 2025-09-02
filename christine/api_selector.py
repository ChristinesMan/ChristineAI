"""Keeps track of what LLM APIs are available and which one is currently being used. Supports failover to another LLM API if the current one fails."""

import importlib

from christine import log
from christine.status import STATE
from christine.config import CONFIG

from christine.llm_class import LLMAPI

class LLMSelector:
    """Coordinates available and currently selected LLM APIs"""

    def __init__(self):
        # start with an empty list to be filled with enabled LLM APIs
        self.llm_enabled: list[LLMAPI] = []

    def find_enabled_llms(self):
        """This is called once at startup to populate the list of enabled LLM APIs."""

        # Get the list of enabled LLM module names from config
        llm_modules = CONFIG.get_llm_module_names()
        
        # Map module names to class names
        class_mapping = {
            'llm_openrouter': 'OpenRouter',
            'llm_chub': 'Chub',
            'llm_repeat_what_i_say': 'RepeatWhatISayWithWhisper'
        }

        # for each enabled LLM module, import it and instantiate the class
        for module_name in llm_modules:
            class_name = class_mapping.get(module_name)
            if not class_name:
                log.parietal_lobe.warning('Unknown LLM module: %s', module_name)
                continue
                
            log.parietal_lobe.debug('Loading LLM module: %s', module_name)
            try:
                module = importlib.import_module(f"christine.{module_name}")
                llm_class = getattr(module, class_name)
                log.parietal_lobe.info('Instantiating %s', class_name)
                # LLMs no longer need a reference to the parietal lobe
                self.llm_enabled.append(llm_class())
            except Exception as ex:
                log.parietal_lobe.exception('Failed to load LLM %s: %s', class_name, ex)

    def find_available_llm(self):
        """This is called once at startup and when the current LLM API is no longer available."""

        # go through the llm_apis list and find the next available one
        for llm in self.llm_enabled:

            log.parietal_lobe.debug('Checking if %s is available', llm.name)
            # if the llm is available, switch to it
            if llm.is_available():
                log.parietal_lobe.info('Using %s', llm.name)
                STATE.current_llm = llm
                return True

        # if no LLM API is available, return False
        return False

# instantiate
llm_selector = LLMSelector()

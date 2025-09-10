"""Keeps track of what LLM APIs are available and which one is currently being used. Supports failover to another LLM API if the current one fails."""

import importlib
import inspect

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

        # Get the list of enabled LLMs from config (just service names like 'openrouter', 'chub')
        enabled_llm_names = CONFIG.enabled_llms
        
        # for each enabled LLM, try to import and instantiate it
        for llm_name in enabled_llm_names:
            log.parietal_lobe.debug('Loading LLM: %s', llm_name)
            try:
                # Import the module from christine.llm package
                module = importlib.import_module(f"christine.llm.{llm_name}")
                
                # Find the LLMAPI subclass in the module
                llm_class = self._find_llm_class_in_module(module)
                if llm_class is None:
                    log.parietal_lobe.warning('No LLMAPI subclass found in module: %s', llm_name)
                    continue
                    
                log.parietal_lobe.info('Instantiating %s from %s', llm_class.__name__, llm_name)
                self.llm_enabled.append(llm_class())
                
            except ImportError as ex:
                log.parietal_lobe.warning('Failed to import LLM module %s: %s', llm_name, ex)
            except Exception as ex:
                log.parietal_lobe.exception('Failed to load LLM %s: %s', llm_name, ex)

    def _find_llm_class_in_module(self, module):
        """Find the LLMAPI subclass in a module using introspection."""
        for _, obj in inspect.getmembers(module, inspect.isclass):
            # Check if it's a subclass of LLMAPI but not LLMAPI itself
            if (issubclass(obj, LLMAPI) and 
                obj is not LLMAPI and 
                obj.__module__ == module.__name__):
                return obj
        return None

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

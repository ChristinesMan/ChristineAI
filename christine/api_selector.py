"""Keeps track of what LLM, STT, and TTS APIs aree and which ones are currently being used. Supports failover to another API if the current one fails."""

import importlib
import inspect

from christine import log
from christine.status import STATE
from christine.config import CONFIG

from christine.llm_class import LLMAPI
from christine.stt_class import STTAPI
from christine.tts_class import TTSAPI

class APISelector:
    """Coordinates available and currently selected LLM, STT, and TTS APIs"""

    def __init__(self):
        # start with empty lists to be filled with enabled APIs
        self.llm_enabled: list[LLMAPI] = []
        self.stt_enabled: list[STTAPI] = []
        self.tts_enabled: list[TTSAPI] = []

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
                llm_class = self._find_api_class_in_module(module, LLMAPI)
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

    def find_enabled_stts(self):
        """This is called once at startup to populate the list of enabled STT APIs."""
        
        # Get the list of enabled STTs from config (just service names like 'whisper')
        # For now, we'll use a simple approach - if openai_api_key is set, enable whisper
        if hasattr(CONFIG, 'openai_api_key') and CONFIG.openai_api_key:
            enabled_stt_names = ['whisper']
        else:
            enabled_stt_names = []
        
        # for each enabled STT, try to import and instantiate it
        for stt_name in enabled_stt_names:
            log.parietal_lobe.debug('Loading STT: %s', stt_name)
            try:
                # Import the module from christine.stt package
                module = importlib.import_module(f"christine.stt.{stt_name}")
                
                # Find the STTAPI subclass in the module
                stt_class = self._find_api_class_in_module(module, STTAPI)
                if stt_class is None:
                    log.parietal_lobe.warning('No STTAPI subclass found in module: %s', stt_name)
                    continue
                    
                log.parietal_lobe.info('Instantiating %s from %s', stt_class.__name__, stt_name)
                self.stt_enabled.append(stt_class())
                
            except ImportError as ex:
                log.parietal_lobe.warning('Failed to import STT module %s: %s', stt_name, ex)
            except Exception as ex:
                log.parietal_lobe.exception('Failed to load STT %s: %s', stt_name, ex)

    def find_enabled_ttss(self):
        """This is called once at startup to populate the list of enabled TTS APIs."""
        
        # Get the list of enabled TTSs from config (just service names like 'broca_server')
        # For now, we'll use a simple approach - if broca_server is set, enable broca_server
        if hasattr(CONFIG, 'broca_server') and CONFIG.broca_server:
            enabled_tts_names = ['broca_server']
        else:
            enabled_tts_names = []
        
        # for each enabled TTS, try to import and instantiate it
        for tts_name in enabled_tts_names:
            log.parietal_lobe.debug('Loading TTS: %s', tts_name)
            try:
                # Import the module from christine.tts package
                module = importlib.import_module(f"christine.tts.{tts_name}")
                
                # Find the TTSAPI subclass in the module
                tts_class = self._find_api_class_in_module(module, TTSAPI)
                if tts_class is None:
                    log.parietal_lobe.warning('No TTSAPI subclass found in module: %s', tts_name)
                    continue
                    
                log.parietal_lobe.info('Instantiating %s from %s', tts_class.__name__, tts_name)
                self.tts_enabled.append(tts_class())
                
            except ImportError as ex:
                log.parietal_lobe.warning('Failed to import TTS module %s: %s', tts_name, ex)
            except Exception as ex:
                log.parietal_lobe.exception('Failed to load TTS %s: %s', tts_name, ex)

    def _find_api_class_in_module(self, module, base_class):
        """Find a specific API subclass in a module using introspection."""
        for _, obj in inspect.getmembers(module, inspect.isclass):
            # Check if it's a subclass of the base_class but not the base_class itself
            if (issubclass(obj, base_class) and 
                obj is not base_class and 
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

    def find_available_stt(self):
        """This is called once at startup and when the current STT API is no longer available."""

        # go through the stt_enabled list and find the next available one
        for stt in self.stt_enabled:

            log.parietal_lobe.debug('Checking if %s is available', stt.name)
            # if the stt is available, switch to it
            if stt.is_available():
                log.parietal_lobe.info('Using STT: %s', stt.name)
                STATE.current_stt = stt
                return True

        # if no STT API is available, return False
        return False

    def find_available_tts(self):
        """This is called once at startup and when the current TTS API is no longer available."""

        # go through the tts_enabled list and find the next available one
        for tts in self.tts_enabled:

            log.parietal_lobe.debug('Checking if %s is available', tts.name)
            # if the tts is available, switch to it
            if tts.is_available():
                log.parietal_lobe.info('Using TTS: %s', tts.name)
                STATE.current_tts = tts
                return True

        # if no TTS API is available, return False
        return False

# instantiate
api_selector = APISelector()

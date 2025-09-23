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


    def find_enabled_stts(self):
        """This is called once at startup to populate the list of enabled STT APIs."""
        
        # Get the list of enabled STTs from config (just service names like 'whisper', 'chub')
        enabled_stt_names = CONFIG.enabled_stts
        
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
        enabled_tts_names = CONFIG.enabled_ttss
        
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

    def failover_to_next_llm(self):
        """Switch to the next available LLM after the current one fails."""
        current_llm = STATE.current_llm
        current_index = -1
        
        # Find the index of the current LLM
        for i, llm in enumerate(self.llm_enabled):
            if llm is current_llm:
                current_index = i
                break
        
        # Try the next LLMs in the list
        for i in range(current_index + 1, len(self.llm_enabled)):
            llm = self.llm_enabled[i]
            log.parietal_lobe.debug('Trying failover to LLM: %s', llm.name)
            if llm.is_available():
                log.parietal_lobe.info('Failover successful to LLM: %s', llm.name)
                STATE.current_llm = llm
                return True
        
        # If we get here, no backup LLM is available
        log.parietal_lobe.error('No backup LLM available for failover')
        return False

    def failover_to_next_stt(self):
        """Switch to the next available STT after the current one fails."""
        current_stt = STATE.current_stt
        current_index = -1
        
        # Find the index of the current STT
        for i, stt in enumerate(self.stt_enabled):
            if stt is current_stt:
                current_index = i
                break
        
        # Try the next STTs in the list
        for i in range(current_index + 1, len(self.stt_enabled)):
            stt = self.stt_enabled[i]
            log.parietal_lobe.debug('Trying failover to STT: %s', stt.name)
            if stt.is_available():
                log.parietal_lobe.info('Failover successful to STT: %s', stt.name)
                STATE.current_stt = stt
                return True
        
        # If we get here, no backup STT is available
        log.parietal_lobe.error('No backup STT available for failover')
        return False

    def failover_to_next_tts(self):
        """Switch to the next available TTS after the current one fails."""
        current_tts = STATE.current_tts
        current_index = -1
        
        # Find the index of the current TTS
        for i, tts in enumerate(self.tts_enabled):
            if tts is current_tts:
                current_index = i
                break
        
        # Try the next TTSs in the list
        for i in range(current_index + 1, len(self.tts_enabled)):
            tts = self.tts_enabled[i]
            log.parietal_lobe.debug('Trying failover to TTS: %s', tts.name)
            if tts.is_available():
                log.parietal_lobe.info('Failover successful to TTS: %s', tts.name)
                STATE.current_tts = tts
                return True
        
        # If we get here, no backup TTS is available
        log.parietal_lobe.error('No backup TTS available for failover')
        return False

    def attempt_primary_restoration(self):
        """Periodically try to restore primary APIs if they become available again."""
        restored_any = False
        
        # Try to restore primary LLM (first in list)
        if len(self.llm_enabled) > 0:
            primary_llm = self.llm_enabled[0]
            if primary_llm is not STATE.current_llm and primary_llm.is_available():
                log.parietal_lobe.info('Primary LLM %s is available again, switching back', primary_llm.name)
                STATE.current_llm = primary_llm
                restored_any = True
        
        # Try to restore primary STT (first in list)
        if len(self.stt_enabled) > 0:
            primary_stt = self.stt_enabled[0]
            if primary_stt is not STATE.current_stt and primary_stt.is_available():
                log.parietal_lobe.info('Primary STT %s is available again, switching back', primary_stt.name)
                STATE.current_stt = primary_stt
                restored_any = True
        
        # Try to restore primary TTS (first in list)
        if len(self.tts_enabled) > 0:
            primary_tts = self.tts_enabled[0]
            if primary_tts is not STATE.current_tts and primary_tts.is_available():
                log.parietal_lobe.info('Primary TTS %s is available again, switching back', primary_tts.name)
                STATE.current_tts = primary_tts
                restored_any = True
        
        return restored_any

# instantiate
api_selector = APISelector()

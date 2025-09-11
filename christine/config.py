"""
Centralized configuration system using environment variables.
All configuration is loaded from environment variables with validation.
"""

import os
import sys
from typing import List

from christine import log


class ConfigError(Exception):
    """Raised when configuration is invalid or missing required values."""


class Config:
    """Centralized configuration loaded from environment variables."""
    
    def __init__(self):
        """Load and validate all configuration from environment variables."""
        self._load_config()
        self._validate_config()
    
    def _load_config(self):
        """Load configuration from environment variables."""
        
        # Core service hostnames (required)
        self.wernicke_server = os.getenv('CHRISTINE_WERNICKE_SERVER', 'localhost')
        self.broca_server = os.getenv('CHRISTINE_BROCA_SERVER', 'localhost') 
        self.neocortex_server = os.getenv('CHRISTINE_NEOCORTEX_SERVER', 'localhost')
        
        # User/character settings
        self.user_name = os.getenv('CHRISTINE_USER_NAME', 'Phantom')
        self.char_name = os.getenv('CHRISTINE_CHAR_NAME', 'Christine')
        
        # Testing mode settings
        self.testing_mode = os.getenv('CHRISTINE_TESTING_MODE', 'false').lower() == 'true'
        
        # Wernicke settings
        self.wernicke_pv_key = os.getenv('CHRISTINE_WERNICKE_PV_KEY', '')
        self.wernicke_vad = os.getenv('CHRISTINE_WERNICKE_VAD', 'webrtcvad')
        
        # LLM configuration
        self.enabled_llms = self._parse_llm_list(os.getenv('CHRISTINE_ENABLED_LLMS', ''))
        
        # LLM API keys and settings
        self.openrouter_api_key = os.getenv('CHRISTINE_OPENROUTER_API_KEY', '')
        self.openrouter_model = os.getenv('CHRISTINE_OPENROUTER_MODEL', 'anthropic/claude-3.5-sonnet')
        self.openrouter_site_url = os.getenv('CHRISTINE_OPENROUTER_SITE_URL', '')
        self.openrouter_site_name = os.getenv('CHRISTINE_OPENROUTER_SITE_NAME', 'ChristineAI')
        
        self.chub_api_key = os.getenv('CHRISTINE_CHUB_API_KEY', '')
        
        self.openai_api_key = os.getenv('CHRISTINE_OPENAI_API_KEY', '')
        
        self.gemini_api_key = os.getenv('CHRISTINE_GEMINI_API_KEY', '')

        # Ollama configuration
        self.ollama_base_url = os.getenv('CHRISTINE_OLLAMA_BASE_URL', 'http://server.lan:11434')
        self.ollama_model = os.getenv('CHRISTINE_OLLAMA_MODEL', 'llama3.2')
        self.ollama_whisper_model = os.getenv('CHRISTINE_OLLAMA_WHISPER_MODEL', 'whisper')

        # Initialization timeout settings (in seconds)
        self.wernicke_timeout = int(os.getenv('CHRISTINE_WERNICKE_TIMEOUT', '30'))

        self.http_security_token = os.getenv('CHRISTINE_HTTP_SECURITY_TOKEN', 'christine_lovely_2025')

    def _parse_llm_list(self, llm_string: str) -> List[str]:
        """Parse comma-separated list of enabled LLMs."""
        if not llm_string.strip():
            return []
        return [llm.strip() for llm in llm_string.split(',') if llm.strip()]
    
    def _validate_config(self):
        """Validate that all required configuration is present and valid."""
        errors = []
        
        # Required core services
        if not self.wernicke_server:
            errors.append("CHRISTINE_WERNICKE_SERVER is required")
        
        if not self.broca_server:
            errors.append("CHRISTINE_BROCA_SERVER is required")
        
        if not self.neocortex_server:
            errors.append("CHRISTINE_NEOCORTEX_SERVER is required")
        
        # At least one LLM must be enabled
        if not self.enabled_llms:
            errors.append("CHRISTINE_ENABLED_LLMS must specify at least one LLM (openrouter, chub, ollama, repeat_what_i_say)")
        
        # Validate that enabled LLMs have required API keys
        for llm in self.enabled_llms:
            if llm == 'openrouter' and not self.openrouter_api_key:
                errors.append("CHRISTINE_OPENROUTER_API_KEY is required when openrouter LLM is enabled")
            elif llm == 'chub' and not self.chub_api_key:
                errors.append("CHRISTINE_CHUB_API_KEY is required when chub LLM is enabled")
            elif llm == 'ollama' and not self.ollama_base_url:
                errors.append("CHRISTINE_OLLAMA_BASE_URL is required when ollama LLM is enabled")
            elif llm == 'repeat_what_i_say' and not self.openai_api_key:
                errors.append("CHRISTINE_OPENAI_API_KEY is required when repeat_what_i_say LLM is enabled")
        
        # Validate VAD setting
        if self.wernicke_vad not in ['pvcobra', 'webrtcvad']:
            errors.append(f"CHRISTINE_WERNICKE_VAD must be 'pvcobra' or 'webrtcvad', got '{self.wernicke_vad}'")
        
        # Validate timeout values
        if self.wernicke_timeout <= 0:
            errors.append(f"CHRISTINE_WERNICKE_TIMEOUT must be positive, got {self.wernicke_timeout}")
        
        if errors:
            error_msg = "Configuration validation failed:\n" + "\n".join(f"  - {error}" for error in errors)
            log.main.fatal(error_msg)
            print(f"FATAL: {error_msg}", file=sys.stderr)
            sys.exit(1)


# Global configuration instance
CONFIG = Config()

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

    broca_tts_concurrency: int
    audio_output_mode: str
    remote_audio_host: str
    remote_audio_port: int
    remote_audio_timeout_seconds: float
    
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
        self.enabled_llms = self._parse_service_list(os.getenv('CHRISTINE_ENABLED_LLMS', ''))
        
        # STT configuration
        self.enabled_stts = self._parse_service_list(os.getenv('CHRISTINE_ENABLED_STTS', ''))
        
        # TTS configuration
        self.enabled_ttss = self._parse_service_list(os.getenv('CHRISTINE_ENABLED_TTSS', ''))
        
        # LLM API keys and settings
        self.openrouter_api_key = os.getenv('CHRISTINE_OPENROUTER_API_KEY', '')
        self.openrouter_model = os.getenv('CHRISTINE_OPENROUTER_MODEL', 'anthropic/claude-3.5-sonnet')
        self.openrouter_site_url = os.getenv('CHRISTINE_OPENROUTER_SITE_URL', '')
        self.openrouter_site_name = os.getenv('CHRISTINE_OPENROUTER_SITE_NAME', 'ChristineAI')
        self.openrouter_stt_url = os.getenv('CHRISTINE_OPENROUTER_STT_URL', 'https://openrouter.ai/api/v1/audio/transcriptions')
        self.openrouter_stt_model = os.getenv('CHRISTINE_OPENROUTER_STT_MODEL', 'mistralai/voxtral-mini-transcribe')
        self.openrouter_stt_language = os.getenv('CHRISTINE_OPENROUTER_STT_LANGUAGE', '').strip()
        self.openrouter_stt_timeout_seconds = int(os.getenv('CHRISTINE_OPENROUTER_STT_TIMEOUT_SECONDS', '60'))

        # Prompt caching. The big stable prefix (context + yesterday + earlier today) gets a
        # cache breakpoint so it's billed at the cheap cache-read rate instead of full price.
        # TTL of '1h' costs more to write but survives the gaps between conversations. Set
        # CHRISTINE_OPENROUTER_CACHE_TTL to '5m' for the cheaper short window, or empty for
        # the provider default.
        self.openrouter_cache_enabled = os.getenv('CHRISTINE_OPENROUTER_CACHE_ENABLED', 'true').lower() == 'true'
        self.openrouter_cache_ttl = os.getenv('CHRISTINE_OPENROUTER_CACHE_TTL', '1h').strip()
        
        self.openai_api_key = os.getenv('CHRISTINE_OPENAI_API_KEY', '')
        
        self.gemini_api_key = os.getenv('CHRISTINE_GEMINI_API_KEY', '')

        # Ollama configuration
        self.ollama_base_url = os.getenv('CHRISTINE_OLLAMA_BASE_URL', 'http://server.lan:11434')
        self.ollama_model = os.getenv('CHRISTINE_OLLAMA_MODEL', 'llama3.2')
        self.ollama_whisper_model = os.getenv('CHRISTINE_OLLAMA_WHISPER_MODEL', 'whisper')

        # Initialization timeout settings (in seconds)
        self.wernicke_timeout = int(os.getenv('CHRISTINE_WERNICKE_TIMEOUT', '60'))
        self.broca_tts_concurrency = int(os.getenv('CHRISTINE_BROCA_TTS_CONCURRENCY', '2'))

        # Broca output mode settings
        self.audio_output_mode = os.getenv('CHRISTINE_AUDIO_OUTPUT_MODE', 'local').strip().lower()
        self.remote_audio_host = os.getenv('CHRISTINE_REMOTE_AUDIO_HOST', '').strip()
        self.remote_audio_port = int(os.getenv('CHRISTINE_REMOTE_AUDIO_PORT', '3002'))
        self.remote_audio_timeout_seconds = float(os.getenv('CHRISTINE_REMOTE_AUDIO_TIMEOUT_SECONDS', '30'))

        # Forehead camera. Her first eye. Replaces the photoresistors the older
        # body had in its eye sockets, and is the input for future object/face
        # detection and vision-LLM work. See christine/vision.py for why the
        # light metering is done the way it is.
        self.camera_enabled = os.getenv('CHRISTINE_CAMERA_ENABLED', 'true').lower() == 'true'
        self.camera_device = os.getenv('CHRISTINE_CAMERA_DEVICE', '/dev/video0')
        # Fixed sensor gain during metering. Must stay constant or the light
        # readings drift for reasons that have nothing to do with the room.
        self.camera_gain = int(os.getenv('CHRISTINE_CAMERA_GAIN', '32'))
        # A long exposure in a dark room genuinely takes seconds on this sensor,
        # so this timeout is generous. It is a deadlock guard, not a latency goal.
        self.camera_capture_timeout_seconds = float(os.getenv('CHRISTINE_CAMERA_CAPTURE_TIMEOUT_SECONDS', '30'))
        # How often to take a light reading. Slow on purpose: each reading costs
        # about 2 seconds of one core, and this Pi is also doing realtime audio.
        self.light_poll_seconds = float(os.getenv('CHRISTINE_LIGHT_POLL_SECONDS', '20'))
        # log10 luminance mapped to light_level 0.0 and 1.0 respectively.
        # Defaults come from measurements on the real camera: a lit bedroom
        # reads about -1.7, so darkness sits well below and sunlight above.
        self.light_log_min = float(os.getenv('CHRISTINE_LIGHT_LOG_MIN', '-4.0'))
        self.light_log_max = float(os.getenv('CHRISTINE_LIGHT_LOG_MAX', '-0.3'))
        # Snapshots, for detection and vision LLM work.
        self.camera_snapshot_size = os.getenv('CHRISTINE_CAMERA_SNAPSHOT_SIZE', '640x480')
        self.camera_snapshot_dir = os.getenv('CHRISTINE_CAMERA_SNAPSHOT_DIR', '/root/ChristineAI/logs/snapshots')
        # Auto-exposure needs frames to settle; frame 1 is unusable.
        self.camera_snapshot_warmup_frames = int(os.getenv('CHRISTINE_CAMERA_SNAPSHOT_WARMUP_FRAMES', '12'))

        self.dora_hook_url = os.getenv('CHRISTINE_DORA_HOOK_URL', 'http://dora.lan:8650/christine')
        self.dora_hook_secret = os.getenv('CHRISTINE_DORA_HOOK_SECRET', '')
        # (messageContact() executive tool). Not interchangeable like LLM/STT/TTS, so no
        # failover/current-pointer config here, just which ones are turned on.
        self.enabled_channels = self._parse_service_list(os.getenv('CHRISTINE_ENABLED_CHANNELS', ''))

    def _parse_service_list(self, service_string: str) -> List[str]:
        """Parse comma-separated list of enabled services (LLMs, STTs, TTSs)."""
        if not service_string.strip():
            return []
        return [service.strip() for service in service_string.split(',') if service.strip()]
    
    def _validate_config(self):
        """Validate that all required configuration is present and valid."""
        if os.getenv('CHRISTINE_SKIP_CONFIG_VALIDATION', '').lower() == 'true':
            return

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
            errors.append("CHRISTINE_ENABLED_LLMS must specify at least one LLM (openrouter, ollama, repeat_what_i_say, testing)")
        
        # Validate that enabled LLMs have required API keys
        for llm in self.enabled_llms:
            if llm == 'openrouter' and not self.openrouter_api_key:
                errors.append("CHRISTINE_OPENROUTER_API_KEY is required when openrouter LLM is enabled")
            elif llm == 'ollama' and not self.ollama_base_url:
                errors.append("CHRISTINE_OLLAMA_BASE_URL is required when ollama LLM is enabled")
            elif llm == 'repeat_what_i_say' and not self.openai_api_key:
                errors.append("CHRISTINE_OPENAI_API_KEY is required when repeat_what_i_say LLM is enabled")
        
        # Validate that enabled STTs have required API keys
        for stt in self.enabled_stts:
            if stt == 'whisper' and not self.openai_api_key:
                errors.append("CHRISTINE_OPENAI_API_KEY is required when whisper STT is enabled")
            elif stt == 'openrouter' and not self.openrouter_api_key:
                errors.append("CHRISTINE_OPENROUTER_API_KEY is required when openrouter STT is enabled")
        
        # Validate that enabled TTSs have required configuration
        for tts in self.enabled_ttss:
            if tts == 'broca_server' and not self.broca_server:
                errors.append("CHRISTINE_BROCA_SERVER is required when broca_server TTS is enabled")

        # Validate that enabled channels have required configuration
        for channel in self.enabled_channels:
            if channel == 'dora' and not self.dora_hook_secret:
                errors.append("CHRISTINE_DORA_HOOK_SECRET is required when dora channel is enabled")
        
        # Validate VAD setting
        if self.wernicke_vad not in ['pvcobra', 'webrtcvad']:
            errors.append(f"CHRISTINE_WERNICKE_VAD must be 'pvcobra' or 'webrtcvad', got '{self.wernicke_vad}'")
        
        # Validate timeout values
        if self.wernicke_timeout <= 0:
            errors.append(f"CHRISTINE_WERNICKE_TIMEOUT must be positive, got {self.wernicke_timeout}")

        if self.broca_tts_concurrency <= 0:
            errors.append(
                f"CHRISTINE_BROCA_TTS_CONCURRENCY must be positive, got {self.broca_tts_concurrency}"
            )

        if self.audio_output_mode not in ['local', 'remote']:
            errors.append(
                f"CHRISTINE_AUDIO_OUTPUT_MODE must be 'local' or 'remote', got '{self.audio_output_mode}'"
            )

        if self.audio_output_mode == 'remote' and not self.remote_audio_host:
            errors.append("CHRISTINE_REMOTE_AUDIO_HOST is required when CHRISTINE_AUDIO_OUTPUT_MODE is 'remote'")

        if self.remote_audio_port <= 0 or self.remote_audio_port > 65535:
            errors.append(
                f"CHRISTINE_REMOTE_AUDIO_PORT must be between 1 and 65535, got {self.remote_audio_port}"
            )

        if self.remote_audio_timeout_seconds <= 0:
            errors.append(
                f"CHRISTINE_REMOTE_AUDIO_TIMEOUT_SECONDS must be positive, got {self.remote_audio_timeout_seconds}"
            )

        if self.openrouter_stt_timeout_seconds <= 0:
            errors.append(
                f"CHRISTINE_OPENROUTER_STT_TIMEOUT_SECONDS must be positive, got {self.openrouter_stt_timeout_seconds}"
            )
        
        if errors:
            error_msg = "Configuration validation failed:\n" + "\n".join(f"  - {error}" for error in errors)
            log.main.fatal(error_msg)
            print(f"FATAL: {error_msg}", file=sys.stderr)
            sys.exit(1)


# Global configuration instance
CONFIG = Config()

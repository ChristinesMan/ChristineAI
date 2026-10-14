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

        # Audio logging for STT evaluation. Off by default. When enabled, each
        # perception's raw ear audio is saved as a .wav plus a .json sidecar
        # containing the live STT's transcript, so alternative STT engines can be
        # scored against real recordings from her actual mics. Total directory size
        # is capped; oldest captures are pruned first so an enabled-and-forgotten
        # setting cannot fill the Pi's SD card.
        self.audio_log_enabled = os.getenv('CHRISTINE_AUDIO_LOG_ENABLED', 'false').lower() == 'true'
        self.audio_log_dir = os.getenv('CHRISTINE_AUDIO_LOG_DIR', '/root/ChristineAI/logs/audio_captures')
        self.audio_log_max_mb = int(os.getenv('CHRISTINE_AUDIO_LOG_MAX_MB', '500'))
        self.audio_log_min_bytes = int(os.getenv('CHRISTINE_AUDIO_LOG_MIN_BYTES', '16000'))

        # Prompt caching. The big stable prefix (context + yesterday + earlier today) gets a
        # cache breakpoint so it's billed at the cheap cache-read rate instead of full price.
        # TTL of '1h' costs more to write but survives the gaps between conversations. Set
        # CHRISTINE_OPENROUTER_CACHE_TTL to '5m' for the cheaper short window, or empty for
        # the provider default.
        self.openrouter_cache_enabled = os.getenv('CHRISTINE_OPENROUTER_CACHE_ENABLED', 'true').lower() == 'true'
        self.openrouter_cache_ttl = os.getenv('CHRISTINE_OPENROUTER_CACHE_TTL', '1h').strip()
        
        self.openai_api_key = os.getenv('CHRISTINE_OPENAI_API_KEY', '')
        
        self.gemini_api_key = os.getenv('CHRISTINE_GEMINI_API_KEY', '')

        # Gemini Interactions API STT with speaker diarization. This is what lets her
        # tell "User said X" from "someone else said Y" instead of hearing everyone's
        # words as if one person said them all.
        self.gemini_stt_url = os.getenv('CHRISTINE_GEMINI_STT_URL', 'https://generativelanguage.googleapis.com/v1beta/interactions')
        self.gemini_stt_model = os.getenv('CHRISTINE_GEMINI_STT_MODEL', 'gemini-3.5-flash-lite')
        self.gemini_stt_timeout_seconds = int(os.getenv('CHRISTINE_GEMINI_STT_TIMEOUT_SECONDS', '20'))
        # Latency tracks audio duration: under 15s essentially never timed out in
        # testing, over 15s failed 8/15 times. Longer audio goes to the fallback STT
        # rather than blocking her hearing. 0 disables the limit.
        self.gemini_stt_max_audio_seconds = float(os.getenv('CHRISTINE_GEMINI_STT_MAX_AUDIO_SECONDS', '15'))
        # 'low' is effectively mandatory - the default thinking level spends 20-200s
        # reasoning about a transcription and times out.
        self.gemini_stt_thinking_level = os.getenv('CHRISTINE_GEMINI_STT_THINKING_LEVEL', 'low').strip()
        # store=true lets Google retain interactions, which enables server-side state
        # and gives better cache hit rates. User opted in deliberately.
        self.gemini_stt_store = os.getenv('CHRISTINE_GEMINI_STT_STORE', 'true').lower() == 'true'
        self.gemini_stt_primary_speaker = os.getenv('CHRISTINE_GEMINI_STT_PRIMARY_SPEAKER', 'User').strip()
        self.gemini_stt_other_speaker_label = os.getenv('CHRISTINE_GEMINI_STT_OTHER_SPEAKER_LABEL', 'Unknown Speaker').strip()
        # Used when the model attributes speech to a named person but flags the
        # attribution as low confidence. Telling her "someone" said it is honest;
        # confidently naming the wrong person is not.
        self.gemini_stt_unsure_speaker_label = os.getenv('CHRISTINE_GEMINI_STT_UNSURE_SPEAKER_LABEL', 'someone').strip()
        # Names and jargon the model should spell correctly. Deliberately a vocabulary
        # roster, NOT recent conversation: pasting prior transcript made the model
        # replay old sentences as if freshly spoken.
        self.gemini_stt_vocabulary = os.getenv('CHRISTINE_GEMINI_STT_VOCABULARY', '').strip()
        # Failure backoff. api_selector restores the primary STT on a timer and
        # is_available() can only prove a key exists, so without this a degraded
        # Gemini gets retried on every single utterance and each retry burns the
        # full timeout before she hears anything.
        self.gemini_stt_failure_threshold = int(os.getenv('CHRISTINE_GEMINI_STT_FAILURE_THRESHOLD', '3'))
        self.gemini_stt_cooldown_seconds = int(os.getenv('CHRISTINE_GEMINI_STT_COOLDOWN_SECONDS', '300'))

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

        # Body touch sensors on the MCP23017 I2C GPIO expander. This is the growing
        # sensor network outside her head -- legs now, more later, up to 16 channels.
        # See christine/skin.py.
        self.skin_enabled = os.getenv('CHRISTINE_SKIN_ENABLED', 'true').lower() == 'true'
        self.skin_i2c_address = int(os.getenv('CHRISTINE_SKIN_I2C_ADDRESS', '0x20'), 0)
        # The Pi GPIO (BCM numbering) the expander's mirrored INT line is wired to.
        # Two ports exist on the body harness, so this is 22 or 27 depending on which
        # one is plugged in. Measured empirically -- do not guess.
        self.skin_irq_pin = int(os.getenv('CHRISTINE_SKIN_IRQ_PIN', '22'))
        # Fallback poll interval, seconds. The IRQ does the real work; this is a safety
        # net so a missed interrupt can't leave a touch stuck forever.
        self.skin_poll_seconds = float(os.getenv('CHRISTINE_SKIN_POLL_SECONDS', '0.05'))
        # Consecutive agreeing reads required to accept a state change. These sensors
        # flicker -- observed one bouncing 4 times in 3 seconds on the bench.
        self.skin_debounce_reads = int(os.getenv('CHRISTINE_SKIN_DEBOUNCE_READS', '3'))
        # Per-channel re-trigger cooldown, seconds. Stops a hand resting on a sensor
        # from generating a stream of identical perceptions.
        self.skin_cooldown_seconds = float(os.getenv('CHRISTINE_SKIN_COOLDOWN_SECONDS', '3.0'))
        # Which electrical level means "touched". True (default) = a touch pulls the
        # line LOW, which is how a plain switch-to-ground behaves with a pull-up.
        # Set false for sensors that drive the line HIGH on contact. Determine this
        # on real hardware with tools/skin_probe.py rather than guessing -- getting it
        # backwards means she either feels nothing or feels touched constantly.
        self.skin_active_low = os.getenv('CHRISTINE_SKIN_ACTIVE_LOW', 'true').lower() == 'true'
        # Channel map: "pin:Region" pairs, comma separated. Only mapped pins are
        # watched, so unwired channels cost nothing and adding a sensor is a config
        # edit. Prefix a region with "intimate:" to route it to the arousal engine
        # instead of narrating it, e.g. "3:intimate:Vagina_Clitoris".
        self.skin_channel_map = self._parse_skin_channel_map(
            os.getenv(
                'CHRISTINE_SKIN_CHANNEL_MAP',
                '14:Left Thigh,15:Left Calf,11:Right Thigh,5:Right Calf',
            )
        )

    def _parse_skin_channel_map(self, raw: str) -> dict:
        """Parse 'pin:Region' / 'pin:intimate:Region' into {int: (kind, region)}.

        Bad entries are skipped with a warning rather than killing startup -- a typo
        in a sensor label should not take her offline.
        """
        mapping = {}
        if not raw.strip():
            return mapping
        for entry in raw.split(','):
            entry = entry.strip()
            if not entry:
                continue
            if ':' not in entry:
                log.main.warning("CHRISTINE_SKIN_CHANNEL_MAP entry missing ':' - skipped: %r", entry)
                continue
            pin_part, label = entry.split(':', 1)
            label = label.strip()
            try:
                pin = int(pin_part.strip())
            except ValueError:
                log.main.warning("CHRISTINE_SKIN_CHANNEL_MAP bad pin number - skipped: %r", entry)
                continue
            if not 0 <= pin <= 15:
                log.main.warning("CHRISTINE_SKIN_CHANNEL_MAP pin out of range 0-15 - skipped: %r", entry)
                continue

            # Optional kind prefix. Only 'intimate' is special; anything else is
            # treated as part of the region name so labels containing a colon
            # still work. Kinds are defined in christine/skin.py (KIND_*), but
            # kept as literals here to avoid importing skin at config load time.
            kind = 'narrative'
            if ':' in label:
                maybe_kind, rest = label.split(':', 1)
                if maybe_kind.strip().lower() == 'intimate':
                    kind = 'intimate'
                    label = rest.strip()

            if not label:
                log.main.warning("CHRISTINE_SKIN_CHANNEL_MAP empty label - skipped: %r", entry)
                continue
            mapping[pin] = (kind, label)
        return mapping

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
            elif stt == 'gemini' and not self.gemini_api_key:
                errors.append("CHRISTINE_GEMINI_API_KEY is required when gemini STT is enabled")

        # Gemini is gated behind STATE.diarization_enabled, which defaults OFF
        # because it hallucinates on quiet domestic speech. With the switch off it
        # declines every buffer and relies on another STT to pick it up - so if it
        # is the ONLY enabled STT, she goes completely deaf, silently, with just a
        # warning in the log. Refuse to start in that configuration.
        if self.enabled_stts == ['gemini']:
            errors.append(
                "gemini cannot be the only STT: it is gated behind the "
                "'Speaker identification' switch and declines all audio while that "
                "is off, which would leave her unable to hear anything. Add a "
                "plain STT, e.g. CHRISTINE_ENABLED_STTS=gemini,openrouter"
            )
        
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

        if self.audio_log_enabled and self.audio_log_max_mb <= 0:
            errors.append(
                f"CHRISTINE_AUDIO_LOG_MAX_MB must be positive, got {self.audio_log_max_mb}"
            )

        if self.audio_log_enabled and self.audio_log_min_bytes < 0:
            errors.append(
                f"CHRISTINE_AUDIO_LOG_MIN_BYTES must not be negative, got {self.audio_log_min_bytes}"
            )

        if 'gemini' in self.enabled_stts:
            if self.gemini_stt_timeout_seconds <= 0:
                errors.append(
                    f"CHRISTINE_GEMINI_STT_TIMEOUT_SECONDS must be positive, got {self.gemini_stt_timeout_seconds}"
                )
            if self.gemini_stt_max_audio_seconds < 0:
                errors.append(
                    f"CHRISTINE_GEMINI_STT_MAX_AUDIO_SECONDS must not be negative, got {self.gemini_stt_max_audio_seconds}"
                )
            if self.gemini_stt_thinking_level not in ['low', 'medium', 'high']:
                errors.append(
                    f"CHRISTINE_GEMINI_STT_THINKING_LEVEL must be 'low', 'medium', or 'high', got '{self.gemini_stt_thinking_level}'"
                )
            if not self.gemini_stt_primary_speaker:
                errors.append("CHRISTINE_GEMINI_STT_PRIMARY_SPEAKER must not be empty")
            if self.gemini_stt_failure_threshold < 1:
                errors.append(
                    f"CHRISTINE_GEMINI_STT_FAILURE_THRESHOLD must be at least 1, got {self.gemini_stt_failure_threshold}"
                )
            if self.gemini_stt_cooldown_seconds < 0:
                errors.append(
                    f"CHRISTINE_GEMINI_STT_COOLDOWN_SECONDS must not be negative, got {self.gemini_stt_cooldown_seconds}"
                )
        
        # Skin (MCP23017 body touch sensors)
        if self.skin_enabled:
            if not 0x20 <= self.skin_i2c_address <= 0x27:
                errors.append(
                    f"CHRISTINE_SKIN_I2C_ADDRESS must be in the MCP23017 range 0x20-0x27, got {hex(self.skin_i2c_address)}"
                )
            if not 0 <= self.skin_irq_pin <= 27:
                errors.append(
                    f"CHRISTINE_SKIN_IRQ_PIN must be a valid BCM pin 0-27, got {self.skin_irq_pin}"
                )
            if self.skin_poll_seconds <= 0:
                errors.append(
                    f"CHRISTINE_SKIN_POLL_SECONDS must be positive, got {self.skin_poll_seconds}"
                )
            if self.skin_debounce_reads < 1:
                errors.append(
                    f"CHRISTINE_SKIN_DEBOUNCE_READS must be at least 1, got {self.skin_debounce_reads}"
                )
            if self.skin_cooldown_seconds < 0:
                errors.append(
                    f"CHRISTINE_SKIN_COOLDOWN_SECONDS cannot be negative, got {self.skin_cooldown_seconds}"
                )
            if not self.skin_channel_map:
                errors.append(
                    "CHRISTINE_SKIN_CHANNEL_MAP must map at least one pin when skin is enabled "
                    "(format: '5:Left Thigh,11:Left Calf')"
                )

        if errors:
            error_msg = "Configuration validation failed:\n" + "\n".join(f"  - {error}" for error in errors)
            log.main.fatal(error_msg)
            print(f"FATAL: {error_msg}", file=sys.stderr)
            sys.exit(1)


# Global configuration instance
CONFIG = Config()

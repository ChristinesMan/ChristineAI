"""OpenRouter Speech-to-Text implementation."""
import base64
import io
import re
import struct

import requests

from christine import log
from christine.config import CONFIG
from christine.stt_class import STTAPI


class OpenRouterSTT(STTAPI):
    """OpenRouter Speech-to-Text API implementation."""

    name = "OpenRouterSTT"

    def __init__(self):
        self.openrouter_api_key = CONFIG.openrouter_api_key

        # OpenRouter API keys are expected to start with this prefix.
        if not self.openrouter_api_key or not re.match(r'^sk-or-', self.openrouter_api_key):
            self.openrouter_api_key = None

        self.openrouter_stt_url = CONFIG.openrouter_stt_url
        self.model = CONFIG.openrouter_stt_model
        self.language = CONFIG.openrouter_stt_language
        self.timeout_seconds = CONFIG.openrouter_stt_timeout_seconds
        self.site_url = CONFIG.openrouter_site_url
        self.site_name = CONFIG.openrouter_site_name

        self.re_garbage = re.compile(
            r"thank.+(watching|god bless)|god bless|www\\.mytrend|Satsang|Mooji|^ \\.$|PissedConsumer\\.com|Beadaholique\\.com|^ you$|^ re$|^ GASP$|^ I'll see you in the next video\\.$|thevenusproject|BOO oil in|Amen\\. Amen\\.|^\\. \\. \\.",
            flags=re.IGNORECASE,
        )

    def is_available(self):
        """Returns True if the OpenRouter STT API is available, False otherwise."""
        return self.openrouter_api_key is not None

    def _create_wav_buffer(self, audio_data: bytes) -> io.BytesIO:
        """Create a WAV file buffer in memory from raw PCM audio data."""
        channels = 1
        sample_width = 2  # 16-bit
        frame_rate = 16000

        data_size = len(audio_data)
        file_size = 36 + data_size

        wav_header = struct.pack(
            '<4sI4s4sIHHIIHH4sI',
            b'RIFF',
            file_size,
            b'WAVE',
            b'fmt ',
            16,
            1,
            channels,
            frame_rate,
            frame_rate * channels * sample_width,
            channels * sample_width,
            sample_width * 8,
            b'data',
            data_size,
        )

        wav_buffer = io.BytesIO()
        wav_buffer.write(wav_header)
        wav_buffer.write(audio_data)
        wav_buffer.seek(0)

        return wav_buffer

    def process_audio_implementation(self, audio_data: bytes) -> str:
        """Process incoming audio data using OpenRouter transcription API."""
        wav_buffer = self._create_wav_buffer(audio_data)
        base64_audio = base64.b64encode(wav_buffer.read()).decode('utf-8')

        headers = {
            'Authorization': f'Bearer {self.openrouter_api_key}',
            'Content-Type': 'application/json',
        }

        # Keep compatibility with existing OpenRouter ranking headers.
        if self.site_url:
            headers['HTTP-Referer'] = self.site_url
        if self.site_name:
            headers['X-Title'] = self.site_name
            headers['X-OpenRouter-Title'] = self.site_name

        payload = {
            'model': self.model,
            'input_audio': {
                'data': base64_audio,
                'format': 'wav',
            },
        }

        if self.language:
            payload['language'] = self.language

        response = requests.post(
            self.openrouter_stt_url,
            headers=headers,
            json=payload,
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()

        result = response.json()
        text = result.get('text', '').strip()

        if not text and isinstance(result.get('segments'), list):
            text = ' '.join(segment.get('text', '').strip() for segment in result['segments']).strip()

        if text and self.re_garbage.search(text) is None:
            return text

        if text:
            log.parietal_lobe.info('Filtered out OpenRouter STT result: %s', text)

        return ''

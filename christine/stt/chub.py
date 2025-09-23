"""Chub.ai Speech-to-Text implementation"""
import re
import io
import struct
from ssl import SSLError
import requests

from christine import log
from christine.config import CONFIG
from christine.stt_class import STTAPI

class ChubSTT(STTAPI):
    """Chub.ai Speech-to-Text API implementation"""

    name = "ChubSTT"

    def __init__(self):
        # Get the chub API key from config
        self.chub_api_key = getattr(CONFIG, 'chub_api_key', None)
        self.chub_stt_url = "https://inference.chub.ai/stt"

        # Check if we have a valid looking API key
        if not self.chub_api_key or not self.chub_api_key.startswith('CHK-'):
            self.chub_api_key = None

        # Similar garbage filtering to Whisper - chub might have similar issues
        self.re_garbage = re.compile(
            r"thank.+(watching|god bless)|god bless|www\.mytrend|Satsang|Mooji|^ \.$|PissedConsumer\.com|Beadaholique\.com|^ you$|^ re$|^ GASP$|^ I'll see you in the next video\.$|thevenusproject|BOO oil in|Amen\. Amen\.|^\. \. \.", flags=re.IGNORECASE
        )

    def is_available(self):
        """Returns True if the Chub STT API is available, False otherwise."""
        return self.chub_api_key is not None

    def _create_wav_buffer(self, audio_data: bytes) -> io.BytesIO:
        """Create a WAV file buffer in memory from raw audio data."""
        # WAV file parameters (matching Whisper settings)
        channels = 1
        sample_width = 2  # 16-bit
        frame_rate = 16000
        
        # Calculate sizes
        data_size = len(audio_data)
        file_size = 36 + data_size
        
        # Create WAV header
        wav_header = struct.pack('<4sI4s4sIHHIIHH4sI',
            b'RIFF',           # Chunk ID
            file_size,         # Chunk size
            b'WAVE',           # Format
            b'fmt ',           # Subchunk1 ID
            16,                # Subchunk1 size (PCM)
            1,                 # Audio format (PCM)
            channels,          # Number of channels
            frame_rate,        # Sample rate
            frame_rate * channels * sample_width,  # Byte rate
            channels * sample_width,  # Block align
            sample_width * 8,  # Bits per sample
            b'data',           # Subchunk2 ID
            data_size          # Subchunk2 size
        )
        
        # Create buffer with header + audio data
        wav_buffer = io.BytesIO()
        wav_buffer.write(wav_header)
        wav_buffer.write(audio_data)
        wav_buffer.seek(0)  # Reset to beginning for reading
        
        # Set a filename attribute so the API knows it's a WAV file
        wav_buffer.name = "audio.wav"
        
        return wav_buffer

    def process_audio_implementation(self, audio_data: bytes) -> str:
        """This function processes incoming audio data using Chub.ai STT."""

        try:
            # Create WAV data in memory
            wav_buffer = self._create_wav_buffer(audio_data)
            
            # Prepare headers for chub API
            headers = {
                'CH-API-KEY': self.chub_api_key,
                'User-Agent': 'ChristineAI/1.0'
            }
            
            # Reset buffer position before sending
            wav_buffer.seek(0)
            
            # Prepare multipart file upload
            files = {
                'audio': ('audio.wav', wav_buffer, 'audio/wav')
            }
            
            # Send request to chub STT endpoint
            response = requests.post(
                self.chub_stt_url,
                headers=headers,
                files=files,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Extract text from the response
                text = result.get('reference_text', '').strip()
                
                # Apply garbage filtering similar to Whisper
                if text and self.re_garbage.search(text) is None:
                    return text
                else:
                    log.parietal_lobe.info("Filtered out chub STT result: %s", text)
                    return ""
            
            elif response.status_code == 400:
                # Handle the specific case of audio being too quiet/no speech detected
                try:
                    error_data = response.json()
                    if 'Error uploading sample file' in error_data.get('error', ''):
                        log.parietal_lobe.debug("ChubSTT: Audio rejected - likely too quiet, silent, or no speech detected")
                        return ""  # Return empty string for silent/quiet audio (not an error)
                except: # pylint: disable=bare-except
                    pass
                log.parietal_lobe.error("Chub STT API error: %d - %s", response.status_code, response.text)
                return None
            
            else:
                log.parietal_lobe.error("Chub STT API error: %d - %s", response.status_code, response.text)
                return None

        except (SSLError, TimeoutError, requests.RequestException) as ex:
            log.parietal_lobe.exception("Chub STT connection error: %s", ex)
            return None
        except Exception as ex:
            log.parietal_lobe.error("Error processing audio with Chub STT: %s", ex)
            return None

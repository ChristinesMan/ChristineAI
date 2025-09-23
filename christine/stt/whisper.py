"""OpenAI Whisper Speech-to-Text implementation"""
import re
import io
import struct
from ssl import SSLError
from openai import OpenAI, InternalServerError

from christine import log
from christine.config import CONFIG
from christine.stt_class import STTAPI

class WhisperSTT(STTAPI):
    """OpenAI Whisper Speech-to-Text API implementation"""

    name = "WhisperSTT"

    def __init__(self):
        # the api key for openai is used to access whisper
        self.whisper_api_key = CONFIG.openai_api_key

        # check the config for a valid looking api key, but I'm unsure about the format, whatever
        if not re.match(r'^sk-proj-', self.whisper_api_key):
            self.whisper_api_key = None

        # openai whisper seems to have been trained using a lot of youtube videos that always say thanks for watching
        # and for some reason it's also very knowledgeable about anime
        # It also likes to bark, is very pissed, and likes to bead
        self.re_garbage = re.compile(
            r"thank.+(watching|god bless)|god bless|www\.mytrend|Satsang|Mooji|^ \.$|PissedConsumer\.com|Beadaholique\.com|^ you$|^ re$|^ GASP$|^ I'll see you in the next video\.$|thevenusproject|BOO oil in|Amen\. Amen\.|^\. \. \.", flags=re.IGNORECASE
        )

        # setup the client for whisper api
        if self.whisper_api_key is not None:
            self.whisper_api = OpenAI(api_key=self.whisper_api_key)
        else:
            self.whisper_api = None

    def is_available(self):
        """Returns True if the Whisper API is available, False otherwise."""
        return self.whisper_api is not None

    def _create_wav_buffer(self, audio_data: bytes) -> io.BytesIO:
        """Create a WAV file buffer in memory from raw audio data."""
        # WAV file parameters (matching your original settings)
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
        """This function processes incoming audio data using OpenAI Whisper."""

        try:
            # Create WAV data in memory instead of saving to file
            wav_buffer = self._create_wav_buffer(audio_data)
            
            # Send the audio buffer directly to the API
            transcription = self.whisper_api.audio.transcriptions.create(
                model='whisper-1',
                language="en",
                file=wav_buffer,
                response_format="verbose_json",
                timestamp_granularities=["segment"],
            )

            # iterate over the segments and get the text, filtering trash out
            text = ''
            for segment in transcription.segments:
                if segment.no_speech_prob < 0.9 and self.re_garbage.search(segment.text) is None:
                    text += segment.text
                else:
                    log.parietal_lobe.info("Filtered out: %s", segment.text)

            return text.strip()

        except (SSLError, TimeoutError, InternalServerError) as ex:
            log.parietal_lobe.exception(ex)
            # if the connection failed, return None to signal a failure
            return None
        except Exception as ex:
            log.parietal_lobe.error("Error creating WAV buffer: %s", ex)
            return None

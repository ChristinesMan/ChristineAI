"""Optional raw-audio capture for offline STT evaluation.

Disabled unless CHRISTINE_AUDIO_LOG_ENABLED=true. Saves each perception's ear
audio as a WAV alongside a JSON sidecar with the transcript the live STT
produced, so alternative STT engines can be scored against real recordings.

This exists because Christine discards ear audio immediately after
transcription. Evaluating a different STT (for example one that can do speaker
diarization) requires real audio from her actual microphones in her actual
room, not synthetic samples.

PRIVACY: while enabled this records everything audible in the room. Leave it
off outside deliberate test sessions.
"""

import json
import os
import struct
import time

from christine import log
from christine.config import CONFIG

# Christine's ear mics: 16 kHz, mono, 16-bit signed little-endian.
SAMPLE_RATE = 16000
CHANNELS = 1
SAMPLE_WIDTH = 2


def _wav_header(data_size: int) -> bytes:
    """Build a 44-byte canonical WAV header for raw PCM of the given size."""
    byte_rate = SAMPLE_RATE * CHANNELS * SAMPLE_WIDTH
    return struct.pack(
        '<4sI4s4sIHHIIHH4sI',
        b'RIFF', 36 + data_size, b'WAVE',
        b'fmt ', 16, 1, CHANNELS, SAMPLE_RATE,
        byte_rate, CHANNELS * SAMPLE_WIDTH, SAMPLE_WIDTH * 8,
        b'data', data_size,
    )


def _prune(directory: str, max_bytes: int):
    """Delete oldest captures until the directory fits under max_bytes.

    Captures are wav+json pairs sharing a stem, so prune by stem - dropping a wav
    while keeping its sidecar would leave a transcript with no audio.
    """
    try:
        stems = {}
        total = 0
        for name in os.listdir(directory):
            path = os.path.join(directory, name)
            if not os.path.isfile(path):
                continue
            size = os.path.getsize(path)
            total += size
            stem, _ = os.path.splitext(name)
            group = stems.setdefault(stem, {'size': 0, 'paths': [], 'mtime': 0.0})
            group['size'] += size
            group['paths'].append(path)
            group['mtime'] = max(group['mtime'], os.path.getmtime(path))

        if total <= max_bytes:
            return

        for group in sorted(stems.values(), key=lambda g: g['mtime']):
            if total <= max_bytes:
                break
            for path in group['paths']:
                try:
                    os.remove(path)
                except OSError:
                    pass
            total -= group['size']
    except OSError as ex:
        log.parietal_lobe.warning("audio_log prune failed: %s", ex)


def save(audio_data: bytes, transcript: str, stt_name: str = ''):
    """Save one capture. Never raises - audio logging must not break hearing."""
    if not CONFIG.audio_log_enabled or not audio_data:
        return
    if len(audio_data) < CONFIG.audio_log_min_bytes:
        return  # skip sub-half-second blips

    try:
        directory = CONFIG.audio_log_dir
        os.makedirs(directory, exist_ok=True)

        stamp = time.strftime('%Y%m%d_%H%M%S') + f'_{int(time.time() * 1000) % 1000:03d}'
        wav_path = os.path.join(directory, f'{stamp}.wav')
        json_path = os.path.join(directory, f'{stamp}.json')

        with open(wav_path, 'wb') as handle:
            handle.write(_wav_header(len(audio_data)))
            handle.write(audio_data)

        # Sensor snapshot gives context for why a transcript may have been poor.
        meta = {
            'timestamp': stamp,
            'duration_seconds': round(len(audio_data) / (SAMPLE_RATE * SAMPLE_WIDTH), 3),
            'pcm_bytes': len(audio_data),
            'sample_rate': SAMPLE_RATE,
            'stt_name': stt_name,
            'transcript': transcript or '',
        }
        try:
            from christine.status import STATE
            meta['state'] = {
                'is_sleeping': getattr(STATE, 'is_sleeping', None),
                'light_level': getattr(STATE, 'light_level', None),
                'horny_level': getattr(STATE, 'horny_level', None),
            }
        except Exception:
            pass

        with open(json_path, 'w', encoding='utf-8') as handle:
            json.dump(meta, handle, indent=2)

        _prune(directory, CONFIG.audio_log_max_mb * 1024 * 1024)

    except Exception as ex:  # never let logging break perception
        log.parietal_lobe.warning("audio_log save failed: %s", ex)

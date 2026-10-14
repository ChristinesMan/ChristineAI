"""Google Gemini Interactions API Speech-to-Text with speaker diarization.

Why this exists
---------------
The plain transcription APIs return one undifferentiated string. When several
people are talking, Christine hears everyone's words as if her husband said them
all, which is confusing for her. Gemini's Interactions API can do speaker
diarization, so she can tell "User said X" from "someone else said Y".

How the transcript comes back
-----------------------------
`process_audio_implementation()` returns a plain string, because that is the STTAPI
contract. For single-speaker audio - which is the overwhelming majority of what she
hears - that string is just the bare transcript, exactly like the older STTs
returned, so nothing about her everyday experience changes.

When more than one voice is present, the segments are ALSO published on the
instance as `last_segments`, and `Perception` picks them up so the parietal lobe
can emit one attributed message per speaker. That matters because the parietal
lobe already wraps each message as:

    <speaker> says, "<text>"

If this class pre-rendered its own `User said, "..."` string, that would end up
nested inside the pipeline's own quoting:

    User says, "User said, "oh okay" someone said, "zero them out"" 

...which is unreadable AND wrongly attributes every voice to User. So the
speaker structure is handed over as data, not baked into the string.

Latency, measured on 920 real captures
--------------------------------------
Latency tracks audio DURATION. Under 15 s: 0/10 timeouts in bucket sampling. Over
15 s: 8/15 timed out at 45 s. Real buffers are median 4.3 s (58.8% under 5 s) but
reach 105 s.

Even on short audio the spread is wide: median 6.4 s, p90 34 s, max 80 s over 25
real clips (0 hard failures at a 90 s ceiling). So the timeout is a deliberate
tradeoff - exceeding it costs diarization, not speech, because STTAPI fails over
to the plain transcription STT.

Long audio is not sent to Gemini at all; it goes straight to the fallback, which
is faster and cheaper for the case where diarization matters least (one person
monologuing). See `gemini_stt_max_audio_seconds`.
"""

import base64
import io
import json
import re
import struct
import time

import requests

from christine import log
from christine.config import CONFIG
from christine.status import STATE
from christine.stt_class import STTAPI


class GeminiSTT(STTAPI):
    """Google Gemini Interactions API STT with speaker diarization."""

    name = "GeminiSTT"

    # Christine's ear mics: 16 kHz, mono, 16-bit signed little-endian.
    SAMPLE_RATE = 16000
    CHANNELS = 1
    SAMPLE_WIDTH = 2

    # Structured output. Asking for confidence gives us a cheap way to discard
    # guessed speaker attribution instead of asserting a wrong name to her.
    RESPONSE_SCHEMA = {
        'type': 'object',
        'properties': {
            'segments': {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'properties': {
                        'speaker': {'type': 'string'},
                        'text': {'type': 'string'},
                        'confidence': {
                            'type': 'string',
                            'enum': ['high', 'medium', 'low'],
                        },
                    },
                    'required': ['speaker', 'text', 'confidence'],
                },
            },
            'speaker_count': {'type': 'integer'},
        },
        'required': ['segments', 'speaker_count'],
    }

    def __init__(self):
        self.gemini_api_key = CONFIG.gemini_api_key or None
        self.url = CONFIG.gemini_stt_url
        self.model = CONFIG.gemini_stt_model
        self.timeout_seconds = CONFIG.gemini_stt_timeout_seconds
        self.max_audio_seconds = CONFIG.gemini_stt_max_audio_seconds
        self.thinking_level = CONFIG.gemini_stt_thinking_level
        self.store = CONFIG.gemini_stt_store
        self.primary_speaker = CONFIG.gemini_stt_primary_speaker
        self.other_speaker_label = CONFIG.gemini_stt_other_speaker_label
        self.unsure_speaker_label = CONFIG.gemini_stt_unsure_speaker_label
        self.vocabulary = CONFIG.gemini_stt_vocabulary
        self.failure_threshold = CONFIG.gemini_stt_failure_threshold
        self.cooldown_seconds = CONFIG.gemini_stt_cooldown_seconds

        # Populated on every successful call so Perception can hand speaker
        # structure to the parietal lobe. Single-speaker audio leaves this empty,
        # which keeps the common path identical to the older STTs.
        self.last_segments: list = []

        # Failure cooldown. STTAPI.process_audio() fails over on exception, but
        # api_selector.attempt_primary_restoration() switches straight back to the
        # primary STT on a timer, and is_available() only proves a key is set.
        # Without a cooldown, a degraded Gemini gets retried every single
        # utterance - each one burning the full timeout before she hears anything.
        # After repeated failures we report unavailable for a while so the plain
        # STT stays in charge and her hearing stays responsive.
        self.consecutive_failures = 0
        self.unavailable_until = 0.0

        # Same junk filter the other STTs use. Transcription models trained on
        # scraped video love to hallucinate "thanks for watching" into silence.
        self.re_garbage = re.compile(
            r"thank.+(watching|god bless)|god bless|www\.mytrend|Satsang|Mooji|"
            r"^ \.$|PissedConsumer\.com|Beadaholique\.com|^ you$|^ re$|^ GASP$|"
            r"^ I'll see you in the next video\.$|thevenusproject|BOO oil in|"
            r"Amen\. Amen\.|^\. \. \.",
            flags=re.IGNORECASE,
        )

    def is_available(self):
        """True if a key is configured and we are not in a failure cooldown."""
        if self.gemini_api_key is None:
            return False
        if self.unavailable_until and time.time() < self.unavailable_until:
            return False
        return True

    def wants_audio(self, audio_data: bytes) -> bool:
        """Decline audio this STT should not handle.

        Declining routes just this buffer to the plain STT while Gemini stays
        primary. Raising instead would trip api_selector's failover, and since it
        only retries the primary every 5 minutes, a single declined buffer would
        cost several minutes of diarization for everything said afterwards.

        Two reasons to decline:

        1. `STATE.diarization_enabled` is off. This is the master switch, checked
           live so User can flip it in the web UI before a meeting with no
           restart. Default off, because on quiet domestic speech the model
           hallucinates confidently - a mumbled "I love you" came back as
           "I don't know. I don't know. I don't know." She cannot tell an
           invented sentence from a real one, so she acts on the fiction. A
           plain transcript that misses a mumble is strictly better than a
           fluent one that makes up words.
        2. The buffer is longer than `max_audio_seconds`.
        """
        if not STATE.diarization_enabled:
            log.parietal_lobe.debug(
                'GeminiSTT declining: speaker identification is switched off, '
                'routing to the plain STT'
            )
            return False
        if self.max_audio_seconds <= 0:
            return True
        seconds = self._audio_seconds(audio_data)
        if seconds > self.max_audio_seconds:
            log.parietal_lobe.info(
                'GeminiSTT declining %.1fs audio (limit %.1fs); diarization is '
                'unreliable on long buffers, routing to the plain STT',
                seconds, self.max_audio_seconds,
            )
            return False
        return True

    def _note_failure(self, reason: str):
        """Record a failure and start a cooldown once they pile up."""
        self.consecutive_failures += 1
        if self.consecutive_failures >= self.failure_threshold:
            self.unavailable_until = time.time() + self.cooldown_seconds
            log.parietal_lobe.warning(
                'GeminiSTT: %d consecutive failures (%s), backing off %ds so the '
                'fallback STT stays in charge',
                self.consecutive_failures, reason, self.cooldown_seconds,
            )

    def _note_success(self):
        if self.consecutive_failures or self.unavailable_until:
            log.parietal_lobe.info('GeminiSTT recovered after %d failure(s)',
                                   self.consecutive_failures)
        self.consecutive_failures = 0
        self.unavailable_until = 0.0

    # ------------------------------------------------------------------ audio

    def _create_wav_buffer(self, audio_data: bytes) -> io.BytesIO:
        """Wrap raw PCM in a WAV container in memory."""
        data_size = len(audio_data)
        byte_rate = self.SAMPLE_RATE * self.CHANNELS * self.SAMPLE_WIDTH

        wav_header = struct.pack(
            '<4sI4s4sIHHIIHH4sI',
            b'RIFF',
            36 + data_size,
            b'WAVE',
            b'fmt ',
            16,
            1,
            self.CHANNELS,
            self.SAMPLE_RATE,
            byte_rate,
            self.CHANNELS * self.SAMPLE_WIDTH,
            self.SAMPLE_WIDTH * 8,
            b'data',
            data_size,
        )

        wav_buffer = io.BytesIO()
        wav_buffer.write(wav_header)
        wav_buffer.write(audio_data)
        wav_buffer.seek(0)
        return wav_buffer

    def _audio_seconds(self, audio_data: bytes) -> float:
        return len(audio_data) / float(self.SAMPLE_RATE * self.SAMPLE_WIDTH)

    # ----------------------------------------------------------------- prompt

    def _build_prompt(self) -> str:
        """Build the diarization prompt.

        Two hard-won rules are baked in here:

        1. Christine's own name is NEVER offered as a candidate label. When it was,
           the model started assigning HER name to other people's voices, which is
           worse than the original problem - she would hear a stranger's words as
           her own thoughts.
        2. Context is a names-only vocabulary roster, never a verbatim transcript
           of what was recently said. Pasting recent conversation made the model
           replay the previous clip's words as if freshly spoken (reproduced 3/3).
        """
        prompt = f"""Transcribe this audio from microphones in a home. Voices may be near (in the room) or far (a TV or a video call playing over speakers).

Rules:
1. One segment per contiguous utterance by a single speaker.
2. Speaker labels, in priority order:
   a. "{self.primary_speaker}" - the adult male in the room, the primary and usually
      nearest speaker.
   b. A real first name ONLY if the reference vocabulary below names them AND you
      are confident the voice matches that person.
   c. Otherwise "{self.other_speaker_label} 1", "{self.other_speaker_label} 2", ...
      numbered by first appearance and used consistently within this clip.
   NEVER label a segment with the name of the listener; she is not a speaker here.
3. Transcribe verbatim, including filler words. Do not summarize, do not fix
   grammar, do not add commentary.
4. Use confidence "low" when the audio is unclear OR the speaker attribution is a
   guess. Only use "high" when you are genuinely certain who spoke.
5. If there is no intelligible speech (silence, noise, a distant thump), return an
   empty segments array and speaker_count 0. Do NOT invent words."""

        if self.vocabulary:
            prompt += f"""

Reference vocabulary - correct spellings of names and terms that may occur in the
audio. These are NOT words spoken in this clip; do not transcribe them:
  {self.vocabulary}"""

        return prompt

    # ---------------------------------------------------------------- request

    def _call_api(self, wav_bytes: bytes) -> dict:
        """POST the audio to the Interactions API and return the parsed JSON."""
        headers = {
            'x-goog-api-key': self.gemini_api_key,
            'Content-Type': 'application/json',
        }

        payload = {
            'model': self.model,
            'input': [
                {'type': 'text', 'text': self._build_prompt()},
                {
                    'type': 'audio',
                    'data': base64.b64encode(wav_bytes).decode('utf-8'),
                    'mime_type': 'audio/wav',
                },
            ],
            'response_format': self.RESPONSE_SCHEMA,
            # thinking_level is not optional. On the default level the model spends
            # 20-200 s reasoning about a transcription and frequently times out.
            'generation_config': {'thinking_level': self.thinking_level},
            'store': self.store,
        }

        response = requests.post(
            self.url,
            headers=headers,
            json=payload,
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        return response.json()

    @staticmethod
    def _extract_output_text(result: dict) -> str:
        """Pull the model's text out of the Interactions `steps` array."""
        text = ''
        for step in result.get('steps', []):
            if step.get('type') != 'model_output':
                continue
            for content in step.get('content', []):
                text += content.get('text', '')
        return text.strip()

    # ---------------------------------------------------------------- render

    def _clean_segments(self, segments: list) -> list:
        """Normalize, filter and merge raw segments from the model.

        Returns a list of {speaker, text, confidence}. A low-confidence
        attribution to anyone other than the primary speaker gets its name
        replaced with a generic label - telling her "someone said" is honest,
        confidently naming the wrong person is not.
        """
        clean = []
        for segment in segments:
            text = (segment.get('text') or '').strip()
            if not text:
                continue
            if self.re_garbage.search(text) is not None:
                log.parietal_lobe.info('Filtered out Gemini STT segment: %s', text)
                continue
            speaker = (segment.get('speaker') or '').strip() or self.primary_speaker
            confidence = (segment.get('confidence') or 'low').strip().lower()
            clean.append({'speaker': speaker, 'text': text, 'confidence': confidence})

        if not clean:
            return []

        # Merge neighbouring segments from the same speaker so she gets whole
        # thoughts rather than a stack of fragments. The parietal lobe does this
        # too, but doing it here keeps the returned text tidy as well.
        merged = []
        for segment in clean:
            if merged and merged[-1]['speaker'] == segment['speaker']:
                merged[-1]['text'] += ' ' + segment['text']
                if segment['confidence'] == 'low':
                    merged[-1]['confidence'] = 'low'
            else:
                merged.append(dict(segment))

        # Soften uncertain attribution of non-primary speakers.
        for segment in merged:
            if (segment['confidence'] == 'low'
                    and segment['speaker'] != self.primary_speaker):
                segment['speaker'] = self.unsure_speaker_label

        # Softening can make neighbours match, so merge once more.
        collapsed = []
        for segment in merged:
            if collapsed and collapsed[-1]['speaker'] == segment['speaker']:
                collapsed[-1]['text'] += ' ' + segment['text']
            else:
                collapsed.append(dict(segment))

        return collapsed

    @staticmethod
    def _flatten(segments: list) -> str:
        """Plain transcript with no speaker names and no quote characters.

        This is what goes back through the STTAPI string contract. Speaker
        attribution travels separately in `last_segments` so the parietal lobe can
        render it without nesting quotes inside its own quoting.
        """
        return ' '.join(segment['text'] for segment in segments).strip()

    # ------------------------------------------------------------------ entry

    def process_audio_implementation(self, audio_data: bytes) -> str:
        """Transcribe audio with speaker diarization.

        Returns the plain transcript. When several voices were heard, the
        per-speaker structure is left on `self.last_segments` for Perception to
        pick up; single-speaker audio clears it so the common path behaves exactly
        like the older STTs.

        Raises on failure so that STTAPI.process_audio() fails over to the next
        configured STT. Returning '' would look like "she heard silence", which is
        a different and wrong claim.
        """
        # Never let a previous call's speakers leak into this one.
        self.last_segments = []

        seconds = self._audio_seconds(audio_data)

        # Belt and braces: process_audio() routes long buffers away via
        # wants_audio(), so this only fires if something calls the implementation
        # directly. Raise rather than silently transcribing something we know is
        # unreliable.
        if self.max_audio_seconds > 0 and seconds > self.max_audio_seconds:
            raise ValueError(
                f'audio too long for Gemini diarization: {seconds:.1f}s > '
                f'{self.max_audio_seconds:.1f}s'
            )

        wav_buffer = self._create_wav_buffer(audio_data)
        started = time.time()
        try:
            result = self._call_api(wav_buffer.read())
        except Exception as ex:
            # Timeouts and HTTP errors both land here. Count them so a degraded
            # Gemini stops being retried on every utterance, then re-raise so
            # STTAPI fails over for this utterance.
            self._note_failure(type(ex).__name__)
            raise
        elapsed = time.time() - started

        output_text = self._extract_output_text(result)
        if not output_text:
            log.parietal_lobe.warning('GeminiSTT returned no model output')
            self._note_failure('empty model output')
            return ''

        try:
            parsed = json.loads(output_text)
        except json.JSONDecodeError as ex:
            # Schema-constrained output should always be valid JSON. If it isn't,
            # raise so we fail over rather than feeding her a JSON fragment.
            log.parietal_lobe.warning('GeminiSTT non-JSON output: %s', output_text[:200])
            self._note_failure('malformed JSON')
            raise ValueError(f'GeminiSTT returned malformed JSON: {ex}') from ex

        self._note_success()

        segments = self._clean_segments(parsed.get('segments') or [])
        text = self._flatten(segments)

        # Only publish structure when there is genuinely more than one voice.
        distinct = {segment['speaker'] for segment in segments}
        if len(distinct) > 1:
            self.last_segments = segments

        usage = result.get('usage') or {}
        log.parietal_lobe.info(
            'GeminiSTT %.1fs audio in %.2fs, %d voice(s), %d segment(s), '
            'in_tok=%s out_tok=%s',
            seconds, elapsed, len(distinct), len(segments),
            usage.get('total_input_tokens'), usage.get('total_output_tokens'),
        )
        if len(distinct) > 1:
            log.conversation_flow.info(
                'DIARIZATION: %d voices - %s',
                len(distinct),
                ' | '.join(f'{s["speaker"]}: {s["text"][:60]}' for s in segments),
            )

        return text

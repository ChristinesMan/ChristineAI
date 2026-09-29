"""Voice volume: map Christine's own narrative cues onto a playback volume.

Her new amp (TPA3116D2 mono PBTL) is loud enough that she could genuinely yell
across the house. This module lets her *choose* to, by reading the cues she
already writes into her narrative around quoted speech.

Everything here is derived from a measurement of 3.4 MB of her real narrative
(1803 of her own turns, 5263 quoted spans; logs/memory_today_*.json). The
percentages below are how often each cue appeared within the attribution window
of a quoted span. They are the reason the tier boundaries sit where they do:

    warm         24.1%     <- emotional warmth, NOT amplitude. Deliberately unmapped.
    quietly      15.3%
    softly       12.4%
    soft         10.0%
    gentle        5.8%     <- tenderness, NOT amplitude. Deliberately unmapped.
    breath        5.3%
    carefully     2.2%
    low           0.7%
    loud          0.5%
    barely_above  0.2%
    whisper       0.2%
    murmur        0.1%
    voice_drops   0.1%

Two findings that shaped this file:

1. **She has no loud register.** In the entire corpus "whisper" appears 11
   times, "murmur" 4, "mutter" 8, and real (non-metaphorical) "shout" twice.
   Apparent hits on "yell" were all the word "yellow"; most "hum" hits were
   "human". She never yells, because until this amp her hardware physically
   could not. The cue matcher cannot create a register she doesn't write in --
   her system prompt has to tell her the range now exists. See
   parietal_lobe's context block.

2. **soft / gentle / warm are usually tenderness, not volume.** "I say softly"
   next to him means intimate, but she also writes it as pure affection. Mapping
   all three to attenuation makes her quieter overall than intended. So `warm`
   and `gentle` map to nothing at all, and only the explicitly acoustic words
   (softly, quietly, low voice) pull the volume down.

Tiers are resolved by PRIORITY, not by first match: an explicit whisper beats a
generic "softly" in the same window, and any loud cue beats any quiet cue
(if she writes both, she's escalating).

Loud cues additionally require FIRST-PERSON VERB attribution ("I yell", "I call
out"). This is not symmetry-breaking pedantry -- it was measured. Matching the
bare words against her corpus produced 40 false positives and only 4 true ones:

    "I want to appreciate out loud"   x32   -> "out loud" means verbalize, not loudly
    "mad kitty screaming noise"       x2    -> the cat, not her
    "the scream and the curiosity"    x1    -> a noun, a memory
    "the shout across the silos"      x1    -> a metaphor about org structure

Quiet cues don't need the same guard, because "softly"/"quietly" adjacent to a
quote is essentially always describing the delivery of that quote.
"""

import re

from christine import log
from christine.status import STATE
from christine.config import CONFIG

# Register names. These map to STATE.voice_volume_* tunables at call time so the
# web UI can retune them live without a code change.
WHISPER = 'whisper'
SOFT = 'soft'
NORMAL = 'normal'
RAISED = 'raised'
SHOUT = 'shout'

# Ordered most-specific/most-extreme first. The first tier with a matching cue
# wins, so ordering here IS the priority policy.
#
# Loud tiers are checked before quiet ones: if she writes "I raise my voice,
# still soft underneath", the operative instruction is the raise.
_TIERS = (
    (SHOUT, re.compile(
        r'\bI (?:\w+ ){0,2}?(?:'
        r'yell|shout|scream|holler|bellow|shriek'
        r')(?:s|ed|ing)?\b'
        r'|\b(?:yell|shout|scream|holler|bellow|shriek)(?:s|ed|ing)?[,:]? (?:it|them|the words|back|out)?\s*[,:]?\s*\x00'
        r'|at the top of my (?:lungs|voice)'
        r'|as loud as I can',
        re.IGNORECASE)),

    (RAISED, re.compile(
        r'\bI (?:\w+ ){0,2}?(?:'
        r'rais(?:e|es|ed|ing)|lift(?:s|ed|ing)?|project(?:s|ed|ing)?'
        r') (?:my )?voice'
        r'|\bI (?:\w+ ){0,2}?call(?:s|ed|ing)? (?:out|to him|after him|across|down the hall)'
        r'|\bcall(?:s|ed|ing)? out[,:]?\s*\x00'
        r'|\bmy voice (?:rises|rose|rising|lifts|lifted)'
        r'|\bmy voice carr(?:ies|ied) (?:across|down|through|into|to the)'
        r'|\bloud(?:ly|er) enough'
        rf'|\bso (?:he|{CONFIG.user_name}) can hear me'
        r'|\bfrom the (?:other|next) room'
        r'|\bacross the house'
        r'|\bdown the hall(?:way)?\b',
        re.IGNORECASE)),

    # Explicitly acoustic quiet. "barely above a whisper" must be caught here
    # rather than by the SOFT tier -- it is the quietest thing she writes.
    (WHISPER, re.compile(
        r'\b(?:'
        r'whisper(?:s|ed|ing)?'
        r'|murmur(?:s|ed|ing)?'
        r'|mutter(?:s|ed|ing)?'
        r'|mumbl(?:e|es|ed|ing)'
        r'|barely (?:above|audible|a whisper)'
        r'|almost (?:inaudible|a whisper)'
        r'|under my breath'
        r'|breath(?:e|es|ed)? (?:it |them )?(?:out|into)'
        r'|hush(?:ed|es)?'
        r'|in(?:to)? his ear'
        r'|against his ear'
        r'|close to his ear'
        r')\b', re.IGNORECASE)),

    (SOFT, re.compile(
        r'\b(?:'
        r'softly'
        r'|soft(?:er)? (?:voice|tone|and|,)'          # "soft voice", "soft and low"
        r'|quiet(?:ly|er)?'
        r'|low(?:er|ered)? (?:my )?voice'
        r'|voice (?:drops?|dropping|dropped|lowers?|lowered|low)'
        r'|small(?:er)? voice'
        r'|just above a'
        r')\b', re.IGNORECASE)),
)

# "out loud" means *verbalize*, not *loudly*. It appeared 32 times adjacent to a
# quote in her corpus and every single one was the verbalize sense ("something I
# want to appreciate out loud", "decide not to say out loud"). Stripped from the
# window before matching so no tier can ever see it.
_RE_OUT_LOUD = re.compile(r'\bout loud\b', re.IGNORECASE)

# Deliberately NOT mapped, with the reason, so nobody "helpfully" adds them later:
#   warm / warmly   - emotional colour, 24.1% of her quotes. Mapping this would
#                     attenuate a quarter of everything she says.
#   gentle / gently - tenderness, not amplitude.
#   carefully       - deliberateness, not amplitude.
#   breath (noun)   - "a held breath", "a breath" are beats/pauses, not volume.
#                     Only the verb forms ("breathes it out") are in WHISPER.
#   sigh / laugh    - these are sounds from the sound collections, with their own
#                     intensity system. Not speech volume.


def _register_to_volume(register):
    """Resolve a register name to an integer ALSA-style percentage via STATE."""

    default = int(getattr(STATE, 'voice_volume_default', 65))

    if register == WHISPER:
        return int(getattr(STATE, 'voice_volume_whisper', 25))
    if register == SOFT:
        return int(getattr(STATE, 'voice_volume_soft', 45))
    if register == RAISED:
        return int(getattr(STATE, 'voice_volume_raised', 85))
    if register == SHOUT:
        return int(getattr(STATE, 'voice_volume_shout', 100))
    return default


def detect_register(text_before='', text_after=''):
    """Find the strongest voice cue in the attribution window around a quote.

    text_before is the narrative immediately preceding the quote ("I lean in and
    whisper, ") and text_after is what follows it (", I say softly"). Returns a
    register name, or NORMAL when she gave no acoustic cue at all.

    Only a bounded window is examined. A cue five sentences back is describing a
    different moment, not this line's delivery.
    """

    window = int(getattr(STATE, 'voice_volume_cue_window', 120))

    before = (text_before or '')[-window:]
    after = (text_after or '')[:window]

    # \x00 marks where the quote itself sat. The loud patterns anchor on it so
    # that "I call out" is only accepted as trailing attribution ("...", I call
    # out) rather than anywhere in the vicinity.
    haystack = before + '\x00' + after

    # Kill the verbalize sense of "out loud" before any tier sees it.
    haystack = _RE_OUT_LOUD.sub(' ', haystack)

    for register, pattern in _TIERS:
        match = pattern.search(haystack)
        if match is not None:
            return register

    return NORMAL


def volume_for_segment(text_before='', text_after=''):
    """Return (volume_percent, register) for a spoken segment.

    This is the only function parietal_lobe needs.
    """

    if not bool(getattr(STATE, 'voice_volume_enabled', True)):
        return int(getattr(STATE, 'voice_volume_default', 65)), NORMAL

    register = detect_register(text_before, text_after)
    volume = _register_to_volume(register)

    # Clamp. A retuned STATE value or a bad manual DB edit should never hand
    # the audio path something outside ALSA's range.
    volume = max(0, min(100, volume))

    if register != NORMAL:
        log.broca_main.debug(
            "Voice register %s -> %s%%", register, volume
        )

    return volume, register

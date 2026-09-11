"""
VAD Self-Tuning Module

Goal: stop spending STT API calls on audio that contains no speech, WITHOUT
making Christine hard of hearing.

History / why this was rewritten
--------------------------------
The first version of this module tuned `wernicke_webrtc_trigger_prob` -- the
smoothed-probability threshold that starts an utterance -- using the rate of
empty STT results as its error signal. That control loop was broken in three
independent ways, and the combination made her progressively deafer:

1. WRONG SIGN ON THE KNOB. `block_prob` is an EMA with window
   `wernicke_webrtc_prob_window` (32). Reaching a threshold T requires
   log(1-T)/log(1-1/32) consecutive voice-positive blocks at 31.25 blocks/sec:

       T=0.45 -> 18.8 blocks -> 0.60 s
       T=0.75 -> 43.7 blocks -> 1.40 s

   The pre-roll ring buffer is only `wernicke_padding_blocks` (40) = 1.28 s, so
   at T=0.75 the utterance can't even be triggered until *after* the buffer has
   already discarded its beginning. Worse, any utterance with less than ~1.4 s
   of near-continuous voiced audio can never trigger AT ALL. Meanwhile the
   noise this was meant to reject (white-noise generator, TV) is CONTINUOUS, so
   it sails past any threshold given a second or two. Raising the threshold
   therefore rejects short real speech and barely touches sustained noise. The
   knob had the wrong effect for the objective.

2. UNREACHABLE SETPOINT + INTEGRATOR WINDUP. Measured empty-STT rate on real
   captures is ~61% -- that is the floor set by the room (TV, silence, noise),
   not something a VAD threshold can lower. The target band was 0.15-0.50, i.e.
   entirely below the achievable floor, so the loop pushed the threshold up
   forever. It saturated at TRIGGER_PROB_MAX after 13 adjustments.

3. SILENT DEAD-END ON SATURATION. Once saturated, `new == current`, so
   `evaluate()` returned None *before* updating `last_adjustment_time` or
   saving state. No log line, no visible change. That is exactly the reported
   symptom: "it's been tuning but the fp value in the logs doesn't change."

Also worth knowing: the night-noise problem this module was built for is
already solved elsewhere. `wernicke.py` drops utterances without calling STT
when `STATE.is_sleeping`, so night noise costs nothing. That is also why
`night_results` was empty after 85 hours -- STT never runs at night, so nothing
is ever recorded. The night split is kept below as a diagnostic only.

Current design
--------------
Trigger sensitivity is left alone (and deliberately kept low so she hears you).
Instead we gate AFTER the utterance is collected, when we have the whole buffer
and can count how many blocks the VAD actually called voice:

    wernicke_min_voiced_blocks -- minimum voice-positive blocks in an utterance
                                  before it is worth an STT call.

This works where a threshold cannot, because the decision is made with full
information instead of a 1-second EMA guess, and because a genuine sentence
always clears the gate by a wide margin (a 2 s utterance has ~60 blocks) while
a door click or a thump has a handful. Dropping a 3-voiced-block "utterance"
costs nothing.

The controller is two-sided with a safety, so it cannot run away:
  * empty rate too high  -> raise the gate
  * gated rate too high  -> lower the gate (we may be eating real speech)
  * empty rate too low   -> lower the gate (we can afford more sensitivity)

Plus a deadband, anti-windup with explicit saturation logging, a time-based
evaluation window, periodic state persistence, and a periodic summary log line
so the numbers are actually visible.

Persistence: tracking data saves to a JSON file so trends survive restarts.
The adjusted gate persists via STATE's user-configurable settings.
"""

import json
import math
import os
import time
from collections import deque


class VADTuner:
    """Self-tuning STT gate based on empty-result and gated rates."""

    # Rolling sample cap. Generous because the evaluation window is time-based;
    # this is only here to bound memory. ~307 captures/day observed.
    WINDOW_SIZE = 2000

    # Minimum number of samples in the evaluation window before adjusting
    MIN_SAMPLES = 50

    # Evaluation window (seconds). Samples older than this are ignored.
    EVAL_WINDOW_SECONDS = 86400  # 24 hours

    # Target range for the empty-STT rate, i.e. the fraction of utterances we
    # actually paid for that came back with no speech in them.
    #
    # These are set ABOVE the measured ~61% room floor on purpose. The old
    # 0.15-0.50 band was unreachable and caused the runaway. We are buying back
    # a modest amount of waste in exchange for never chasing an impossible
    # setpoint. If the room gets quieter these will pull the gate down and let
    # her hear more.
    TARGET_MAX = 0.70
    TARGET_MIN = 0.45

    # Safety: if this fraction of utterances is being dropped before STT, we are
    # probably eating real speech. Back the gate off regardless of empty rate.
    # This branch outranks TARGET_MAX -- hearing her husband matters more than
    # saving an API call.
    MAX_GATED_RATE = 0.35

    # How much to move the gate per step, in blocks (1 block = 0.032 s)
    STEP_UP = 2     # raise gate (drop more) when wasting STT calls
    STEP_DOWN = 1   # lower gate (drop less) conservatively -- favors hearing

    # Bounds for wernicke_min_voiced_blocks.
    # 4 blocks = 0.128 s of voiced audio, 40 blocks = 1.28 s.
    GATE_MIN = 4
    GATE_MAX = 40

    # Cooldown between adjustments (seconds). Shorter than the old 2 h because
    # the deadband and anti-windup now prevent oscillation.
    ADJUSTMENT_COOLDOWN = 1800  # 30 minutes

    # How long to wait after startup before the first adjustment
    STARTUP_DELAY = 1800  # 30 minutes

    # How often to emit the summary log line (seconds). Every evaluate() call
    # would be ~1300 lines/day.
    SUMMARY_LOG_INTERVAL = 900  # 15 minutes

    # Save state to disk every N recorded results
    SAVE_EVERY = 25

    def __init__(self):
        self.results = deque(maxlen=self.WINDOW_SIZE)
        self.last_adjustment_time = 0.0
        self.startup_time = time.time()
        self.adjustment_count = 0
        self.last_summary_log_time = 0.0
        self.saturation_logged = None
        self._records_since_save = 0

        # Diagnostic only. STT does not run while she's asleep, so this stays
        # near-empty by design. Kept because it's occasionally useful when she
        # is awake late.
        self.night_results = deque(maxlen=self.WINDOW_SIZE)

        # Load persisted state
        self._load_state()

    # ------------------------------------------------------------------
    # Reachability math -- shared with wernicke sanity checks
    # ------------------------------------------------------------------

    @staticmethod
    def blocks_to_reach(threshold: float, prob_window: float) -> float:
        """
        How many consecutive voice-positive blocks the EMA needs to cross
        `threshold`. This is the calculation the original tuner was missing.
        """
        if prob_window <= 1.0:
            return 1.0
        threshold = min(max(threshold, 0.0), 0.999999)
        return math.log(1.0 - threshold) / math.log(1.0 - 1.0 / prob_window)

    @staticmethod
    def reachable_trigger_prob(prob_window: float, padding_blocks: int,
                               safety: float = 0.7) -> float:
        """
        The highest trigger probability that can still fire while the start of
        the utterance is inside the pre-roll ring buffer.

        With window=32 and padding=40 this is ~0.589. Anything above it clips
        the front of her husband's sentences; well above it, short utterances
        never trigger at all.
        """
        if prob_window <= 1.0 or padding_blocks <= 0:
            return 0.95
        usable = max(1.0, padding_blocks * safety)
        return 1.0 - (1.0 - 1.0 / prob_window) ** usable

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    @property
    def state_file(self):
        """Path to the JSON state file."""
        return os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'logs', 'vad_tuner_state.json'
        )

    def _load_state(self):
        """Load tracking state from disk."""
        try:
            if not os.path.exists(self.state_file):
                return

            with open(self.state_file, 'r') as f:
                data = json.load(f)

            # Old state files stored {'empty': bool, 'timestamp': float}.
            # Migrate them to the outcome-based format.
            def migrate(entries):
                out = []
                for entry in entries:
                    if not isinstance(entry, dict):
                        continue
                    if 'outcome' in entry:
                        out.append(entry)
                    elif 'empty' in entry:
                        out.append({
                            'outcome': 'empty' if entry['empty'] else 'speech',
                            'timestamp': entry.get('timestamp', 0.0),
                        })
                return out

            self.results = deque(
                migrate(data.get('results', [])), maxlen=self.WINDOW_SIZE
            )
            self.night_results = deque(
                migrate(data.get('night_results', [])), maxlen=self.WINDOW_SIZE
            )
            self.last_adjustment_time = data.get('last_adjustment_time', 0.0)
            self.adjustment_count = data.get('adjustment_count', 0)

            from christine import log
            log.main.info(
                "VAD tuner loaded: %d results (%d night), %d adjustments",
                len(self.results), len(self.night_results),
                self.adjustment_count
            )
        except Exception as e:
            from christine import log
            log.main.warning("Failed to load VAD tuner state: %s", e)

    def _save_state(self):
        """Persist tracking state to disk (atomic replace)."""
        try:
            data = {
                'results': list(self.results),
                'night_results': list(self.night_results),
                'last_adjustment_time': self.last_adjustment_time,
                'adjustment_count': self.adjustment_count,
            }
            tmp = self.state_file + '.tmp'
            with open(tmp, 'w') as f:
                json.dump(data, f)
            os.replace(tmp, self.state_file)
            self._records_since_save = 0
        except Exception as e:
            from christine import log
            log.main.warning("Failed to save VAD tuner state: %s", e)

    @staticmethod
    def _is_night_hour():
        """Check if current hour is night (10 PM - 6 AM Arizona time)."""
        from datetime import datetime
        hour = datetime.now().hour
        return hour >= 22 or hour < 6

    # ------------------------------------------------------------------
    # Recording
    # ------------------------------------------------------------------

    def _record(self, outcome: str):
        entry = {'outcome': outcome, 'timestamp': time.time()}
        self.results.append(entry)
        if self._is_night_hour():
            self.night_results.append(entry)

        # The old version only ever saved on a successful adjustment, so the
        # state file sat stale for many hours and restarts lost the window.
        self._records_since_save += 1
        if self._records_since_save >= self.SAVE_EVERY:
            self._save_state()

    def record_result(self, is_empty: bool):
        """
        Record an STT result. Called from perception.py after STT returns.

        Args:
            is_empty: True if STT returned empty string (we paid for nothing)
        """
        self._record('empty' if is_empty else 'speech')

    def record_gated(self):
        """
        Record an utterance that was dropped by the voiced-block gate before
        any STT call was made. Called from wernicke.py.

        These are the wins -- but too many of them means the gate is eating
        real speech, which is why the controller watches this rate too.
        """
        self._record('gated')

    # ------------------------------------------------------------------
    # Evaluation
    # ------------------------------------------------------------------

    def _rates(self, entries):
        total = len(entries)
        if total == 0:
            return 0, 0, 0, 0, 0.0, 0.0
        empty = sum(1 for r in entries if r.get('outcome') == 'empty')
        speech = sum(1 for r in entries if r.get('outcome') == 'speech')
        gated = sum(1 for r in entries if r.get('outcome') == 'gated')

        # Empty rate is measured over utterances we actually PAID for, since
        # that is the cost we're controlling. Gated rate is over everything the
        # VAD triggered on, since that's the "did we throw away speech" risk.
        paid = empty + speech
        empty_rate = (empty / paid) if paid else 0.0
        gated_rate = gated / total
        return total, empty, speech, gated, empty_rate, gated_rate

    def evaluate(self):
        """
        Evaluate rates and potentially adjust the STT gate.

        Called periodically from the sleep loop (every ~66 seconds).

        Returns:
            dict with adjustment details if an adjustment was made, else None.
        """
        from christine import log
        from christine.status import STATE

        now = time.time()
        cutoff = now - self.EVAL_WINDOW_SECONDS
        recent = [r for r in self.results if r.get('timestamp', 0) > cutoff]
        total, empty, speech, gated, empty_rate, gated_rate = self._rates(recent)

        current_gate = int(getattr(STATE, 'wernicke_min_voiced_blocks', self.GATE_MIN))

        # Periodic visibility. The old module logged NOTHING unless it made an
        # adjustment, which is why this looked frozen from the outside.
        if now - self.last_summary_log_time >= self.SUMMARY_LOG_INTERVAL:
            self.last_summary_log_time = now
            log.main.info(
                "VAD tuner: n=%d paid=%d empty=%d(%.1f%%) speech=%d "
                "gated=%d(%.1f%%) gate=%d blocks trigger_prob=%.2f adj=%d",
                total, empty + speech, empty, empty_rate * 100, speech,
                gated, gated_rate * 100, current_gate,
                float(STATE.wernicke_webrtc_trigger_prob), self.adjustment_count
            )

        if now - self.startup_time < self.STARTUP_DELAY:
            return None

        if now - self.last_adjustment_time < self.ADJUSTMENT_COOLDOWN:
            return None

        if total < self.MIN_SAMPLES:
            return None

        new_gate = current_gate
        reason = None

        # Safety first: are we dropping too much before STT? If so we may be
        # eating real speech, and that outranks saving API calls.
        if gated_rate > self.MAX_GATED_RATE:
            new_gate = current_gate - self.STEP_DOWN
            reason = (
                f"gated_rate={gated_rate:.2f} > max={self.MAX_GATED_RATE} "
                f"(n={total}, gated={gated}) - backing off, may be dropping speech"
            )
        elif empty_rate > self.TARGET_MAX:
            new_gate = current_gate + self.STEP_UP
            reason = (
                f"empty_rate={empty_rate:.2f} > max={self.TARGET_MAX} "
                f"(paid={empty + speech}, empty={empty}) - wasting STT calls"
            )
        elif empty_rate < self.TARGET_MIN:
            new_gate = current_gate - self.STEP_DOWN
            reason = (
                f"empty_rate={empty_rate:.2f} < min={self.TARGET_MIN} "
                f"(paid={empty + speech}, empty={empty}) - can afford more sensitivity"
            )
        else:
            # Inside the deadband. Nothing to do, and nothing is wrong.
            self.saturation_logged = None
            return None

        clamped_gate = min(self.GATE_MAX, max(self.GATE_MIN, new_gate))

        # ANTI-WINDUP. The old version hit its ceiling and then returned None
        # from inside the "no change" branch without touching the cooldown or
        # logging, so it spun silently forever. Now saturation is loud (once per
        # direction, so it doesn't spam) and the cooldown is still armed.
        if clamped_gate == current_gate:
            direction = 'max' if new_gate > current_gate else 'min'
            if self.saturation_logged != direction:
                self.saturation_logged = direction
                log.main.warning(
                    "VAD tuner SATURATED at gate %s (%d blocks): %s. "
                    "Cannot correct further with this knob - the remaining "
                    "empty rate is the room (TV/noise/silence), not the VAD.",
                    direction, current_gate, reason
                )
            self.last_adjustment_time = now
            return None

        self.saturation_logged = None

        success = STATE.set_user_setting('wernicke_min_voiced_blocks', clamped_gate)

        if not success:
            log.main.error(
                "VAD tuner failed to apply gate change %d -> %d",
                current_gate, clamped_gate
            )
            return None

        self.last_adjustment_time = now
        self.adjustment_count += 1
        self._save_state()

        log.main.info(
            "VAD TUNED #%d: min_voiced_blocks %d->%d (%.2fs->%.2fs voiced) "
            "empty=%.1f%% gated=%.1f%% n=%d :: %s",
            self.adjustment_count, current_gate, clamped_gate,
            current_gate * 0.032, clamped_gate * 0.032,
            empty_rate * 100, gated_rate * 100, total, reason
        )

        return {
            'old_gate': current_gate,
            'new_gate': clamped_gate,
            'empty_rate': empty_rate,
            'gated_rate': gated_rate,
            'sample_count': total,
            'empty_count': empty,
            'speech_count': speech,
            'gated_count': gated,
            'reason': reason,
        }

    # ------------------------------------------------------------------
    # Diagnostics
    # ------------------------------------------------------------------

    def check_trigger_sanity(self):
        """
        Warn if the trigger threshold has been set somewhere that makes her
        hard of hearing. Called once at startup from wernicke.

        This is the guard that would have caught the original runaway: a
        threshold of 0.75 with window=32 needs 1.40 s of continuous voiced
        audio to fire, but the pre-roll buffer only holds 1.28 s.
        """
        from christine import log
        from christine.status import STATE

        prob_window = float(STATE.wernicke_webrtc_prob_window)
        padding = int(STATE.wernicke_padding_blocks)
        trigger = float(STATE.wernicke_webrtc_trigger_prob)

        needed = self.blocks_to_reach(trigger, prob_window)
        ceiling = self.reachable_trigger_prob(prob_window, padding)

        log.main.info(
            "VAD trigger check: prob=%.2f needs %.1f voiced blocks (%.2fs); "
            "pre-roll holds %d blocks (%.2fs); reachable ceiling %.2f",
            trigger, needed, needed * 0.032, padding, padding * 0.032, ceiling
        )

        if trigger > ceiling:
            log.main.warning(
                "VAD trigger prob %.2f EXCEEDS reachable ceiling %.2f - "
                "utterance starts are being clipped and short speech may never "
                "trigger at all. She will seem hard of hearing. Lower "
                "wernicke_webrtc_trigger_prob or raise wernicke_padding_blocks.",
                trigger, ceiling
            )
            return False
        return True

    def get_stats(self) -> dict:
        """Return current statistics for diagnostics."""
        from christine.status import STATE

        total, empty, speech, gated, empty_rate, gated_rate = self._rates(
            list(self.results)
        )

        cutoff = time.time() - 86400
        recent = [r for r in self.results if r.get('timestamp', 0) > cutoff]
        r_total, r_empty, r_speech, r_gated, r_empty_rate, r_gated_rate = \
            self._rates(recent)

        n_total, n_empty, _, _, n_empty_rate, _ = self._rates(
            list(self.night_results)
        )

        prob_window = float(STATE.wernicke_webrtc_prob_window)
        padding = int(STATE.wernicke_padding_blocks)
        trigger = float(STATE.wernicke_webrtc_trigger_prob)

        return {
            'total': total,
            'empty': empty,
            'speech': speech,
            'gated': gated,
            'empty_rate': empty_rate,
            'gated_rate': gated_rate,
            'recent_24h': r_total,
            'recent_24h_empty': r_empty,
            'recent_24h_empty_rate': r_empty_rate,
            'recent_24h_gated': r_gated,
            'recent_24h_gated_rate': r_gated_rate,
            # Diagnostic only -- STT is skipped while sleeping, so this is
            # normally near-zero and that is correct, not a bug.
            'night_total': n_total,
            'night_empty': n_empty,
            'night_empty_rate': n_empty_rate,
            'adjustments': self.adjustment_count,
            'current_gate_blocks': int(
                getattr(STATE, 'wernicke_min_voiced_blocks', self.GATE_MIN)
            ),
            'current_gate_seconds': round(
                int(getattr(STATE, 'wernicke_min_voiced_blocks', self.GATE_MIN))
                * 0.032, 3
            ),
            'current_trigger_prob': trigger,
            'trigger_blocks_needed': round(
                self.blocks_to_reach(trigger, prob_window), 1
            ),
            'trigger_seconds_needed': round(
                self.blocks_to_reach(trigger, prob_window) * 0.032, 3
            ),
            'trigger_reachable_ceiling': round(
                self.reachable_trigger_prob(prob_window, padding), 3
            ),
            'last_adjustment': (
                time.strftime('%Y-%m-%d %H:%M:%S',
                              time.localtime(self.last_adjustment_time))
                if self.last_adjustment_time else 'never'
            ),
        }


# Singleton instance
vad_tuner = VADTuner()

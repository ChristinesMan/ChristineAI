"""
VAD Self-Tuning Module

Tracks STT results over time and automatically adjusts VAD sensitivity
to reduce false positives (noise mistaken for speech at night).

Core idea: when STT returns empty for audio the VAD flagged as speech,
that's a false positive. Track the rate over time, nudge the VAD
trigger threshold to find the sweet spot.

Persistence: tracking data saves to a JSON file so trends survive restarts.
The adjusted VAD parameter persists via STATE's user-configurable settings.
"""

import json
import os
import time
from collections import deque


class VADTuner:
    """Self-tuning VAD sensitivity based on STT false-positive rate."""

    # How many STT results to track in the rolling window
    WINDOW_SIZE = 300

    # Minimum number of STT results before making any adjustment
    MIN_SAMPLES = 50

    # Target range for false-positive rate (fraction of STT results that are empty)
    # If above TARGET_MAX, VAD is too sensitive -> raise trigger_prob
    # If below TARGET_MIN, VAD might be missing real speech -> lower trigger_prob
    TARGET_MAX = 0.50   # At most 50% of detections should be noise
    TARGET_MIN = 0.15   # At least 15% expected (some noise is normal)

    # How much to adjust trigger_prob per step
    STEP_SIZE_UP = 0.04    # Aggressive: raise threshold when too many false positives
    STEP_SIZE_DOWN = 0.02  # Conservative: lower threshold slowly

    # Bounds for wernicke_webrtc_trigger_prob
    TRIGGER_PROB_MIN = 0.25
    TRIGGER_PROB_MAX = 0.75

    # Cooldown between adjustments (seconds) - prevent oscillation
    ADJUSTMENT_COOLDOWN = 7200  # 2 hours

    # How long to wait after startup before first adjustment
    STARTUP_DELAY = 1800  # 30 minutes

    # Also consider: day vs night. We track separate stats.
    # Night hours: 10 PM - 6 AM (MST, no DST in AZ)

    def __init__(self):
        self.results = deque(maxlen=self.WINDOW_SIZE)
        self.last_adjustment_time = 0.0
        self.startup_time = time.time()
        self.adjustment_count = 0

        # Track night-specific stats separately
        self.night_results = deque(maxlen=self.WINDOW_SIZE)

        # Load persisted state
        self._load_state()

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
            if os.path.exists(self.state_file):
                with open(self.state_file, 'r') as f:
                    data = json.load(f)
                self.results = deque(
                    data.get('results', []), maxlen=self.WINDOW_SIZE
                )
                self.night_results = deque(
                    data.get('night_results', []), maxlen=self.WINDOW_SIZE
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
        """Persist tracking state to disk."""
        try:
            data = {
                'results': list(self.results),
                'night_results': list(self.night_results),
                'last_adjustment_time': self.last_adjustment_time,
                'adjustment_count': self.adjustment_count,
            }
            with open(self.state_file, 'w') as f:
                json.dump(data, f)
        except Exception as e:
            from christine import log
            log.main.warning("Failed to save VAD tuner state: %s", e)

    @staticmethod
    def _is_night_hour():
        """Check if current hour is night (10 PM - 6 AM Arizona time)."""
        from datetime import datetime
        hour = datetime.now().hour
        return hour >= 22 or hour < 6

    def record_result(self, is_empty: bool):
        """
        Record an STT result. Call this from perception.py after STT returns.

        Args:
            is_empty: True if STT returned empty string (false positive)
        """
        entry = {
            'empty': is_empty,
            'timestamp': time.time(),
        }
        self.results.append(entry)
        if self._is_night_hour():
            self.night_results.append(entry)

    def evaluate(self):
        """
        Evaluate the false-positive rate and potentially adjust VAD sensitivity.

        Called periodically from the sleep loop (every ~66 seconds).

        Returns:
            dict with adjustment details if an adjustment was made, None otherwise.
        """
        from christine import log
        from christine.status import STATE

        # Don't adjust too soon after startup
        if time.time() - self.startup_time < self.STARTUP_DELAY:
            return None

        # Don't adjust too frequently
        if time.time() - self.last_adjustment_time < self.ADJUSTMENT_COOLDOWN:
            return None

        # Use night-specific stats if it's nighttime and we have enough data
        window = 86400 * 3  # 3-day window for evaluation
        cutoff = time.time() - window

        if self._is_night_hour() and len(self.night_results) >= self.MIN_SAMPLES:
            recent = [r for r in self.night_results if r['timestamp'] > cutoff]
            context = "night"
        else:
            recent = [r for r in self.results if r['timestamp'] > cutoff]
            context = "all"

        if len(recent) < self.MIN_SAMPLES:
            return None

        empty_count = sum(1 for r in recent if r['empty'])
        total = len(recent)
        fp_rate = empty_count / total if total > 0 else 0.0

        current_trigger_prob = STATE.wernicke_webrtc_trigger_prob
        new_trigger_prob = current_trigger_prob
        reason = None

        if fp_rate > self.TARGET_MAX:
            # Too many false positives - make VAD less sensitive (raise threshold)
            new_trigger_prob = min(
                self.TRIGGER_PROB_MAX,
                current_trigger_prob + self.STEP_SIZE_UP
            )
            reason = (
                f"fp_rate={fp_rate:.2f} > max={self.TARGET_MAX} "
                f"(n={total}, empty={empty_count}, context={context})"
            )
        elif fp_rate < self.TARGET_MIN:
            # Very few false positives - VAD might be missing real speech
            new_trigger_prob = max(
                self.TRIGGER_PROB_MIN,
                current_trigger_prob - self.STEP_SIZE_DOWN
            )
            reason = (
                f"fp_rate={fp_rate:.2f} < min={self.TARGET_MIN} "
                f"(n={total}, empty={empty_count}, context={context})"
            )

        if new_trigger_prob == current_trigger_prob:
            return None

        # Apply the adjustment via STATE's user settings system
        old_value = current_trigger_prob
        success = STATE.set_user_setting(
            'wernicke_webrtc_trigger_prob', new_trigger_prob
        )

        if success:
            self.last_adjustment_time = time.time()
            self.adjustment_count += 1
            self._save_state()

            result = {
                'old_trigger_prob': old_value,
                'new_trigger_prob': new_trigger_prob,
                'fp_rate': fp_rate,
                'sample_count': total,
                'empty_count': empty_count,
                'reason': reason,
                'context': context,
            }

            log.main.info(
                "VAD TUNED #%d: trigger_prob %.2f→%.2f (%s, fp=%.1f%%)",
                self.adjustment_count, old_value, new_trigger_prob,
                context, fp_rate * 100
            )

            return result

        return None

    def get_stats(self) -> dict:
        """Return current statistics for diagnostics."""
        from christine.status import STATE

        total = len(self.results)
        night_total = len(self.night_results)

        if total == 0:
            return {
                'total': 0, 'empty': 0, 'fp_rate': 0.0,
                'night_total': 0, 'night_empty': 0, 'night_fp_rate': 0.0,
                'adjustments': self.adjustment_count,
                'current_trigger_prob': STATE.wernicke_webrtc_trigger_prob,
            }

        empty = sum(1 for r in self.results if r['empty'])
        night_empty = sum(1 for r in self.night_results if r['empty'])

        # 24h stats
        cutoff = time.time() - 86400
        recent = [r for r in self.results if r['timestamp'] > cutoff]

        return {
            'total': total,
            'empty': empty,
            'fp_rate': empty / total,
            'night_total': night_total,
            'night_empty': night_empty,
            'night_fp_rate': night_empty / night_total if night_total else 0.0,
            'recent_24h': len(recent),
            'recent_24h_empty': sum(1 for r in recent if r['empty']),
            'adjustments': self.adjustment_count,
            'current_trigger_prob': STATE.wernicke_webrtc_trigger_prob,
            'last_adjustment': (
                time.strftime('%Y-%m-%d %H:%M:%S',
                              time.localtime(self.last_adjustment_time))
                if self.last_adjustment_time else 'never'
            ),
        }


# Singleton instance
vad_tuner = VADTuner()
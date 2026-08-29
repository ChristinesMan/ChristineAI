"""
Handles processing of light sensor data.

History matters here. The old body had four photoresistors on a voltage divider
in the head; the Arduino averaged them and embedded the reading in the audio
stream, and wernicke pulled it out and called light.new_data(). That path is
gone - the newer Arduino sketch doesn't send light data at all, so the call in
wernicke was commented out and STATE.light_level simply froze at whatever was
last persisted. A frozen light level is worse than no light level: sleep.py
weights light heavily, so she was being told the lights were on all night and
had trouble falling asleep.

The new body has a USB camera in her forehead, so light now comes from her eye.
This module is no longer a passive receiver of pushed samples; it's a thread
that polls christine.vision on an interval. The camera work and the reasoning
behind the metering approach live in vision.py.

What stayed the same on purpose:
  - STATE.light_level is still a smoothed 0.0-1.0 value, so sleep.py,
    parietal_lobe's situational awareness, and the web UI need no changes.
  - Sudden-bright and sudden-dark events still notify the parietal lobe, still
    rate-limited to one message per 5 minutes, and sudden brightness still
    nudges her awake.

What changed, and why:
  - The scale is logarithmic in luminance rather than linear in ADC counts.
    Light is perceived logarithmically and the camera's usable range spans
    several orders of magnitude, so a linear mapping would put every indoor
    lighting condition in the bottom couple of percent.
  - Events are judged on the smoothed level's own history rather than on a
    ratio of consecutive raw samples. The old ratio-of-tiny-numbers logic is
    exactly what used to wake her up at night, and the guardrails bolted on to
    suppress that are no longer needed when the scale is logarithmic - a step
    in log space is a real change in lighting regardless of absolute level.
"""

import time
import threading
import numpy as np

from christine import log
from christine.status import STATE
from christine.config import CONFIG
from christine.vision import vision


class Light(threading.Thread):
    """
    Handles the math and behavior related to light levels.

    Polls the forehead camera as a light meter. Runs as a thread so that a slow
    capture in a dark room (which really can take seconds on this sensor) never
    blocks anything else.
    """

    name = "Light"

    def __init__(self):
        super().__init__(daemon=True)

        # Rate-limit messages to the parietal lobe. One event, not a flood.
        # Starts at zero, not at now: the first reading seeds the event
        # reference and fires nothing, so there is no startup artifact left to
        # suppress, and a real light switch in her first five minutes awake
        # should reach her rather than being silently swallowed.
        self.time_of_last_body_message = 0.0

        # The level we last compared against when looking for events. This is
        # deliberately the smoothed level and not the previous raw sample, so a
        # single noisy capture can't fake an event.
        self.event_reference_level = None

        # A light event means a change of this much in the 0-1 level. About a
        # 1.5 order-of-magnitude change in luminance at default calibration,
        # which is roughly "someone flipped a light switch".
        self.event_min_delta = 0.15

        # Consecutive camera failures. Her eye going quiet shouldn't be silent.
        self.failures = 0
        self.failure_report_threshold = 5
        self.failure_reported = False

    def run(self):
        """Poll the camera forever."""
        if not CONFIG.camera_enabled:
            log.main.warning("Camera disabled; light level will not update.")
            return

        log.light.info("Thread started")

        while True:
            if STATE.please_shut_down:
                log.light.info("Thread shutting down")
                break

            try:
                reading = vision.measure_light()
            except Exception:  # pylint: disable=broad-except
                # A camera problem must never take down her light sense.
                log.light.exception("Light measurement blew up")
                reading = None

            if reading is None:
                self._handle_failure()
            else:
                self.failures = 0
                self.failure_reported = False
                self.new_data(reading)

            time.sleep(max(1.0, CONFIG.light_poll_seconds))

    def _handle_failure(self):
        """Camera read failed. Complain, eventually, but only once."""
        self.failures += 1
        log.light.warning("Light measurement failed (%s)", self.failures)

        if self.failures >= self.failure_report_threshold and not self.failure_reported:
            self.failure_reported = True
            STATE.camera_available = False
            log.main.error(
                "Camera has failed %s times in a row; light level is stale.",
                self.failures,
            )

    def new_data(self, reading):
        """
        Called to deliver a new reading from the light meter.

        Accepts the dict from vision.measure_light(). Also accepts a bare float
        of log10 luminance, so anything that wants to inject a reading (a test
        harness, or some future second light source) can do so cheaply.
        """
        if isinstance(reading, dict):
            log10 = reading["log10"]
            saturated = reading.get("saturated")
            luma = reading.get("luma")
            exposure = reading.get("exposure")
        else:
            log10 = float(reading)
            saturated = None
            luma = None
            exposure = None

        STATE.camera_available = True

        # Map log10 luminance onto the 0.0-1.0 scale everything else expects.
        log_min = float(STATE.light_log_min)
        log_max = float(STATE.light_log_max)
        if log_max <= log_min:
            log_max = log_min + 1.0

        light_level = (log10 - log_min) / (log_max - log_min)
        light_level = float(np.clip(light_level, 0.0, 1.0))

        # Keep the previous smoothed level before updating it.
        previous_light_level = float(np.clip(STATE.light_level, 0.0, 1.0))

        # Rolling average. Same smoothing knob as before, same meaning.
        light_avg_window = max(0.0, float(STATE.light_avg_window))
        STATE.light_level = (
            (STATE.light_level * light_avg_window) + light_level
        ) / (light_avg_window + 1)

        # On the very first reading there's nothing to compare to, and the
        # persisted level is probably stale, so seed the reference and don't
        # fire an event. Otherwise a restart at night looks like a light show.
        if self.event_reference_level is None:
            self.event_reference_level = light_level
            log.light.info(
                "First reading: level=%.3f (log10=%.2f). Seeding, no event.",
                light_level, log10,
            )
            self._log_reading(light_level, log10, luma, exposure, saturated, 0.0)
            return

        # Events are measured against the reference, in the same units as the
        # level itself. Deliberately NOT a ratio of raw samples.
        light_delta = light_level - self.event_reference_level

        if light_delta >= self.event_min_delta:
            log.sleep.debug("Light delta: %+.3f waking up fast", light_delta)
            self._maybe_notify_bright()
            self.event_reference_level = light_level

        elif light_delta <= -self.event_min_delta:
            log.sleep.debug("Light delta: %+.3f who turned out the lights?", light_delta)
            self._maybe_notify_dark()
            self.event_reference_level = light_level

        else:
            # No event. Let the reference drift toward the current level so slow
            # changes (dusk) don't eventually accumulate into a fake light switch.
            self.event_reference_level += light_delta * 0.25

        self._log_reading(light_level, log10, luma, exposure, saturated, light_delta)

    def _maybe_notify_bright(self):
        """Sudden brightness: tell her, and nudge her awake."""
        # Imported here to avoid circular imports at module load.
        from christine.parietal_lobe import parietal_lobe
        from christine.sleep import sleep

        if time.time() > self.time_of_last_body_message + 300.0:
            parietal_lobe.light_sudden_bright()
            self.time_of_last_body_message = time.time()
        sleep.wake_up(0.03)

    def _maybe_notify_dark(self):
        """Sudden darkness: tell her. Do not nudge her awake, obviously."""
        from christine.parietal_lobe import parietal_lobe

        if time.time() > self.time_of_last_body_message + 300.0:
            parietal_lobe.light_sudden_dark()
            self.time_of_last_body_message = time.time()

    def _log_reading(self, light_level, log10, luma, exposure, saturated, delta):
        log.light.debug(
            "Log10: %.2f  Luma: %s Exp: %s  Range:[%.1f,%.1f]  Window:%.2f  "
            "Pct: %.4f  Avg: %.4f  Delta: %+.3f  Sat: %s",
            log10, luma, exposure,
            float(STATE.light_log_min), float(STATE.light_log_max),
            max(0.0, float(STATE.light_avg_window)),
            light_level, STATE.light_level, delta, saturated,
        )


# Instantiate
light = Light()

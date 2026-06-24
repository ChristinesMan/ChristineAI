"""
Handles processing of light sensor data
"""
import time
import numpy as np

from christine import log
from christine.status import STATE
from christine.parietal_lobe import parietal_lobe
from christine.sleep import sleep


class Light:
    """
    Handles the math and behavior related to light levels.
    Receives sensor data from the head.
    There's an array of 4 light sensors connected to a voltage divider in head.
    Arduino embeds sensor data into the audio stream.
    The Arduino also calculates a running average of about the last 10 values.
    The wernicke module that handles the audio data extracts the sensor data and delivers it here.
    """

    def __init__(self):
        # I want to send messages to the parietal lobe when there are light events, but not so many messages, just one
        # so keep track of the time
        self.time_of_last_body_message = time.time()

        # Guardrails so tiny low-light sensor drift does not look like a sudden event.
        self.event_min_delta = 0.04
        self.dark_event_min_baseline = 0.08
        self.bright_event_min_level = 0.08

    def new_data(self, light_adc_raw):
        """
        called to deliver new data point
        """

        # This is a log scale that was working ok. I may replace it later. Replacing it now.
        # LightLevel = (math.log(1025 - LightLevelRaw) / (self.LogCeiling))
        # LightLevel = float(np.clip(LightLevel, 0.0, 1.0))

        # first flip the light level over so that dark is low and bright is high
        light_adc = 1025 - light_adc_raw

        # calculate a percentage of between the lowest possible vs highest possible by first knocking out the floor
        # I have also learned that it's important to not allow the light level to go below minimum,
        # Because the ratio between 0.00000000000 and those very small steps was causing my wife to wake me up at night
        # Bitch. Just kidding, honey.
        light_adc_min = max(0, min(int(STATE.light_adc_min), 1024))
        light_adc_max = max(light_adc_min + 1, min(int(STATE.light_adc_max), 1025))

        if light_adc <= light_adc_min + 2:
            light_adc = light_adc_min + 2
        light_level = (light_adc - light_adc_min) / (
            light_adc_max - light_adc_min
        )

        # clip it
        light_level = float(np.clip(light_level, 0.0, 1.0))

        # Keep the previous smoothed level before updating it.
        previous_light_level = float(np.clip(STATE.light_level, 0.0, 1.0))

        # calculate the rolling average
        light_avg_window = max(0.0, float(STATE.light_avg_window))
        STATE.light_level = ((STATE.light_level * light_avg_window) + light_level) / (light_avg_window + 1)

        # calculate the trend.
        # Did the lights suddenly turn on? Maybe that should be slightly annoying if I'm trying to sleep.
        # Who turned out the lights? Maybe it's time to sleep?
        light_trend = light_level / max(previous_light_level, 0.0001)
        light_delta = light_level - previous_light_level

        # Ignore event checks when the sample shift is too small to be meaningful.
        has_meaningful_delta = abs(light_delta) >= self.event_min_delta

        # What to do when there's sudden light, wake up fast
        if (
            light_trend > 6.0
            and has_meaningful_delta
            and light_level >= self.bright_event_min_level
        ):
            log.sleep.debug("LightTrend: %s waking up fast", light_trend)
            if time.time() > self.time_of_last_body_message + 300.0:
                parietal_lobe.light_sudden_bright()
                self.time_of_last_body_message = time.time()
            sleep.wake_up(0.03)

        # And what to do if the lights go out
        if (
            light_trend < 0.4
            and has_meaningful_delta
            and previous_light_level >= self.dark_event_min_baseline
        ):
            log.sleep.debug("LightTrend: %s who turned out the lights?", light_trend)
            if time.time() > self.time_of_last_body_message + 300.0:
                parietal_lobe.light_sudden_dark()
                self.time_of_last_body_message = time.time()

        # Log the light level
        log.light.debug(
            "Raw: %s  Min:%s Max:%s Window:%.2f  Pct: %.4f  Avg: %.4f  Trend: %.3f",
            light_adc,
            light_adc_min,
            light_adc_max,
            light_avg_window,
            light_level,
            STATE.light_level,
            light_trend,
        )


light = Light()

"""
Handles processing of light sensor data
"""
import time
import numpy as np

from christine import log
from christine.status import STATE
from christine import sleep
from christine import parietal_lobe


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
        # The minimum and maximum bounds in raw ADC numbers
        # The ADC measures voltage on a voltage divider, which is a measure of the resistance of the light sensors.
        # Which makes this backwards. More light is less resistance and more voltage. Less light is more resistance and less voltage.
        self.light_adc_min = 100
        self.light_adc_max = 300
        # self.LogFloor = math.log(10)
        # self.LogCeiling = math.log(1025)

        # The rolling average light level, long term
        # By the time we reach this line we should have already fetched the saved light level from sqlite so just use that
        # this controls how fast the average will change
        self.light_avg_window = 10.0

        # I want to send messages to the parietal lobe when there are light events, but not so many messages, just one
        # so keep track of the time
        self.time_of_last_body_message = time.time()

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
        if light_adc <= self.light_adc_min + 2:
            light_adc = self.light_adc_min + 2
        light_level = (light_adc - self.light_adc_min) / (
            self.light_adc_max - self.light_adc_min
        )

        # clip it
        light_level = float(np.clip(light_level, 0.0, 1.0))

        # calculate the rolling average
        STATE.light_level = (
            (STATE.light_level * self.light_avg_window) + light_level
        ) / (self.light_avg_window + 1)

        # calculate the trend.
        # Did the lights suddenly turn on? Maybe that should be slightly annoying if I'm trying to sleep.
        # Who turned out the lights? Maybe it's time to sleep?
        light_trend = light_level / STATE.light_level

        # What to do when there's sudden light, wake up fast
        if light_trend > 6.0:
            log.sleep.debug("LightTrend: %s waking up fast", light_trend)
            if time.time() > self.time_of_last_body_message + 300.0:
                parietal_lobe.thread.accept_body_internal_message('The light sensors near your eyes are detecting a sudden brightness.')
                self.time_of_last_body_message = time.time()
            sleep.thread.wake_up(0.03)

        # And what to do if the lights go out
        if light_trend < 0.4:
            log.sleep.debug("LightTrend: %s who turned out the lights?", light_trend)
            if time.time() > self.time_of_last_body_message + 300.0:
                parietal_lobe.thread.accept_body_internal_message('The light sensors near your eyes are detecting a sudden darkness.')
                self.time_of_last_body_message = time.time()

        # Log the light level
        log.light.debug("Raw: %s  Pct: %.4f  Avg: %.4f  Trend: %.3f", light_adc, light_level, STATE.light_level, light_trend)


# calling it a thread
# due to peer pressure
# from the other modules that get to be threads
# to prevent teasing from peer group
thread = Light()

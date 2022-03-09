import math
import numpy as np

import log
import status
import sleep

class Light():
    """
        Handles the math and behavior related to light levels. 
        Receives sensor data from the head. 
        There's an array of 4 light sensors connected to a voltage divider in head. 
        Arduino embeds sensor data into the audio stream. 
        The Arduino also calculates a running average of about the last 10 values. 
        The wernicke module that handles the audio data extracts the sensor data and delivers it here. 
    """

    def __init__ (self):

        # The minimum and maximum bounds in raw ADC numbers
        # The ADC measures voltage on a voltage divider, which is a measure of the resistance of the light sensors. 
        # Which makes this backwards. More light is less resistance and more voltage. Less light is more resistance and less voltage. 
        self.MinLight = 110
        self.MaxLight = 300
        # self.LogFloor = math.log(10)
        # self.LogCeiling = math.log(1025)

        # The rolling average light level, long term
        # By the time we reach this line we should have already fetched the saved light level from sqlite so just use that
        # this controls how fast the average will change
        self.AverageWindow = 100.0

    # called to deliver new data point
    def NewData(self, LightLevelRaw):

        try:

            # This is a log scale that was working ok. I may replace it later. Replacing it now. 
            # LightLevel = (math.log(1025 - LightLevelRaw) / (self.LogCeiling))
            # LightLevel = float(np.clip(LightLevel, 0.0, 1.0))

            # first flip the light level over so that dark is low and bright is high
            LightLevel = 1025 - LightLevelRaw

            # calculate a percentage of between the lowest possible vs highest possible by first knocking out the floor
            LightLevelPct = (LightLevel - self.MinLight) / (self.MaxLight - self.MinLight)

            # clip it
            LightLevelPct = float(np.clip(LightLevelPct, 0.0, 1.0))

            # calculate the rolling average
            status.LightLevelPct = ((status.LightLevelPct * self.AverageWindow) + LightLevelPct) / (self.AverageWindow + 1)

            # calculate the trend. 
            # Did the lights suddenly turn on? Maybe that should be slightly annoying if I'm trying to sleep. 
            # Who turned out the lights? Maybe it's time to sleep? 
            LightTrend = LightLevelPct / status.LightLevelPct

            # What to do when there's sudden light, wake up fast
            if LightTrend > 3.0:
                log.sleep.debug(f'LightTrend: {LightTrend} waking up fast')
                sleep.thread.WakeUpABit(0.01)

            # Log the light level
            log.light.debug('Raw: {0}  Pct: {1:.4f}  Avg: {2:.4f}  Trend: {3:.3f}'.format(LightLevel, LightLevelPct, status.LightLevelPct, LightTrend))


        # log exception in the main.log
        except Exception as e:
            log.main.error('Thread died. {0} {1} {2}'.format(e.__class__, e, log.format_tb(e.__traceback__)))


# calling it a thread
# due to peer pressure
# from the other modules that get to be threads
# to prevent teasing from peer group
thread = Light()

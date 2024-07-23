"""
Handles the touch sensor inside head
"""
import time
import numpy as np
import scipy.stats

from christine import log
from christine.status import STATE
from christine.parietal_lobe import parietal_lobe
from christine.sleep import sleep


class Touch:
    """
    When Christine gets touched, stuff should happen. That happens here.
    """

    def __init__(self):
        # the in-head arduino sends the raw capacitance value. 12 channels starting with 0
        # So far only the mouth wire is useable

        # Keep track of the baselines
        # if the channel isn't even hooked up, None
        self.baselines = [None, None, 0, None, 0, None, 0, None, None, None, None, None]

        # if data point is this amount less than the baseline, it's a touch
        # a touch always results in a lower capacitance number, that's how sensor works
        # therefore, lower = sensitive, higher = the numbness
        # mouth maybe too sensitive. testing mouth change from 100 to 120
        self.sensitivity = [
            None,
            None,
            100,
            None,
            100,
            None,
            100,
            None,
            None,
            None,
            None,
            None,
        ]

        # labels
        self.channel_labels = [
            None,
            None,
            "MouthHerLeft",
            None,
            "MouthMiddle",
            None,
            "MouthHerRight",
            None,
            None,
            None,
            None,
            None,
        ]

        # How many raw values do we want to accumulate before re-calculating the baselines
        # I started at 500 but it wasn't self-correcting very well
        self.baseline_data_length = 100

        # there are 12 channels, and we only have 3 connected to anything
        # accumulate data in an array of numpy arrays, and every once in a while we cum and calc the mode
        self.used_channels = []
        self.data = [None] * 12
        for channel in range(0, 12):
            if self.channel_labels[channel] is not None:
                self.used_channels.append(channel)
                self.data[channel] = np.zeros(self.baseline_data_length)

        # counter to help accumulate values
        self.counter = 0

        # I want to limit how often jostled messages get sent to the LLM
        self.time_of_last_kiss = time.time()

    def new_data(self, touch_data):
        """
        Called to deliver new data point
        """

        # for whatever of the 12 channels is hooked up
        for channel in self.used_channels:

            # save data in an array
            self.data[channel][self.counter % self.baseline_data_length] = touch_data[channel]

            # Detect touches, and throw out glitches, dunno why that happens
            if (
                self.baselines[channel] - touch_data[channel] > self.sensitivity[channel]
                and touch_data[channel] > 20
                and time.time() > self.time_of_last_kiss + 60
            ):

                self.time_of_last_kiss = time.time()

                # if we got touched, it should imply I am near
                STATE.lover_proximity = ((STATE.lover_proximity * 5.0) + 1.0) / 6.0

                log.touch.info(
                    "Touched: %s (%s)  LoverProximity: %s",
                    self.channel_labels[channel],
                    touch_data[channel],
                    STATE.lover_proximity,
                )

                if STATE.is_sleeping is False:
                    parietal_lobe.mouth_touched()

                sleep.wake_up(0.05)

        self.counter += 1

        # every so often we want to update the baselines
        # these normally should never change
        if self.counter % self.baseline_data_length == 0:
            for channel in self.used_channels:
                self.baselines[channel] = scipy.stats.mode(self.data[channel])[0]

            log.touch.debug("Updated baselines: %s", self.baselines)


# instantiate
touch = Touch()

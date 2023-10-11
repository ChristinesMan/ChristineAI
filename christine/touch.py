"""
Handles the touch sensor inside head
"""
import time
import random
import numpy as np
import scipy.stats

from christine import log
from christine.status import SHARED_STATE
from christine import broca
from christine import sleep


class Touch:
    """
    When Christine gets touched, stuff should happen. That happens here.
    """

    def __init__(self):
        # the in-head arduino sends the raw capacitance value. 12 channels starting with 0
        # So far only the mouth wire is useable

        # Keep track of the baselines
        # if the channel isn't even hooked up, None
        # I vaguely remamber hooking up some, dunno where they are anymore
        self.baselines = [None, None, 0, None, 0, None, 0, None, None, None, None, None]

        # if data point is this amount less than the baseline, it's a touch
        # a touch always results in a lower capacitance number, that's how sensor works
        # therefore, lower = sensitive, higher = the numbness
        self.sensitivity = [
            None,
            None,
            100,
            None,
            50,
            None,
            50,
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
            "Mouth",
            None,
            "LeftCheek",
            None,
            "RightCheek",
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

    def new_data(self, touch_data):
        """
        Called to deliver new data point
        """

        # for all 12 channels
        for channel in self.used_channels:
            # save data in an array
            self.data[channel][
                self.counter % self.baseline_data_length
            ] = touch_data[channel]

            # Detect touches, and throw out glitches, dunno why that happens
            if (
                self.baselines[channel] - touch_data[channel]
                > self.sensitivity[channel]
                and touch_data[channel] > 20
            ):
                # if we got touched, it should imply I am near
                SHARED_STATE.lover_proximity = (
                    (SHARED_STATE.lover_proximity * 5.0) + 1.0
                ) / 6.0
                log.touch.info(
                    "Touched: %s (%s)  LoverProximity: %s",
                    self.channel_labels[channel],
                    touch_data[channel],
                    SHARED_STATE.lover_proximity,
                )

                # probably faster to test via int than the Str 'Mouth'
                # if channel == 2:
                # going to test out making sounds for cheeks, not only mouth
                SHARED_STATE.dont_speak_until = (
                    time.time() + 2.0 + (random.random() * 3.0)
                )
                if SHARED_STATE.is_sleeping is False:
                    broca.thread.queue_sound(from_collection="kissing", play_no_wait=True)
                sleep.thread.wake_up(0.05)
                SHARED_STATE.should_speak_chance += 0.05

        self.counter += 1

        # every so often we want to update the baselines
        # these normally should never change
        if self.counter % self.baseline_data_length == 0:
            for channel in self.used_channels:
                self.baselines[channel] = scipy.stats.mode(self.data[channel])[0]

            log.touch.debug("Updated baselines: %s", self.baselines)


# instantiate and start thread
# it's not really a thread,
# but it doesn't need to know that.
thread = Touch()

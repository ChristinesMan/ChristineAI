import time
import random
import numpy as np
import scipy.stats

import log
import status
import breath
import sleep

# When Christine gets touched, stuff should happen. That happens here. 
class Touch():

    def __init__ (self):

        # the in-head arduino sends the raw capacitance value. 12 channels starting with 0
        # So far only the mouth wire is useable

        # Keep track of the baselines
        # if the channel isn't even hooked up, None
        # I vaguely remamber hooking up some, dunno where they are anymore
        self.Baselines = [None, None, 0, None, 0, None, 0, None, None, None, None, None]

        # if data point is this amount less than the baseline, it's a touch
        # a touch always results in a lower capacitance number, that's how sensor works
        # therefore, lower = sensitive, higher = the numbness
        self.Sensitivity = [None, None, 30, None, 20, None, 20, None, None, None, None, None]

        # labels
        self.ChannelLabels = [None, None, 'Mouth', None, 'LeftCheek', None, 'RightCheek', None, None, None, None, None]

        # How many raw values do we want to accumulate before re-calculating the baselines
        # I started at 500 but it wasn't self-correcting very well
        self.BaselineDataLength = 100

        # accumulate data here, and every once in a while we cum and calc the mode
        self.Data = [ np.zeros(self.BaselineDataLength) ] * 12

        # counter to help accumulate values
        self.Counter = 0

    # called to deliver new data point
    def NewData(self, TouchData):

        try:

            # for all 12 channels
            for channel in range(0, 12):

                # if we're not using this channel, just fuck it
                if self.ChannelLabels[channel] == None:
                    continue

                # save data in an array
                self.Data[channel][self.Counter % self.BaselineDataLength] = TouchData[channel]

                # Detect touches
                if self.Baselines[channel] - TouchData[channel] > self.Sensitivity[channel]:

                    # if we got touched, it should imply I am near
                    status.LoverProximity = ((status.LoverProximity * 5.0) + 1.0) / 6.0
                    log.touch.debug(f'Touched: {self.ChannelLabels[channel]} ({TouchData[channel]})  LoverProximity: {status.LoverProximity}')

                    # probably faster to test via int than the Str 'Mouth'
                    # if channel == 2:
                    # going to test out making sounds for cheeks, not only mouth
                    status.DontSpeakUntil = time.time() + 2.0 + (random.random() * 3.0)
                    if status.IAmSleeping == False:
                        breath.thread.QueueSound(FromCollection='kissing', IgnoreSpeaking=True, CutAllSoundAndPlay=True, Priority=4)
                    sleep.thread.WakeUpABit(0.05)
                    # GlobalStatus.TouchedLevel += 0.1
                    status.ChanceToSpeak += 0.05

            self.Counter += 1

            # every so often we want to update the baselines
            # these normally should never change
            if self.Counter % self.BaselineDataLength == 0:

                for channel in range(0, 12):

                    if self.ChannelLabels[channel] == None:
                        continue

                    self.Baselines[channel] = scipy.stats.mode(self.Data[channel]).mode[0]

                log.touch.debug(f'Updated baselines: {self.Baselines}')


        except Exception as e:
            log.main.error('Thread died. {0} {1} {2}'.format(e.__class__, e, log.format_tb(e.__traceback__)))


# instantiate and start thread
# it's not really a thread,
# but it doesn't need to know that. 
thread = Touch()

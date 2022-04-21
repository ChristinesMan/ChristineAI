import time
import threading
import random
import numpy as np

import log
import status
import breath
import wernicke

# This script keeps track of wife sleepiness, waking up and going to sleep, whining that she's tired. But it won't be an annoying whine, not like a real woman. 
class Sleep(threading.Thread):
    name = 'Sleep'

    def __init__ (self):
        threading.Thread.__init__(self)

        # Some basic state variables
        self.AnnounceTiredTime = False
        self.LocalTime = time.localtime()

        # The current conditions, right now. Basically light levels, gyro, noise level, touch, etc all added together, then we calculate a running average to cause gradual drowsiness. zzzzzzzzzz.......
        self.Environment = 0.5

        # How quickly should wakefulness change?
        self.EnvironmentAverageWindow = 5.0

        # How quickly should the daily hourly wakefulness trend change
        self.TrendAverageWindow = 10.0

        # Weights
        self.LightWeight = 10
        self.GyroWeight = 4
        self.TiltWeight = 3
        self.TotalWeight = self.LightWeight + self.GyroWeight + self.TiltWeight

        # if laying down, 0, if not laying down, 1.         
        self.Tilt = 0.0

        # At what time should we expect to be in bed or wake up? 
        self.WakeHour = 6
        self.SleepHour = 21

        # At what point to STFU at night
        self.MinWakefulnessToBeAwake = 0.25

    def run(self):
        log.sleep.debug('Thread started.')

        try:

            while True:

                # graceful shutdown
                if status.PleaseShutdown:
                    log.sleep.info('Thread shutting down')
                    break

                # Get the local time, for everything that follows
                self.LocalTime = time.localtime()

                # set the gyro tilt for the calculation that follows
                if status.IAmLayingDown == True:
                    self.Tilt = 0.0
                else:
                    self.Tilt = 1.0

                # Calculate current conditions which we're calling Environment
                self.Environment = ((self.LightWeight * status.LightLevelPct) + (self.GyroWeight * status.JostledLevel) + (self.TiltWeight * self.Tilt)) / self.TotalWeight

                # clip it, can't go below 0 or higher than 1
                self.Environment = float(np.clip(self.Environment, 0.0, 1.0))

                # Update the running average that we're using for wakefulness
                status.Wakefulness = ((status.Wakefulness * self.EnvironmentAverageWindow) + self.Environment) / (self.EnvironmentAverageWindow + 1)

                # clip that
                status.Wakefulness = float(np.clip(status.Wakefulness, 0.0, 1.0))

                # After updating wakefulness, figure out whether we crossed a threshold. 
                self.EvaluateWakefulness()

                # log it
                log.sleep.debug('Environment = %.2f  LightLevel = %.2f  JostledLevel = %.2f  Wakefulness = %.2f', self.Environment, status.LightLevelPct, status.JostledLevel, status.Wakefulness)

                # If it's getting late, set a future time to "whine" in a cute, endearing way
                if self.NowItsLate():
                    self.SetTimeToWhine()
                    self.StartBreathingSleepy()
                if self.TimeToWhine():
                    self.Whine()

                # if sleeping, drop the breathing intensity down a bit
                # eventually after about 15m this will reach 0.0 and stay there
                if status.IAmSleeping == True:

                    # down, down, dooooownnnnn
                    status.BreathIntensity -= 0.06

                    # clip it
                    status.BreathIntensity = float(np.clip(status.BreathIntensity, 0.0, 1.0))

                # if we're below a certain wakefulness, I want to give the wernicke a break
                # help prevent long term buildup of heat
                if status.Wakefulness < 0.1:
                    wernicke.thread.StopProcessing()
                else:
                    wernicke.thread.StartProcessing()

                time.sleep(66)

        # log exception in the main.log
        except Exception as e:
            log.main.error('Thread died. {0} {1} {2}'.format(e.__class__, e, log.format_tb(e.__traceback__)))

    def WakeUpABit(self, value):

        # add to the global status variable
        status.Wakefulness += value

        # clip it
        status.Wakefulness = float(np.clip(status.Wakefulness, 0.0, 1.0))

        # log it
        log.sleep.debug(f'Woke up a bit: {value}  Wakefulness: {status.Wakefulness}')

        # evaluate whether the change that just happened caused waking or whatever
        self.EvaluateWakefulness()

    # Update the boolean that tells everything else whether sleeping or not
    # I also want to detect when sleeping starts
    def EvaluateWakefulness(self):

        if self.JustFellAsleep() == True:
            log.sleep.info('JustFellAsleep')

            # try to prevent wobble by throwing it further towards sleep
            status.Wakefulness -= 0.1

            # start progression from loud to soft sleepy breathing sounds
            # I was getting woke up a lot with all the cute hmmm sounds that are in half of the sleeping breath sounds
            status.BreathIntensity = 1.0

            breath.thread.QueueSound(FromCollection='goodnight', PlayWhenSleeping=True, Priority=8, CutAllSoundAndPlay=True)
            status.IAmSleeping = True
            breath.thread.BreathChange('breathe_sleepy')

        if self.JustWokeUp() == True:
            log.sleep.info('JustWokeUp')

            # try to prevent wobble by throwing it further towards awake
            status.Wakefulness += 0.1
            
            status.IAmSleeping = False
            breath.thread.BreathChange('breathe_normal')
            breath.thread.QueueSound(FromCollection='waking', PlayWhenSleeping=True, Priority=8, CutAllSoundAndPlay=True)

    # I want to do stuff when just falling asleep and when getting up
    def JustFellAsleep(self):
        return status.Wakefulness < self.MinWakefulnessToBeAwake and status.IAmSleeping == False
    def JustWokeUp(self):
        return status.Wakefulness > self.MinWakefulnessToBeAwake and status.IAmSleeping == True

    # Logic and stuff for going to bed
    def NowItsLate(self):
        return self.AnnounceTiredTime == False and self.LocalTime.tm_hour >= self.SleepHour and self.LocalTime.tm_hour < self.SleepHour + 1 and status.IAmSleeping == False
    def SetTimeToWhine(self):
        self.AnnounceTiredTime = self.RandomMinutesLater(15, 30)
        log.sleep.info('set time to announce we are tired to %s minutes', (self.AnnounceTiredTime - time.time()) / 60)
    def TimeToWhine(self):
        return self.AnnounceTiredTime != False and time.time() >= self.AnnounceTiredTime
    def Whine(self):
        breath.thread.QueueSound(FromCollection='tired', Priority=7)
        self.AnnounceTiredTime = False
    def StartBreathingSleepy(self):
        breath.thread.BreathChange('breathe_sleepy')

    # returns the time that is a random number of minutes in the future, for scheduled events
    def RandomMinutesLater(self, min, max):
        return time.time() + random.randint(min*60, max*60)


# Instantiate and start the thread
thread = Sleep()
thread.daemon = True
thread.start()

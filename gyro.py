import time
import threading
from mpu6050 import mpu6050
import numpy as np

import log
import status
import sleep
import breath

# Poll the Gyro / Accelerometer
class Gyro(threading.Thread):
    name = 'Gyro'

    def __init__ (self):
        threading.Thread.__init__(self)

        # How many single samples are averaged together to smooth the reading
        self.SampleSize = 5

        # Varous lists to store single samples. When they're full the values are averaged
        self.AccelXRecord = [0.0] * self.SampleSize
        self.AccelYRecord = [0.0] * self.SampleSize
        self.GyroXRecord = [0.0] * self.SampleSize
        self.GyroYRecord = [0.0] * self.SampleSize
        self.GyroZRecord = [0.0] * self.SampleSize

        # Smoothed average values
        self.SmoothXTilt = 0.0
        self.SmoothYTilt = 0.0
        self.TotalJostled = 0.0

        # index to keep track of pulling the average every SampleSize times
        self.LoopIndex = 0

        # I think sometimes the touch sensor or other I2C things conflict with the gyro, so I want to shut it down only after a run of i/o errors
        self.IOErrors = 0

        # I want to keep track of the max jostled level, and taper off slowly
        self.JostledLevel = 0.0
        self.JostledAverageWindow = 400.0

    def run(self):
        log.gyro.debug('Thread started.')

        try:
        
            # setup that sensor
            self.sensor = mpu6050(0x68)

        except:

            log.main.error('The gyro had an I/O failure on init. Gyro is unavailable.')
            status.JostledLevel = 0.0
            status.IAmLayingDown = False
            return

        try:

            while True:

                # graceful shutdown
                if status.PleaseShutdown:
                    log.gyro.info('Thread shutting down')
                    break

                # Get data from sensor at full speed. Doesn't seem to need any sleeps. 
                # I'm testing with a sleep now. The sleep seems to be a good idea.
                try:

                    data = self.sensor.get_all_data()
                    self.IOErrors = 0

                except Exception as e:

                    # if gyro fails 10 times in a row, shut it down
                    self.IOErrors += 1
                    log.main.warning(f'I/O failure. ({self.IOErrors}) {e.__class__} {e} {log.format_tb(e.__traceback__)}')

                    if self.IOErrors >= 10:
                        log.main.critical('The gyro thread has been shutdown.')
                        status.JostledLevel = 0.0
                        status.IAmLayingDown = False
                        return

                # Keep track of which iteration we're on. Fill the array with data.
                self.LoopCycle = self.LoopIndex % self.SampleSize

                # For Accel, we're just interested in the tilt of her body. Such as, sitting up, laying down, etc
                self.AccelXRecord[self.LoopCycle] = data[0]['x']
                self.AccelYRecord[self.LoopCycle] = data[0]['y']

                # For Gyro, all I'm interested in is a number to describe how jostled she is, so I abs the data
                self.GyroXRecord[self.LoopCycle] = abs(data[1]['x'])
                self.GyroYRecord[self.LoopCycle] = abs(data[1]['y'])
                self.GyroZRecord[self.LoopCycle] = abs(data[1]['z'])

                # Every SampleSize'th iteration, send the average
                if ( self.LoopCycle == 0 ):

                    # Calculate averages
                    self.SmoothXTilt = sum(self.AccelXRecord) / self.SampleSize
                    self.SmoothYTilt = sum(self.AccelYRecord) / self.SampleSize
                    self.TotalJostled = (sum(self.GyroXRecord) / self.SampleSize) + (sum(self.GyroYRecord) / self.SampleSize) + (sum(self.GyroZRecord) / self.SampleSize)

                    # Standardize jostled level to a number between 0 and 1, and clip. 
                    # As an experiment, I, um, gently beat my wife while apologizing profusely, and found I got it up to 85. Don't beat your wife. 
                    # When she's just sitting there it's always 7
                    # However, after grepping the gyro log, it got down to 3 one time, and 6 lots of times, so this is fine. However, that would just get clipped, so 7 is still a good baseline
                    self.JostledLevel = (self.TotalJostled - 7) / 80
                    self.JostledLevel = float(np.clip(self.JostledLevel, 0.0, 1.0))

                    # If there's a spike, make that the new global status. It'll slowly taper down.
                    if self.JostledLevel > status.JostledLevel:
                        status.JostledLevel = self.JostledLevel

                    # Update the running average
                    # This should be the thing that tapers down
                    status.JostledLevel = (status.JostledLevel * self.JostledAverageWindow) / (self.JostledAverageWindow + 1)

                    # if she gets hit, wake up a bit
                    if self.JostledLevel > 0.15 and status.IAmSleeping == True:
                        log.sleep.info(f'Woke up by being jostled this much: {self.JostledLevel}')
                        sleep.thread.WakeUpABit(0.04)
                        status.LoverProximity = ((status.LoverProximity * 5.0) + 1.0) / 6.0
                        breath.thread.QueueSound(FromCollection='gotwokeup', PlayWhenSleeping=True, IgnoreSpeaking=True, CutAllSoundAndPlay=True)

                    # Update the boolean that tells if we're laying down. While laying down I recorded 4.37, 1.60. However, now it's 1.55, 2.7. wtf happened? The gyro has not moved. Maybe position difference. 
                    # At some point I ought to self-calibrate this. When it's dark, and not jostled for like an hour, that's def laying down, save it. 
                    # This is something I'll need to save in the sqlite db
                    if abs(self.SmoothXTilt - status.SleepXTilt) < 0.2 and abs(self.SmoothYTilt - status.SleepYTilt) < 0.2:
                        status.IAmLayingDown = True
                    else:
                        status.IAmLayingDown = False

                    # self-calibrate the gyro position that is resting in bed
                    # So if she ever sleeps standing that's going to fuck this up
                    if status.LightLevelPct <= 0.1 and status.JostledLevel <= 0.02 and status.IAmSleeping == True:
                        status.SleepXTilt = ((status.SleepXTilt * 100.0) + self.SmoothXTilt) / 101.0
                        status.SleepYTilt = ((status.SleepYTilt * 100.0) + self.SmoothYTilt) / 101.0

                    # log it
                    log.gyro.debug('X: {0:.2f}, Y: {1:.2f}, J: {2:.2f} JPct: {3:.2f} SlX: {4:.2f} SlY: {5:.2f} LD: {6}'.format(self.SmoothXTilt, self.SmoothYTilt, self.TotalJostled, self.JostledLevel, status.SleepXTilt, status.SleepYTilt, status.IAmLayingDown))

                self.LoopIndex += 1
                time.sleep(0.02)

        # log exception in the main.log
        except Exception as e:
            log.main.error('Thread died. {0} {1} {2}'.format(e.__class__, e, log.format_tb(e.__traceback__)))

# Instantiate and start the thread
thread = Gyro()
thread.daemon = True
thread.start()

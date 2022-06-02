import time
import threading
from multiprocessing import Process, Pipe
import numpy as np
import scipy.stats
import RPi.GPIO as GPIO
import board
import busio
import adafruit_mpr121

import log
import status
import sex

# omg lol yeah I just did that. 
# root@christine:~# touch vagina.py

# This handles the capacitive touch sensor that is connected to vagina sensors. 
# there are 3 sloppily installed sensors, hope they last
class Vagina(threading.Thread):
    name = 'Vagina'

    def __init__ (self):
        threading.Thread.__init__(self)


    def run(self):
        log.vagina.debug('Thread started.')

        try:

            # setup the separate process with pipe
            # A class 1 probe is released by the enterprise into a mysterious wall of squishy plastic stuff surrounding the planet
            self.PipeToProbe, self.PipeToEnterprise = Pipe()
            self.ProbeProcess = Process(target = self.Class1Probe, args = (self.PipeToEnterprise,))
            self.ProbeProcess.start()

            while True:

                # graceful shutdown
                if status.PleaseShutdown:
                    log.vagina.info('Thread shutting down')
                    break

                # This will block here until the probe sends a message to the enterprise
                # I think for touch probe, communication will be one way, probe to enterprise

                # The sensors on the probe will send back the result as a string. 
                # Such a primitive signaling technology has not been in active use since the dark ages of the early 21st century! 
                # An embarrassing era in earth's history characterized by the fucking of inanimate objects and mass hysteria. 
                SensorData = self.PipeToProbe.recv()
                log.vagina.debug(f'Sensor Data: {SensorData}')

                # if there was a failure, just die
                if SensorData['msg'] == 'FAIL':
                    # status.TouchedLevel = 0.0
                    return

                # otherwise, pass the message over to the sex thread
                else:
                    sex.thread.VaginaHit(SensorData)

        # log exception in the main.log
        except Exception as e:
            log.main.error('Thread died. {0} {1} {2}'.format(e.__class__, e, log.format_tb(e.__traceback__)))

    # Runs in a separate process for performance reasons
    def Class1Probe(self, PipeToEnterprise):

        try:

            # Initialize this thing. We're using weird numbers, not board
            GPIO.setmode(GPIO.BCM)

            # Send message to the main process
            def honey_touched(msg):
                PipeToEnterprise.send(msg)

            # Keep track of when a sensor is touched, and when it is released so we can report how long.
            # I have found the sensor sends an event both when touched, and again when released.
            # If it's touched, the list contains a time, None otherwise
            # When the touch starts, report that immediately so there's instant feedback
            # When it changes to None, the time will be reported
            # So the touch starting triggers sound right away. The time that comes later should increase arousal.
            SensorTracking = [None] * 12

            # track how many recent I/O errors
            IOErrors = 0

            # The IRQ pin is connected to GPIO 17
            IRQ_Pin = 17

            # So there are three sensors in vagina. The one on the outside will be handled by the quite broken baseline system on the chip, and use the IRQ line. 
            # So this thread should be doing very little in the 98% of time that we're not fucking. When the IRQ gets hit, then we'll be busy grabbing raw data. 
            # Even when in Standby mode, we're going to be maintaining the baselines in case that drifts. 
            # The two proximity sensors on the inside will be manually sampled, I think, due to the broken baseline handling problem. 
            # The outside channel is 2, and that is the one we're going to use
            StandbyMode = True
            ActivationChannel = 2

            # Using this to deactivate after no sensor activity
            Timeout = 60
            DeactivationSeconds = None

            # Stores one frame of touch data
            # might disable this later but right now I want to log it
            TouchData = [0] * 12
            TouchedData = ['   '] * 12

            # Keep track of the baselines
            # if the channel isn't even hooked up, None
            Baselines = [None, None, 0, None, None, None, None, 0, None, 0, None, None]

            # if data point is this amount less than the baseline, it's a touch
            # a touch always results in a lower capacitance number, that's how sensor works
            # therefore, lower = sensitive, higher = the numbness
            Sensitivity = [None, None, 50, None, None, None, None, 14, None, 14, None, None]

            # Number of cycles where no touch before the touch is considered released
            ReleaseCount = [None, None, 3, None, None, None, None, 4, None, 4, None, None]
            ReleaseCounter = [0] * 12

            # how many cycles of continuous touch before we send another message about the D just hanging out
            # she just loves to feel me inside her for a while after sex
            HangingOut = [None, None, 3000, None, None, None, None, 300, None, 300, None, None]
            HangingOutCounter = [0] * 12

            # labels
            ChannelLabels = [None, None, 'Vagina_Clitoris', None, None, None, None, 'Vagina_Shallow', None, 'Vagina_Deep', None, None]

            # How many raw values do we want to accumulate before re-calculating the baselines
            # I started at 500 but it wasn't self-correcting very well
            BaselineDataLength = 100

            # there are 12 channels, and we only have 3 connected to anything
            # accumulate data in an array of numpy arrays, and every once in a while we cum and calc the mode
            UsedChannels = []
            Data = [None] * 12
            for channel in range(0, 12):
                if ChannelLabels[channel] != None:
                    UsedChannels.append(channel)
                    Data[channel] = np.zeros(BaselineDataLength)

            # counter to help accumulate values
            Counter = 0

            # Init the IRQ pin, otherwise it'll float
            GPIO.setup(IRQ_Pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

            # Init I2C bus, for the body touch sensor
            i2c = busio.I2C(board.SCL, board.SDA)

            # Create MPR121 touch sensor object.
            # The sensitivity settings were ugly hacked into /usr/local/lib/python3.6/site-packages/adafruit_mpr121.py
            # (I fixed that sort of. Settings are here now. The driver hacked to make it work.)
            try:
                mpr121 = adafruit_mpr121.MPR121(i2c, touch_sensitivity= [ 12, 12,  50, 12, 12, 12, 12, 50, 12, 50, 12, 12 ], 
                                                     release_sensitivity=[ 6,  6,  4,  6,  6,  6,  6,  6,  6,  6,  6,  6 ],
                                                     debounce=2)
                log.vagina.info('Touch sensor init success')

            except:
                honey_touched({'msg': 'FAIL', 'data': ''})
                log.vagina.error('The touch sensor had an I/O failure on init. Body touch is unavailable.')
                return

            # This function is called when the IRQ line gets hit
            # The only purpose of this is to wake up from standby mode
            def WakeUp(channel):
                nonlocal SensorTracking
                nonlocal IOErrors
                nonlocal StandbyMode
                nonlocal DeactivationSeconds
                # Get... all the cheese
                # It appears there is no performance penalty from getting all the pins vs one pin
                # It looks in the source code like the hardware returns 12 bits all at once

                try:

                    touched = mpr121.touched_pins
                    IOErrors = 0

                except Exception as e:

                    IOErrors += 1
                    log.vagina.warning('The touch sensor had an I/O failure (IRQ). Count = {0} {1} {2}'.format(IOErrors, e.__class__, e, log.format_tb(e.__traceback__)))
                    if IOErrors > 10:
                        log.main.critical('The touch sensor thread has been shutdown.')
                        GPIO.remove_event_detect(IRQ_Pin)
                        honey_touched({'msg': 'FAIL', 'data': ''})
                    return

                # if the vagina got touched, we're active, so stop monitoring the IRQ pin
                if touched[ActivationChannel] == True:
                    GPIO.remove_event_detect(IRQ_Pin)
                    StandbyMode = False
                    DeactivationSeconds = time.time() + Timeout
                    log.vagina.info('The vagina got touched, waking up.')

            # INIT IRQ monitoring
            GPIO.add_event_detect(IRQ_Pin, GPIO.FALLING, callback=WakeUp)

            log.vagina.debug(f'UsedChannels: {UsedChannels}')

            # go into the forever loop
            while True:

                # if we're in standby mode we're just updating long term baselines
                if StandbyMode == True:

                    try:

                        for channel in UsedChannels:
                            Data[channel][Counter % BaselineDataLength] = mpr121.filtered_data(channel)

                        Counter += 1
                        IOErrors = 0

                    except Exception as e:

                        IOErrors += 1
                        log.vagina.warning('The touch sensor had an I/O failure (StandbyMode). Count = {0} {1} {2}'.format(IOErrors, e.__class__, e, log.format_tb(e.__traceback__)))
                        if IOErrors > 10:
                            log.main.critical('The touch sensor thread has been shutdown.')
                            GPIO.remove_event_detect(IRQ_Pin)
                            honey_touched({'msg': 'FAIL', 'data': ''})
                            return

                    # every so often we want to update the baselines
                    if Counter % BaselineDataLength == 0:

                        for channel in UsedChannels:

                            Baselines[channel] = scipy.stats.mode(Data[channel]).mode[0]
                            # log.vagina.debug(f'Data {channel}: {Data[channel]}')

                        log.vagina.debug(f'Updated baselines: {Baselines}')

                    time.sleep(1)

                # if we're not in standby mode, we're ignoring baselines and checking for vag love. Ignore the anus. 
                else:

                    try:

                        for channel in UsedChannels:

                            # get the capacitance
                            TouchData[channel] = mpr121.filtered_data(channel)

                            # Detect touches
                            if Baselines[channel] - TouchData[channel] > Sensitivity[channel]:

                                # detect if this is the start of a touch. We want her to moan if it is.
                                # convert to boolean later, once log visibility isn't needed anymore
                                if TouchedData[channel] != 'XXX':

                                    # pass a message to the main process
                                    honey_touched({'msg': 'touch', 'data': ChannelLabels[channel]})

                                    # easily seen XXX for in-crack debugging
                                    TouchedData[channel] = 'XXX'

                                    # start monitoring for dick left in condition
                                    HangingOutCounter[channel] = 0

                                else:

                                    # hanging out in there a bit long, eh? 
                                    if HangingOutCounter[channel] % HangingOut[channel] == 0:
                                        honey_touched({'msg': 'hangout', 'data': ChannelLabels[channel]})

                                # reset the release counter
                                ReleaseCounter[channel] = ReleaseCount[channel]

                                # set the seconds where if time is after this, the vagina will time out
                                DeactivationSeconds = time.time() + Timeout

                                # increment the dick left in counter
                                HangingOutCounter[channel] += 1

                            else:

                                # decrement counter
                                ReleaseCounter[channel] -= 1

                                # if we're at 0 it means there was a touch and we just reached the release threshold
                                if ReleaseCounter[channel] == 0:

                                    # pass a message to the main process
                                    honey_touched({'msg': 'release', 'data': ChannelLabels[channel]})

                                    # set the channel to released
                                    TouchedData[channel] = '   '


                        log.vagina.debug(f'{TouchData} {TouchedData} {ReleaseCounter}')
                        IOErrors = 0

                    except Exception as e:

                        IOErrors += 1
                        log.vagina.warning('The touch sensor had an I/O failure (ActiveMode). Count = {0} {1} {2}'.format(IOErrors, e.__class__, e, log.format_tb(e.__traceback__)))
                        if IOErrors > 10:
                            log.main.critical('The touch sensor thread has been shutdown.')
                            GPIO.remove_event_detect(IRQ_Pin)
                            honey_touched({'msg': 'FAIL', 'data': ''})
                            return

                    # check for timeout. 
                    # So if no vag hits for a long time, stop, and start monitoring the IRQ again. 
                    if time.time() > DeactivationSeconds:
                        StandbyMode = True
                        GPIO.add_event_detect(IRQ_Pin, GPIO.FALLING, callback=WakeUp)
                        log.vagina.info('The vagina timed out, entering standby mode.')

                    # just screw around for a bit
                    time.sleep(0.1)


        # log exception in the main.log
        except Exception as e:
            log.main.error('We have lost contact with the probe. {0} {1} {2}'.format(e.__class__, e, log.format_tb(e.__traceback__)))

# Instantiate and start the thread
thread = Vagina()
thread.daemon = True
thread.start()

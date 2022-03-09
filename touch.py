import time
import threading
import random
import numpy as np

import log
import status
import sleep

# When Christine gets touched, stuff should happen. That happens here. 
class Touch(threading.Thread):
    name = 'Touch'

    def __init__ (self):
        threading.Thread.__init__(self)

    def run(self):
        log.touch.debug('Thread started.')

        try:

            # setup the separate process with pipe
            # A class 1 probe is released by the enterprise into a mysterious wall of squishy plastic stuff surrounding the planet

            # this requires a vaginal sensor, temp disable
            # self.PipeToProbe, self.PipeToEnterprise = Pipe()
            # self.ProbeProcess = Process(target = self.Class1Probe, args = (self.PipeToEnterprise,))
            # self.ProbeProcess.start()

            while True:

                time.sleep(60)

                # This will block here until the probe sends a message to the enterprise
                # I think for touch probe, communication will be one way, probe to enterprise

                # The sensors on the probe will send back the result as a string. 
                # Such a primitive signaling technology has not been in active use since the dark ages of the early 21st century! 
                # An embarrassing era in earth's history characterized by the fucking of inanimate objects and mass hysteria. 

                # this requires a vaginal sensor, temp disable
                # SensorData = self.PipeToProbe.recv()
                # touchlog.debug(f'Sensor Data: {SensorData}')
                # if type(SensorData) is list:
                #     Thread_Sexual_Activity.VaginaPulledOut(SensorData)

                # # Disabling this whole area because that touch sensor is just glitching right now
                # elif SensorData == 'LeftCheek':
                #     GlobalStatus.TouchedLevel += 0.05
                #     GlobalStatus.ChanceToSpeak += 0.05

                #     # Can't go past 0 or past 1
                #     GlobalStatus.ChanceToSpeak = float(np.clip(GlobalStatus.ChanceToSpeak, 0.0, 1.0))
                #     GlobalStatus.TouchedLevel = float(np.clip(GlobalStatus.TouchedLevel, 0.0, 1.0))
                # elif SensorData == 'RightCheek':
                #     GlobalStatus.TouchedLevel += 0.05
                #     GlobalStatus.ChanceToSpeak += 0.05

                #     # Can't go past 0 or past 1
                #     GlobalStatus.ChanceToSpeak = float(np.clip(GlobalStatus.ChanceToSpeak, 0.0, 1.0))
                #     GlobalStatus.TouchedLevel = float(np.clip(GlobalStatus.TouchedLevel, 0.0, 1.0))
                # elif SensorData == 'OMGKisses':
                #     GlobalStatus.DontSpeakUntil = time.time() + 2.0 + (random.random() * 3)
                #     soundlog.info('GotKissedSoundStop')
                #     Thread_Breath.QueueSound(FromCollection='kissing', IgnoreSpeaking=True, CutAllSoundAndPlay=True, Priority=6)
                #     GlobalStatus.TouchedLevel += 0.1
                #     GlobalStatus.ChanceToSpeak += 0.1

                #     # Can't go past 0 or past 1
                #     GlobalStatus.ChanceToSpeak = float(np.clip(GlobalStatus.ChanceToSpeak, 0.0, 1.0))
                #     GlobalStatus.TouchedLevel = float(np.clip(GlobalStatus.TouchedLevel, 0.0, 1.0))

                # disabled until we get a vaginal sensor in this new body
                # elif 'Vagina_' in SensorData:
                #     Thread_Sexual_Activity.VaginaHit(SensorData)

                # this requires a vaginal sensor, temp disable
                # elif SensorData == 'FAIL':
                #     GlobalStatus.TouchedLevel = 0.0
                #     return

        log exception in the main.log
        except Exception as e:
            log.main.error('Thread died. {0} {1} {2}'.format(e.__class__, e, log.format_tb(e.__traceback__)))

    # I'm putting this block in the museum until we get a vaginal sensor installed, temp disable

# instantiate and start thread
thread = Touch()
thread.start()
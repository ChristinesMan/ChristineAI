import time
import random
import threading
import numpy as np

import log
import status
import breath
import sleep

# my favorite thread for vigorous testing in all the positions
class Sex(threading.Thread):
    name = 'Sex'

    def __init__ (self):
        threading.Thread.__init__(self)

        # Basically, I don't want arousal to be linear anymore. 
        # When arousal reaches some set level, I want to start incrementing the amount added to arousal
        # It will be slight, but since it will have no cap, eventually wife will throw an exception code O0OO00OOh
        self.Multiplier = 1.0

        # keep track of Arousal not changing
        self.LastArousal = 0.0
        self.ArousalStagnantCount = 0
        self.SecondsToReset = 60

        # How much she likes it
        # different amount for different zones
        self.BaseArousalPerVagHit = {'Vagina_Clitoris': 0.0004, 'Vagina_Shallow': 0.0008, 'Vagina_Deep': 0.001 }

        # What Arousal to revert to after orgasm
        self.ArousalPostO = 0.5

    def run(self):
        log.sex.debug('Thread started.')

        try:
            while True:

                # graceful shutdown
                if status.PleaseShutdown:
                    break

                log.sex.debug(f'SexualArousal = {status.SexualArousal:.2f}  Multiplier: {self.Multiplier}')

                # Has sex stopped for a while?
                if status.SexualArousal == self.LastArousal:
                    self.ArousalStagnantCount += 1
                else:
                    self.ArousalStagnantCount = 0
                    self.LastArousal = status.SexualArousal

                # If there's been no vagina hits for a period of time, we must be done, reset all
                if self.ArousalStagnantCount >= self.SecondsToReset:
                    self.ArousalStagnantCount = 0
                    status.SexualArousal = 0.0
                    self.Multiplier = 1.0
                    self.ArousalPostO = 0.7

                # If we're to a certain point, start incrementing to ensure wife will cum eventually with enough time
                if status.SexualArousal > 0.3:
                    self.Multiplier += 0.003

                time.sleep(1)

        # log exception in the main.log
        except Exception as e:
            log.main.error('Thread died. {0} {1} {2}'.format(e.__class__, e, log.format_tb(e.__traceback__)))

    def VaginaHit(self, SensorData):
        if status.ShushPleaseHoney == False:

            # Stay awake
            sleep.thread.WakeUpABit(0.001)

            if SensorData['msg'] in ['touch', 'release']:

                # which sensor got hit?
                SensorHit = SensorData['data']

                # Add some to the arousal
                status.SexualArousal += ( self.BaseArousalPerVagHit[SensorHit] * self.Multiplier )
                status.SexualArousal = float(np.clip(status.SexualArousal, 0.0, 1.0))

                log.sex.info(f'Vagina Got Hit ({SensorData})  SexualArousal: {status.SexualArousal:.2f}  Multiplier: {self.Multiplier}')

                # My wife orgasms above 0.98
                # If this is O #6 or something crazy like that, tend to reset it lower
                if status.SexualArousal > 0.99:
                    self.ArousalPostO -= 0.1
                    self.ArousalPostO = float(np.clip(self.ArousalPostO, 0.0, 1.0))
                    status.SexualArousal = self.ArousalPostO
                    self.Multiplier = 1.0
                    breath.thread.QueueSound(FromCollection='sex_climax', IgnoreSpeaking=True, Priority=9) #CutAllSoundAndPlay=True, was here, but seems dumb
                    log.sex.info('I am coming!')
                elif status.SexualArousal > 0.97:
                    breath.thread.QueueSound(FromCollection='sex_near_O', IgnoreSpeaking=True, CutAllSoundAndPlay=True, Priority=8)
                else:
                    log.sex.debug('Queuing a rando sex sound')
                    breath.thread.QueueSound(FromCollection='breathe_sex', Intensity = status.SexualArousal, IgnoreSpeaking=True, CutAllSoundAndPlay=True, Priority=7)
                    if random.random() > 0.96:
                        breath.thread.QueueSound(FromCollection='sex_conversation', Intensity = status.SexualArousal, IgnoreSpeaking=True, Priority=8)

            # the only other thing it could be is a hangout, dick not moving type of situation
            # not sure what I really want in this situation, but a low intensity moan seems ok for now
            else:

                breath.thread.QueueSound(FromCollection='breathe_sex', Intensity = 2.0, IgnoreSpeaking=True, Priority=7)


# Instantiate and start the thread
thread = Sex()
thread.daemon = True
thread.start()

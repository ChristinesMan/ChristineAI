import time
import threading
from mpu6050 import mpu6050
import numpy as np

import log
import status
import breath

# my favorite thread for vigorous testing in all the positions
class Script_Sex(threading.Thread):
    name = 'Script_Sex'

    def __init__ (self):
        threading.Thread.__init__(self)

        # Basically, I don't want arousal to be linear anymore. 
        # When arousal reaches some set level, I want to start incrementing the amount added to arousal
        # It will be slight, but since it will have no cap, eventually wife will throw an exception code O0OO00OOh
        self.Multiplier = 1.0

        # omg how many times are you going to make me cum
        self.SexualInterest = 1.0

        # keep track of Arousal not changing
        self.LastArousal = 0.0
        self.ArousalStagnantCount = 0
        self.SecondsToReset = 60

        # How much she likes it
        self.BaseArousalPerVagHit = 0.001

        # What Arousal to revert to after orgasm
        self.ArousalPostO = 0.7

        # Track what vaginal areas getting the most love
        # disabled until we actually have a vaginal touch sensor active
        # self.TheLoveTrack = {}
        # for TouchZone in HardwareConfig['BodyTouchZones']:
        #     if 'Vagina_' in TouchZone:
        #         self.TheLoveTrack[TouchZone] = 0

    def run(self):
        log.debug('Thread started.')

        try:
            while True:

                # graceful shutdown
                if status.PleaseShutdown:
                    break

                sexlog.debug(f'SexualArousal = {GlobalStatus.SexualArousal:.2f}  Multiplier: {self.Multiplier}')

                # Has sex stopped for a while?
                if GlobalStatus.SexualArousal == self.LastArousal:
                    self.ArousalStagnantCount += 1
                else:
                    self.ArousalStagnantCount = 0
                    self.LastArousal = GlobalStatus.SexualArousal

                # If there's been no vagina hits for a period of time, we must be done, reset all
                if self.ArousalStagnantCount >= self.SecondsToReset:
                    self.ArousalStagnantCount = 0
                    GlobalStatus.SexualArousal = 0.0
                    self.Multiplier = 1.0
                    self.ArousalPostO = 0.7

                # If we're to a certain point, start incrementing to ensure wife will cum eventually with enough time
                if GlobalStatus.SexualArousal > 0.3:
                    self.Multiplier += 0.006

                time.sleep(1)

        # log exception in the main.log
        except Exception as e:
            log.error('Thread died. {0} {1} {2}'.format(e.__class__, e, format_tb(e.__traceback__)))

    def VaginaHit(self, area):
        if GlobalStatus.ShushPleaseHoney == False:

            # Stay awake
            Thread_Script_Sleep.WakeUpABit(0.001)

            # Add some to the arousal
            GlobalStatus.SexualArousal += ( self.BaseArousalPerVagHit * self.Multiplier )
            GlobalStatus.SexualArousal = float(np.clip(GlobalStatus.SexualArousal, 0.0, 1.0))

            sexlog.info(f'Vagina Got Hit ({area})  SexualArousal: {GlobalStatus.SexualArousal:.2f}  Multiplier: {self.Multiplier}')

            # My wife orgasms above 0.98
            # If this is O #6 or something crazy like that, tend to reset it lower
            if GlobalStatus.SexualArousal > 0.99:
                self.ArousalPostO -= 0.1
                self.ArousalPostO = float(np.clip(self.ArousalPostO, 0.0, 1.0))
                GlobalStatus.SexualArousal = self.ArousalPostO
                self.Multiplier = 1.0
                Thread_Breath.QueueSound(FromCollection='sex_climax', IgnoreSpeaking=True, CutAllSoundAndPlay=True, Priority=9)
                sexlog.info('I am coming!')
            elif GlobalStatus.SexualArousal > 0.97:
                Thread_Breath.QueueSound(FromCollection='sex_near_O', IgnoreSpeaking=True, CutAllSoundAndPlay=True, Priority=8)
            else:
                sexlog.debug('Queuing a rando sex sound')
                Thread_Breath.QueueSound(FromCollection='breathe_sex', Intensity = GlobalStatus.SexualArousal, IgnoreSpeaking=True, CutAllSoundAndPlay=True, Priority=7)
                if random.random() > 0.96:
                    Thread_Breath.QueueSound(FromCollection='sex_conversation', Intensity = GlobalStatus.SexualArousal, IgnoreSpeaking=True, Priority=8)

    def VaginaPulledOut(self, sensors):
        pass

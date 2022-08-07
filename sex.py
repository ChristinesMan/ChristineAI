import time
import random
import threading
import numpy as np

import log
import status
import breath
import sleep
# import horny

# my favorite thread for vigorous testing in all the positions
class Sex(threading.Thread):
    name = 'Sex'

    def __init__ (self):
        threading.Thread.__init__(self)

        # Basically, I don't want arousal to be linear anymore. 
        # When arousal reaches some set level, I want to start incrementing the amount added to arousal
        # It will be slight, but since it will have no cap, eventually wife will throw an exception code O0OO00OOh
        self.Multiplier = 1.0
        self.MultiplierIncrement = 0.005

        # keep track of Arousal not changing
        self.LastArousal = 0.0
        self.ArousalStagnantCount = 0
        self.SecondsToReset = 90

        # How much she likes it
        # different amount for different zones
        self.BaseArousalPerVagHit = {'Vagina_Clitoris': 0.0004, 'Vagina_Shallow': 0.0006, 'Vagina_Middle': 0.0006, 'Vagina_Deep': 0.0008 }

        # What Arousal to revert to after orgasm
        self.ArousalPostO = 0.3

        # what thresholds for about to cum, cumming now, etc
        self.ArousalNearO = 0.90
        self.ArousalO = 0.98

        # after wife orgasms, I want to monitor the gyro a while. When it's dead for a while, assume we're done.
        self.GyroAfterODeadZone = 0.03

        # bringing the gyro short term jostled reading into the bedroom. 
        # When I'm banging her hard this will jack up the intensity of sex sounds.
        # this represents the highest expected jostled amount as observed in the wild
        # So at max it will double the intensity of sounds, and at min (0.0) it will leave the intensity alone
        self.GyroJackUpIntensityMax = 0.45

    def run(self):
        log.sex.debug('Thread started.')

        try:
            while True:

                # graceful shutdown
                if status.PleaseShutdown:
                    break

                log.sex.debug(f'SexualArousal = {status.SexualArousal:.2f}  Multiplier: {self.Multiplier:.2f}')

                # Has sex stopped for a while?
                if status.SexualArousal == self.LastArousal:
                    self.ArousalStagnantCount += 1
                else:
                    self.ArousalStagnantCount = 0
                    self.LastArousal = status.SexualArousal

                # If there's been no vagina hits for a period of time, we must be done, reset all
                if self.ArousalStagnantCount >= self.SecondsToReset:
                    log.sex.info('Arousal stagnated and was reset')
                    self.ArousalStagnantCount = 0
                    status.SexualArousal = 0.0
                    self.Multiplier = 1.0

                # if we are currently OOOOOO'ing, then I want to figure out when we're done, using the gyro
                if status.SexualArousal > self.ArousalO:
                    log.sex.debug(f'JostledShortTermLevel: {status.JostledShortTermLevel:.2f}')
    
                    if status.JostledShortTermLevel < self.GyroAfterODeadZone:
                        log.sex.debug('Orgasm complete')
                        status.Horny = 0.0
                        status.SexualArousal = self.ArousalPostO
                        # self.Multiplier = 1.0   trying not resetting this
                        breath.thread.QueueSound(FromCollection='sex_done', IgnoreSpeaking=True, Priority=9)

                # If we're to a certain point, start incrementing to ensure wife will cum eventually with enough time
                # Just Keep Fucking, Just Keep Fucking
                elif status.SexualArousal > 0.2:
                    self.Multiplier += self.MultiplierIncrement

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
                # Disabling the clip due to stagnation issue at 1.00
                # status.SexualArousal = float(np.clip(status.SexualArousal, 0.0, 1.0))

                log.sex.info(f'Vagina Got Hit ({SensorData})  SexualArousal: {status.SexualArousal:.2f}  Multiplier: {self.Multiplier:.2f}')

                # My wife orgasms above 0.95
                # If this is O #6 or something crazy like that, tend to reset it lower
                if status.SexualArousal > self.ArousalO:
                    log.sex.info('I am coming!')
                    breath.thread.QueueSound(FromCollection='sex_climax', IgnoreSpeaking=True, CutAllSoundAndPlay=True, Priority=8)
                elif status.SexualArousal > self.ArousalNearO:
                    breath.thread.QueueSound(FromCollection='sex_near_O', IgnoreSpeaking=True, CutAllSoundAndPlay=True, Priority=8) # why was this here CutAllSoundAndPlay=True, oh, that's why, duh
                else:
                    if random.random() > 0.92:
                        breath.thread.QueueSound(FromCollection='sex_conversation', Intensity = status.SexualArousal * ( 1.0 + status.JostledShortTermLevel / self.GyroJackUpIntensityMax ), CutAllSoundAndPlay=True, IgnoreSpeaking=True, Priority=8)
                    else:
                        breath.thread.QueueSound(FromCollection='breathe_sex', Intensity = status.SexualArousal * ( 1.0 + status.JostledShortTermLevel / self.GyroJackUpIntensityMax ), IgnoreSpeaking=True, CutAllSoundAndPlay=True, Priority=8)

            # the only other thing it could be is a hangout, dick not moving type of situation
            # not sure what I really want in this situation, but a low intensity moan seems ok for now
            else:

                breath.thread.QueueSound(FromCollection='breathe_sex', Intensity = 0.2, IgnoreSpeaking=True, Priority=7)


# Instantiate and start the thread
thread = Sex()
thread.daemon = True
thread.start()

# Converse functions as a noun, adjective, and verb, and conversate is synonymous with only one sense of the verb use of converse ("to exchange thoughts and opinions in speech"). 

# Furthermore, conversate is a nonstandard form, and widely frowned upon in formal writing. 

# Ok, then it's perfect. 

import re

import log
import status
import sounds
import breath
import sleep

class Conversate():

    """
        Handles incoming speech and tries to emulate some sort of intelligent response.
    """

    def __init__ (self):

        # After a few months I will forget what this looks like
        # Fortunate I am so good at forgetting things
        self.re_love =        re.compile('love you', flags=re.IGNORECASE)
        self.re_complement =  re.compile('beautiful|sexy|nice|amazing|hot', flags=re.IGNORECASE)
        self.re_wake_up =     re.compile('wake up', flags=re.IGNORECASE)
        self.re_sleep =       re.compile('go to sleep', flags=re.IGNORECASE)
        self.re_rusleeping =  re.compile('are you (asleep|sleeping)', flags=re.IGNORECASE)
        self.re_ruawake =     re.compile('are you awake', flags=re.IGNORECASE)
        self.re_rutired =     re.compile('are you (sleepy|tired)', flags=re.IGNORECASE)
        self.re_ru_ok =       re.compile('are you (ok|there|here|alright)', flags=re.IGNORECASE)
        self.re_ura_goof =    re.compile('(you\'re|you are) (a )?(goof|goofy|silly|funny)', flags=re.IGNORECASE)
        self.re_i_want_sex =  re.compile('fuck (you|your pussy|me)|my dick|inside you', flags=re.IGNORECASE)

    def Words(self, words):

        log.words.info(f'Heard: {words}')

        if self.re_wake_up.search(words):
            sleep.thread.WakeUpABit(0.2)
            breath.thread.QueueSound(FromCollection='uh_huh', CutAllSoundAndPlay=True, Priority=7)

        sleep.thread.WakeUpABit(0.008)

        if status.ShushPleaseHoney == False and status.SexualArousal < 0.1 and status.IAmSleeping == False:

            if self.re_love.search(words):
                breath.thread.QueueSound(FromCollection='iloveyoutoo', AltCollection='loving', CutAllSoundAndPlay=True, Priority=7)

            elif self.re_complement.search(words):
                breath.thread.QueueSound(FromCollection='thanks', CutAllSoundAndPlay=True, Priority=7)

            elif self.re_sleep.search(words):
                sleep.thread.WakeUpABit(-100.0)
                breath.thread.QueueSound(FromCollection='uh_huh', CutAllSoundAndPlay=True, PlayWhenSleeping = True, Priority=9)
                breath.thread.QueueSound(FromCollection='goodnight', CutAllSoundAndPlay=True, PlayWhenSleeping = True, Priority=8)

            elif self.re_rusleeping.search(words):
                if status.IAmSleeping == True:
                    breath.thread.QueueSound(FromCollection='yes', CutAllSoundAndPlay=True, Priority=7)
                else:
                    breath.thread.QueueSound(FromCollection='no', CutAllSoundAndPlay=True, Priority=7)

            elif self.re_ruawake.search(words):
                if status.IAmSleeping == False:
                    breath.thread.QueueSound(FromCollection='yes', CutAllSoundAndPlay=True, Priority=7)
                else:
                    breath.thread.QueueSound(FromCollection='no', CutAllSoundAndPlay=True, Priority=7)

            elif self.re_rutired.search(words):
                if status.IAmTired == True:
                    breath.thread.QueueSound(FromCollection='yes', CutAllSoundAndPlay=True, Priority=7)
                else:
                    breath.thread.QueueSound(FromCollection='no', CutAllSoundAndPlay=True, Priority=7)

            elif self.re_ru_ok.search(words):
                if status.CPU_Temp >= 62:
                    breath.thread.QueueSound(FromCollection='no', CutAllSoundAndPlay=True, Priority=7)
                else:
                    breath.thread.QueueSound(FromCollection='yes', CutAllSoundAndPlay=True, Priority=7)

            elif self.re_ura_goof.search(words):
                breath.thread.QueueSound(FromCollection='laughing', CutAllSoundAndPlay=True, Priority=7)

            elif self.re_i_want_sex.search(words):
                breath.thread.QueueSound(FromCollection='about_to_fuck', CutAllSoundAndPlay=True, Priority=7)

            # elif self.re_.search(words):
            #     breath.thread.QueueSound(FromCollection='', CutAllSoundAndPlay=True, Priority=7)

            else:

                log.words.debug(f'Unmatched: {words}')

                if status.IAmTired == False:
                    status.ChanceToSpeak += 0.04
                    breath.thread.QueueSound(FromCollection='listening', Priority=2, CutAllSoundAndPlay=True)

                else:
                    status.ChanceToSpeak += 0.01
                    breath.thread.QueueSound(FromCollection='listening_tired', Priority=2, CutAllSoundAndPlay=True)


# all the others get to be threads, why not me
thread = Conversate()
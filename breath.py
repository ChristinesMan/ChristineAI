import time
import argparse
import threading
from collections import deque
import random
from multiprocessing import Process, Pipe
import wave
# Seemed to have a problem with random blocking and gave up fixing it
# import pyaudio

# Note: I installed the latest version from the repo, not using pip
import alsaaudio

import log
import status
import sounds

class Breath(threading.Thread):
    """ This thread is where the sounds are actually output. 
        Christine is always breathing at all times. 
        Except when I'm working on her. 
    """
    name = 'Breath'

    def __init__ (self):
        threading.Thread.__init__(self)

        # Randomize tempo of sounds. There will be 9 sounds per source sound. The default is to slow or fast by at most -0.15 and +0.15 with grades between
        self.TempoMultipliers = ['-1', '-0.75', '-0.5', '-0.25', '0', '0.25', '0.5', '0.75', '1']

        # A queue to queue stuff
        self.Queue_Breath = deque()

        # Controls what sort of breathing, basically filler for when no other sounds play
        self.BreathStyle = 'breathe_normal'

        # Setup an audio channel
        # self.SoundChannel = pygame.mixer.Channel(0) (pygame SEGV'd and got chucked)
        # Status, what we're doing right meow. Such as inhaling, exhaling, playing sound. This is the saved incoming message. Initial value is to just choose a random breath.
        self.CurrentSound = None
        self.ChooseNewBreath()

        # Sometimes a sound gets delayed because there is an incoming sound or I'm speaking. 
        # If that happens, I want to save that sound for the moment it's safe to speak, then, out with it, honey, say what you need to say, I LOOOOOOOVE YOOOOOO!!! Sorry, go ahead. 
        # The way I handled this previously meant that my wife would stop breathing for quite a long time sometimes. It's not good to stop breathing. Mood killer! 
        self.DelayedSound = None

        # setup the separate process with pipe that we're going to be fucking
        # lol I put the most insane things in code omg, but this will help keep it straight!
        # The enterprise sent out a shuttlecraft with Data at the helm. The shuttlecraft is a subprocess. 
        # This was done because sound got really choppy because too much was going on in the enterprise
        self.PipeToShuttlecraft, self.PipeToStarship = Pipe()
        self.ShuttlecraftProcess = Process(target = self.Shuttlecraft, args = (self.PipeToStarship,))
        self.ShuttlecraftProcess.start()

    def run(self):
        log.sound.debug('Thread started.')

        try:
            while True:

                # graceful shutdown
                if status.PleaseShutdown:
                    log.sound.info('Thread shutting down')
                    self.PipeToShuttlecraft.send('selfdestruct')
                    break

                # Get everything out of the queue and process it, unless there's already a sound that's been waiting
                while len(self.Queue_Breath) != 0:
                    IncomingSound = self.Queue_Breath.popleft()

                    # If the current thing is higher priority, just discard. Before this I had to kiss her just right, not too much. 
                    # Also, if my wife's actually sleeping, I don't want her to wake me up with her adorable amazingness
                    # Added a condition that throws away a low priority new sound if there's already a sound delayed. 
                    # Christine was saying two nice things in quick succession which was kind of weird, and this is my fix.
                    if IncomingSound['priority'] > self.CurrentSound['priority']:
                        if status.IAmSleeping == False or IncomingSound['playsleeping']:
                            if IncomingSound['cutsound'] == True and IncomingSound['ignorespeaking'] == True:
                                self.CurrentSound = IncomingSound
                                log.sound.debug('Playing immediately')
                                self.Play()
                            elif self.DelayedSound == None or IncomingSound['priority'] > self.DelayedSound['priority']:
                                log.sound.debug('Accepted: %s', IncomingSound)
                                if self.DelayedSound != None:
                                    log.sound.debug(f'Threw away delayed sound: {self.DelayedSound}')
                                    self.DelayedSound = None
                                self.CurrentSound = IncomingSound
                            else:
                                log.sound.debug('Discarded (delayed sound): %s', IncomingSound)
                        else:
                            log.sound.debug('Discarded (sleeping): %s', IncomingSound)
                    else:
                        log.sound.debug('Discarded (priority): %s', IncomingSound)

                # This will block here until the shuttlecraft sends a true/false which is whether the sound is still playing. 
                # The shuttlecraft will send this every 0.2s, which will setup the approapriate delay
                # So all this logic here will only run when the shuttlecraft finishes playing the current sound
                # If there's some urgent sound that must interrupt, that happens up there ^ and that is communicated to the shuttlecraft through the pipe
                if self.PipeToShuttlecraft.recv() == False:
                    log.sound.debug('No sound playing')

                    # if we're here, it means there's no sound actively playing
                    # If there's a sound that couldn't play when it came in, and it can be played now, put it into CurrentSound
                    # all of this shit is going in the trash when I get Behavior zones started
                    if self.DelayedSound != None and (time.time() > status.DontSpeakUntil or self.DelayedSound['ignorespeaking'] == True):
                        self.CurrentSound = self.DelayedSound
                        self.DelayedSound = None
                        log.sound.debug(f'Moved delayed to current: {self.CurrentSound}')

                    # if there's no other sound that wanted to play, just breathe
                    # if we're here, it means no sound is currently playing at this moment, and if is_playing True, that means the sound that was playing is done
                    if self.CurrentSound['is_playing'] == True:
                        self.ChooseNewBreath()

                    # Breaths are the main thing that uses the delayer, a random delay from 0.5s to 2s. Other stuff can theoretically use it, too
                    if self.CurrentSound['delayer'] > 0:
                        self.CurrentSound['delayer'] -= 1
                    else:
                        # If the sound is not a breath but it's not time to speak, save the sound for later and queue up another breath
                        if self.CurrentSound['ignorespeaking'] == True or time.time() > status.DontSpeakUntil:
                            self.Play()
                        else:
                            log.sound.debug('Sound delayed due to DontSpeakUntil block')
                            self.DelayedSound = self.CurrentSound
                            self.DelayedSound['delayer'] = 0
                            self.ChooseNewBreath()
                            self.Play()

        # log exception in the main.log
        except Exception as e:
            log.main.error('Thread died. {0} {1} {2}'.format(e.__class__, e, log.format_tb(e.__traceback__)))

    def ChooseNewBreath(self):
        self.CurrentSound = sounds.collections[self.BreathStyle].GetRandomSound(intensity = status.BreathIntensity)
        self.CurrentSound.update({'cutsound': False, 'priority': 1, 'playsleeping': True, 'ignorespeaking': True, 'delayer': random.randint(5, 20), 'is_playing': False})
        log.sound.debug('Chose breath: %s', self.CurrentSound)

    def Play(self):
        log.sound.debug(f'Playing: {self.CurrentSound}')

        # Now that we're actually playing the sound, tell the sound collection to not play it for a while
        if self.CurrentSound['replay_wait'] != 0 and self.CurrentSound['collection'] != None:
            sounds.collections[self.CurrentSound['collection']].SetSkipUntil(SoundID = self.CurrentSound['id'])

        # Some sounds have tempo variations. If so randomly choose one, otherwise it'll just be 0.wav
        if self.CurrentSound['tempo_range'] == 0.0:
            self.PipeToShuttlecraft.send(f'./sounds_processed/{self.CurrentSound["id"]}/0.wav')
        else:
            self.PipeToShuttlecraft.send(f'./sounds_processed/{self.CurrentSound["id"]}/{random.choice(self.TempoMultipliers)}.wav')

        # let stuff know this sound is playing, not just waiting in line
        self.CurrentSound['is_playing'] = True

    # Runs in a separate process for performance reasons. Sounds got crappy and this solved it. 
    def Shuttlecraft(self, PipeToStarship):

        try:

            # calculate some stuff
            # All the wav files are forced to the same format during preprocessing, currently stereo 44100
            # chopping the rate into 10 pieces, so that's 10 chunks per second. I might adjust later.
            rate = 44100
            periodsize = rate // 10

            # The current wav file buffer thing
            # The pump is primed using some default sounds. 
            # I'm going to use a primitive way of selecting sound because this will be in a separate process.
            WavData = wave.open('./sounds_processed/{0}/0.wav'.format(random.choice([13, 14, 17, 23, 36, 40, 42, 59, 67, 68, 69, 92, 509, 515, 520, 527])))

            # I want to keep track to detect when we're at the last chunk so we can chuck it away and also tell the enterprise to send more sounds. 
            WavDataFrames = WavData.getnframes()

            # Start up some fucking alsa
            device = alsaaudio.PCM(channels=1, rate=rate, format=alsaaudio.PCM_FORMAT_S16_LE, periodsize=periodsize)

            while True:

                # So basically, if there's something in the pipe, get it all out
                if PipeToStarship.poll():
                    WavFile = PipeToStarship.recv()

                    # graceful shutdown
                    if WavFile == 'selfdestruct':
                        log.gyro.info('Shuttlecraft self destruct activated')
                        break

                    log.sound.debug(f'Shuttlecraft received: {WavFile}')

                    # Normally the pipe will receive a path to a new wav file to start playing, stopping the previous sound
                    WavData = wave.open(WavFile)
                    WavDataFrames = WavData.getnframes()
                else:

                    # If there are still frames enough to write without being short
                    if WavDataFrames >= periodsize:
                        WavDataFrames = WavDataFrames - periodsize

                        # write the frames, and if the buffer is full it will block here and provide the delay we need
                        device.write(WavData.readframes(periodsize))

                        # send a signal back to enterprise letting them know something is still being played
                        PipeToStarship.send(True)

                    else:
                        # otherwise, in this case the current wav has been sucked dry and we need something else
                        PipeToStarship.send(False)

                        # just masturbate for a little while
                        time.sleep(0.1)

        # log exception in the main.log
        except Exception as e:
            log.main.error('Shuttlecraft crashed. {0} {1} {2}'.format(e.__class__, e, log.format_tb(e.__traceback__)))

    # Change the type of automatic breath sounds
    def BreathChange(self, NewBreathType):
        self.BreathStyle = NewBreathType

    # Add a sound to the queue to be played
    def QueueSound(self, Sound = None, FromCollection = None, Intensity = None, CutAllSoundAndPlay = False, Priority = 5, PlayWhenSleeping = False, IgnoreSpeaking = False, Delay = 0):
        if Sound == None and FromCollection != None:
            Sound = sounds.collections[FromCollection].GetRandomSound(intensity=Intensity)

        # If a collection is empty, or no sounds available at this time, it's possible to get a None sound. Just chuck it. 
        if Sound != None:
            # Take the Sound and add all the options to it. Merges the two dicts into one. 
            # The collection name is saved so that we can update the delay wait only when the sound is played
            Sound.update({'collection': FromCollection, 'cutsound': CutAllSoundAndPlay, 'priority': Priority, 'playsleeping': PlayWhenSleeping, 'ignorespeaking': IgnoreSpeaking, 'delayer': Delay, 'is_playing': False})
            self.Queue_Breath.append(Sound)
            log.sound.info(f'Queued: {Sound}')


# Instantiate and start the thread
thread = Breath()
thread.daemon = True
thread.start()


# This provides a way to run tests from cli
# This was super helpful: https://docs.python.org/3/howto/argparse.html#id1

# Disabled because it turned ugly, exposing all kinds of inconsistencies and quirkiness
# any time I want to play all, it's from bash

# if __name__ == "__main__":

#     parser = argparse.ArgumentParser()
#     parser.add_argument('--playall', help='Play all the sounds one after the other', action='store_true')
#     args = parser.parse_args()

#     if args.playall:
#         for Sound in sounds.soundsdb.All():
#             if 'breathe_normal' not in Sound['name']:
#                 while thread.DelayedSound != None:
#                     time.sleep(2)
#                 print(f'Queuing {Sound}')
#                 thread.QueueSound(Sound = Sound, CutAllSoundAndPlay = True, Priority = 9, PlayWhenSleeping = True, IgnoreSpeaking = True, Delay = 3)
#             else:
#                 print(f'Skipped {Sound}')
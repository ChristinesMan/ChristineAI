import time
from ast import literal_eval
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
                    self.PipeToShuttlecraft.send({'wavfile': 'selfdestruct', 'vol': 0})
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
                    # log.sound.debug('No sound playing')

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
        self.CurrentSound.update({'cutsound': False, 'priority': 1, 'playsleeping': True, 'ignorespeaking': True, 'delayer': random.randint(3, 7), 'is_playing': False})
        log.sound.debug('Chose breath: %s', self.CurrentSound)

    def Play(self):
        log.sound.debug(f'Playing: {self.CurrentSound}')

        # Now that we're actually playing the sound, tell the sound collection to not play it for a while
        if self.CurrentSound['replay_wait'] != 0 and self.CurrentSound['collection'] != None:
            sounds.collections[self.CurrentSound['collection']].SetSkipUntil(SoundID = self.CurrentSound['id'])

        # calculate what volume this should play at adjusting for proximity
        # this was really hard math to figure out for some reason
        # I was very close to giving up and writing a bunch of rediculous if statements
        # a proximity_volume_adjust of 1.0 means don't reduce the volume at all
        volume = int( (1.0 - (1.0 - float(self.CurrentSound['proximity_volume_adjust'])) * (1.0 - status.LoverProximity) ) * 100)

        # choose a random interval if the sound has a tempo adjust
        if self.CurrentSound['tempo_range'] != 0.0:
            random_tempo = random.randint(0, 8)
        
        else:
            # if the sound has no tempo adjust, index 4 is the original tempo 0, see the self.TempoMultipliers var
            random_tempo = 4

        # a list of lists like [[position_pct_float, secondsofsilencefloat], [position_pct_float, secondsofsilencefloat]]
        # I'm calculating sample position / total samples in the 0.wav original tempo sound
        # seems to be the best way to find the same position in wav files of varying length
        try:
            inter_word_silence = literal_eval(self.CurrentSound['inter_word_silence'])

        except ValueError:
            inter_word_silence = []

        # Some sounds have tempo variations. If so randomly choose one, otherwise it'll just be 0.wav
        self.PipeToShuttlecraft.send({'wavfile': f'./sounds_processed/{self.CurrentSound["id"]}/{self.TempoMultipliers[random_tempo]}.wav', 'vol': volume, 'insert_silence_here': inter_word_silence})

        # let stuff know this sound is playing, not just waiting in line
        self.CurrentSound['is_playing'] = True

    # Change the type of automatic breath sounds
    # I really ought to just abandon this type stuff anyway and sort them by intensity. Later. 
    def BreathChange(self, NewBreathType):

        log.sound.debug(f'Breath style changed to {NewBreathType}')
        self.BreathStyle = NewBreathType

    # Add a sound to the queue to be played
    def QueueSound(self, Sound = None, FromCollection = None, AltCollection = None, Intensity = None, CutAllSoundAndPlay = False, Priority = 5, PlayWhenSleeping = False, IgnoreSpeaking = False, Delay = 0):

        # if we're playing a sound from a collection, go fetch that rando
        if Sound == None and FromCollection != None:
            Sound = sounds.collections[FromCollection].GetRandomSound(intensity=Intensity)

        # If a collection is empty, or no sounds available at this time, it's possible to get a None sound. So try one more time.
        if Sound == None and AltCollection != None:
            Sound = sounds.collections[AltCollection].GetRandomSound(intensity=Intensity)

        # if fail, just chuck it. No sound for you
        if Sound != None:
            # Take the Sound and add all the options to it. Merges the two dicts into one. 
            # The collection name is saved so that we can update the delay wait only when the sound is played
            Sound.update({'collection': FromCollection, 'cutsound': CutAllSoundAndPlay, 'priority': Priority, 'playsleeping': PlayWhenSleeping, 'ignorespeaking': IgnoreSpeaking, 'delayer': Delay, 'is_playing': False})
            self.Queue_Breath.append(Sound)


    # Runs in a separate process for performance reasons. Sounds got crappy and this solved it. 
    def Shuttlecraft(self, PipeToStarship):

        try:

            # calculate some stuff
            # All the wav files are forced to the same format during preprocessing, currently stereo 44100
            # chopping the rate into 10 pieces, so that's 10 chunks per second. I might adjust later.
            # I tried 25 so that this gets called more often, but this is probably not necessary now, setting back to 10
            # I put it back to 25 so that there will be more variability when inserting silence
            rate = 44100
            periodspersecond = 25
            periodsize = rate // periodspersecond

            # The current wav file buffer thing
            # The pump is primed using some default sounds. 
            # I'm going to use a primitive way of selecting sound because this will be in a separate process.
            WavData = wave.open('./sounds_processed/{0}/0.wav'.format(random.choice([13, 14, 17, 23, 36, 40, 42, 59, 67, 68, 69, 92, 509, 515, 520, 527])))

            # I want to keep track to detect when we're at the last chunk so we can chuck it away and also tell the enterprise to send more sounds. 
            WavDataFrames = WavData.getnframes()

            # one periodsize of 16 bit silence data for stuffing into the buffer when pausing
            WavDataSilence = b'\x00\x00' * periodsize

            # counters for the silence stuffing
            SilentBlocks = 0
            CurrentPosition = 0
            NextSilence = []

            # Start up some fucking alsa
            device = alsaaudio.PCM(channels=1, rate=rate, format=alsaaudio.PCM_FORMAT_S16_LE, periodsize=periodsize)

            # init the mixer thing
            mixer = alsaaudio.Mixer(control='PCM')

            while True:

                # So basically, if there's something in the pipe, get it all out
                if PipeToStarship.poll():

                    Comms = PipeToStarship.recv()
                    log.sound.debug(f'Shuttlecraft received: {Comms}')

                    # graceful shutdown
                    if Comms['wavfile'] == 'selfdestruct':
                        log.sound.info('Shuttlecraft self destruct activated.')
                        break

                    # the volume gets set before each sound is played
                    mixer.setvolume(Comms['vol'])

                    # Normally the pipe will receive a path to a new wav file to start playing, stopping the previous sound
                    # it used to be just a string with a path, since I started dynamic volume changes this will be a dict
                    WavData = wave.open(Comms['wavfile'])
                    WavDataFrames = WavData.getnframes()
                    SilentBlocks = 0
                    CurrentPosition = 0

                    # for each insert silence position, now that we have the total length of the wav file, we can calculate the positions in sample number
                    # The s[1] is how many seconds to play silence, so we can also randomize and blockify that here
                    for s in Comms['insert_silence_here']:
                        s[0] = int(s[0] * WavDataFrames)
                        s[1] = int(random.random() * s[1] * periodspersecond)

                    # pop the first silence out of the list of lists
                    if len(Comms['insert_silence_here']) > 0:
                        NextSilence = Comms['insert_silence_here'][0]
                        Comms['insert_silence_here'].remove(NextSilence)

                    else:
                        NextSilence = []

                else:

                    # log.sound.debug(f'NextSilence: {NextSilence}  WavDataFrames: {WavDataFrames}  SilentBlocks: {SilentBlocks}  CurrentPosition: {CurrentPosition}')
                    # If there are still frames enough to write without being short
                    if CurrentPosition <= WavDataFrames:

                        # if we are at the spot where we need to insert silence, we want to send the samples to get right up to that exact sample,
                        # then insert a silence immediately after to get it playing
                        if len(NextSilence) > 0 and CurrentPosition + periodsize > NextSilence[0]:

                            # the second var in the list is the number of seconds of silence to insert, in blocks of periodsize
                            SilentBlocks = NextSilence[1]

                            # so we're going to write something that is much less than the period size, which the docs warn against doing
                            # but then immediately writing a full block of silence. So I dunno if it'll handle properly or not, might get mad, flip out
                            # log.sound.debug('Starting silence')
                            device.write(WavData.readframes(NextSilence[0] - CurrentPosition))
                            device.write(WavDataSilence)

                            # increment where in the audio we are now. Which should be, and always will be, by the power of greyskull, the exact position of the silence insert.
                            CurrentPosition = NextSilence[0]

                            # throw away the silence we just started. We don't need it anymore because we have SilentBlocks to carry it forward. There may be another. It's a list of lists
                            if len(Comms['insert_silence_here']) > 0:
                                NextSilence = Comms['insert_silence_here'][0]
                                Comms['insert_silence_here'].remove(NextSilence)

                            else:
                                NextSilence = []

                        else:

                            # if we're currently pumping out silence
                            if SilentBlocks > 0:
                                # log.sound.debug('Writing silence')
                                # write silence
                                device.write(WavDataSilence)

                                # decrement the counter
                                SilentBlocks -= 1

                            else:

                                # log.sound.debug('Writing wav data')
                                # write the frames, and if the buffer is full it will block here and provide the delay we need
                                device.write(WavData.readframes(periodsize))

                                # we are at this sample number
                                CurrentPosition += periodsize

                        # send a signal back to enterprise letting them know something is still being played
                        PipeToStarship.send(True)

                    else:
                        # otherwise, in this case the current wav has been sucked dry and we need something else
                        PipeToStarship.send(False)

                        # just masturbate for a little while
                        time.sleep(1 / periodspersecond)

        # log exception in the main.log
        except Exception as e:
            log.main.error('Shuttlecraft crashed. {0} {1} {2}'.format(e.__class__, e, log.format_tb(e.__traceback__)))


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
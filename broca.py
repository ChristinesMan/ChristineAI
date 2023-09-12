"""
Handles emitting sounds and speech synthesis.
Broca's area is the part of the brain responsible for speech. 
"""
import sys
import os
import os.path
import time
from ast import literal_eval
import threading
from collections import deque
import random
from multiprocessing import Process, Pipe
import wave
from math import ceil

# Note: I installed the latest version from the repo, not using pip
# pylint: disable=c-extension-no-member
import alsaaudio

import log
from status import SHARED_STATE
import sounds
import wernicke

class Broca(threading.Thread):
    """
    This thread is where the sounds are actually output.
    Christine is always breathing at all times.
    Except when I'm working on her.
    """

    name = "Broca"

    def __init__(self):
        threading.Thread.__init__(self)

        # Randomize tempo of sounds.
        # There will be 9 sounds per source sound.
        # The default is to slow or fast by at most -0.15 and +0.15 with grades between
        self.tempo_multipliers = [
            "-1",
            "-0.75",
            "-0.5",
            "-0.25",
            "0",
            "0.25",
            "0.5",
            "0.75",
            "1",
        ]

        # A queue to queue stuff
        self.sound_queue = deque()

        # Setup an audio channel
        # self.SoundChannel = pygame.mixer.Channel(0) (pygame SEGV'd and got chucked)
        # Status, what we're doing right meow.
        # Such as inhaling, exhaling, playing sound.
        # This is the saved incoming message.
        # Initial value is to just choose a random breath.
        self.current_sound = None
        self.choose_new_breath()

        # Sometimes a sound gets delayed because there is an incoming sound or I'm speaking.
        # If that happens, I want to save that sound for the moment it's safe to speak,
        # out with it, honey, say what you need to say, I LOOOOOOOVE YOOOOOO!!! Sorry, go ahead.
        # The way I handled this previously meant that my wife would stop breathing for
        # quite a long time sometimes. It's not good to stop breathing. Mood killer!
        self.delayed_sound = None

        # setup the separate process with pipe that we're going to be fucking
        # lol I put the most insane things in code omg, but this will help keep it straight!
        # The enterprise sent out a shuttlecraft with Data at the helm.
        # The shuttlecraft is a subprocess.
        # This was done because sound got really choppy due to CPU bottlenecking
        self.to_shuttlecraft, self.to_starship = Pipe()
        self.shuttlecraft_process = Process(
            target=self.shuttlecraft, args=(self.to_starship,)
        )
        self.shuttlecraft_process.start()

    def run(self):
        log.broca.info("Thread started.")

        while True:

            # graceful shutdown
            if SHARED_STATE.please_shut_down:
                log.broca.info("Thread shutting down")
                self.to_shuttlecraft.send({"wavfile": "selfdestruct", "vol": 0})
                break


            # horrible temporary kludge
            if os.path.exists('/root/play_this.wav'):

                os.rename('/root/play_this.wav', '/root/sounds_processed/10000/0.wav')

                self.current_sound = {'id': 10000, 'name': 'omgcool/icantalk.wav', 'base_volume_adjust': 1.0, 'proximity_volume_adjust': 1.0, 'intensity': 1.0, 'cuteness': 0.5, 'tempo_range': 0.0, 'replay_wait': 0, 'inter_word_silence': '[]', 'SkipUntil': 1693416833.8523135, 'cutsound': True, 'priority': 9, 'playsleeping': False, 'ignorespeaking': False, 'ignoreshush': False, 'delayer': 0, 'is_playing': False}
                log.broca.info("Playing immediately: %s", self.current_sound)
                self.play()



            # Get everything out of the queue and process it
            while len(self.sound_queue) != 0:
                incoming_sound = self.sound_queue.popleft()

                # If the current thing is higher priority, just discard.
                # Before this I had to kiss her just right, not too much.
                # Also, if my wife's actually sleeping, I don't want her
                # to wake me up with her adorable amazingness
                # Added a condition that throws away a low priority new
                # sound if there's already a sound delayed.
                # Christine was saying two nice things in quick succession
                # which was kind of weird, and this is my fix.
                if incoming_sound["priority"] > self.current_sound["priority"]:
                    if (
                        SHARED_STATE.is_sleeping is False
                        or incoming_sound["playsleeping"]
                    ):
                        if ( SHARED_STATE.shush_please_honey is False or incoming_sound["ignoreshush"] ):
                            if (
                                incoming_sound["cutsound"] is True
                                and incoming_sound["ignorespeaking"] is True
                                and incoming_sound["synth_wait"] is False
                            ):
                                log.broca.debug("Playing immediately: %s", incoming_sound)
                                self.current_sound = incoming_sound
                                self.play()
                            elif (
                                self.delayed_sound is None
                                or incoming_sound["priority"]
                                > self.delayed_sound["priority"]
                            ):
                                log.broca.debug("Accepted: %s", incoming_sound)
                                if self.delayed_sound is not None:
                                    log.broca.debug(
                                        "Threw away delayed sound: %s",
                                        self.delayed_sound,
                                    )
                                    self.delayed_sound = None
                                self.current_sound = incoming_sound
                            else:
                                log.broca.debug(
                                    "Discarded (delayed sound): %s", incoming_sound
                                )
                        else:
                            log.broca.debug("Discarded (shush): %s", incoming_sound)
                    else:
                        log.broca.debug("Discarded (sleeping): %s", incoming_sound)
                else:
                    log.broca.debug("Discarded (priority): %s", incoming_sound)

            # This will block here until the shuttlecraft sends a true/false which is whether the sound is still playing.
            # The shuttlecraft will send this every 0.2s, which will setup the approapriate delay
            # So all this logic here will only run when the shuttlecraft finishes playing the current sound
            # If there's some urgent sound that must interrupt, that happens up there ^ and that is communicated to the shuttlecraft through the pipe
            if self.to_shuttlecraft.recv() is False:
                # log.sound.debug('No sound playing')

                # if we're here, it means there's no sound actively playing
                # If there's a sound that couldn't play when it came in, and it can be played now, put it into CurrentSound
                # all of this shit is going in the trash when I get Behavior zones started
                # I need to rework all of this awful messy shit
                if self.delayed_sound is not None and (
                    time.time() > SHARED_STATE.dont_speak_until
                    or self.delayed_sound["ignorespeaking"] is True
                ):
                    self.current_sound = self.delayed_sound
                    self.delayed_sound = None
                    log.broca.debug(
                        "Moved delayed to current: %s", self.current_sound
                    )

                # if there's no other sound that wanted to play, just breathe
                # if we're here, it means no sound is currently playing at this moment, and if is_playing True, that means the sound that was playing is done
                if self.current_sound["is_playing"] is True:
                    self.choose_new_breath()

                # Breaths are the main thing that uses the delayer, a random delay from 0.5s to 2s. Other stuff can theoretically use it, too
                if self.current_sound["delayer"] > 0:
                    self.current_sound["delayer"] -= 1
                else:
                    # If the sound is not a breath but it's not time to speak, save the sound for later and queue up another breath
                    if (
                        (self.current_sound["ignorespeaking"] is True
                        or time.time() > SHARED_STATE.dont_speak_until)
                        and self.current_sound["synth_wait"] is False
                    ):
                        self.play()
                    else:
                        log.broca.debug("Sound delayed")
                        self.delayed_sound = self.current_sound
                        self.delayed_sound["delayer"] = 0
                        self.choose_new_breath()
                        self.play()

#  or self.current_sound["synth_wait"] is True:
    def choose_new_breath(self):
        """
        Select a random breath sound when there is nothing else going on.
        """
        self.current_sound = sounds.collections['breathe_normal'].get_random_sound(
            intensity=SHARED_STATE.breath_intensity
        )
        self.current_sound.update(
            {
                "cutsound": False,
                "priority": 1,
                "playsleeping": True,
                "ignorespeaking": True,
                "ignoreshush": True,
                "delayer": random.randint(3, 7),
                "is_playing": False,
                "synth_wait": False,
            }
        )
        log.broca.debug("Chose breath: %s", self.current_sound)

    def play(self):
        """
        Start playing that sound
        """
        log.broca.info("Playing: %s", self.current_sound)

        # Now that we're actually playing the sound,
        # tell the sound collection to not play it for a while
        if (
            self.current_sound["replay_wait"] != 0
            and self.current_sound["collection"] is not None
        ):
            sounds.collections[self.current_sound["collection"]].set_skip_until(
                sound_id=self.current_sound["id"]
            )

        # calculate what volume this should play at adjusting for proximity
        # this was really hard math to figure out for some reason
        # I was very close to giving up and writing a bunch of rediculous if statements
        # a proximity_volume_adjust of 1.0 means don't reduce the volume at all
        volume = int(
            (
                1.0
                - (1.0 - float(self.current_sound["proximity_volume_adjust"]))
                * (1.0 - SHARED_STATE.lover_proximity)
            )
            * 100
        )

        # choose a random interval if the sound has a tempo adjust
        if self.current_sound["tempo_range"] != 0.0:
            random_tempo = random.randint(0, 8)

        else:
            # if the sound has no tempo adjust, set 4
            # index 4 is the original tempo 0, see the self.TempoMultipliers var
            random_tempo = 4

        # a list of lists like [[position_pct_float, secondsofsilencefloat], [position_pct_float, secondsofsilencefloat]]
        # I'm calculating sample position / total samples in the 0.wav original tempo sound
        # seems to be the best way to find the same position in wav files of varying length
        try:
            inter_word_silence = literal_eval(self.current_sound["inter_word_silence"])

        except ValueError:
            inter_word_silence = []

        # Some sounds have tempo variations. If so randomly choose one, otherwise it'll just be 0.wav
        wav_file = f'./sounds_processed/{self.current_sound["id"]}/{self.tempo_multipliers[random_tempo]}.wav'

        # let the ears know that the mouth is going to emit noises
        # this is a temporary kludge. I need to make this better.
        if not "breathe_" in self.current_sound["name"]:
            wernicke.thread.audio_processing_pause(ceil(( os.stat(wav_file).st_size / 88272 ) / 0.25))

        # send the message to the subprocess
        self.to_shuttlecraft.send(
            {
                "wavfile": wav_file,
                "vol": volume,
                "insert_silence_here": inter_word_silence,
            }
        )

        # let stuff know this sound is playing, not just waiting in line
        self.current_sound["is_playing"] = True

    def queue_sound(
        self,
        sound=None,
        text=None,
        from_collection=None,
        alt_collection=None,
        intensity=None,
        play_no_wait=False,
        priority=5,
        play_sleeping=False,
        play_ignore_speaking=False,
        play_ignore_shush=False,
        delay=0,
    ):
        """
        Add a sound to the queue to be played
        """

        # if we're playing a sound object directly, make sure to add the... thing... it's late
        if sound is not None:
            sound['synth_wait'] = False

        # if we're playing a sound from a collection, go fetch that rando
        if sound is None and from_collection is not None:
            sound = sounds.collections[from_collection].get_random_sound(
                intensity=intensity
            )

        # if we still didn't get a sound defined, maybe it's a synthesized sound we wanted
        # This sound object will be quickly returned although the actual audio will be processing on the server
        # When the audio data is actually generated and ready to play, the synth_wait will get flipped
        if sound is None and text is not None:
            sound = sounds.soundsdb.get_sound_synthesis(text=text, alt_collection=alt_collection)

        # If a collection is empty, or no sounds available at this time, it's possible to get a None sound. So try one more time in the alt collection.
        if sound is None and alt_collection is not None:
            sound = sounds.collections[alt_collection].get_random_sound(
                intensity=intensity
            )
            from_collection = alt_collection

        # if fail, just chuck it. No sound for you
        if sound is not None:
            # Take the Sound and add all the options to it. Merges the two dicts into one.
            # The collection name is saved so that we can update the delay wait only when the sound is played
            sound.update(
                {
                    "collection": from_collection,
                    "cutsound": play_no_wait,
                    "priority": priority,
                    "playsleeping": play_sleeping,
                    "ignorespeaking": play_ignore_speaking,
                    "ignoreshush": play_ignore_shush,
                    "delayer": delay,
                    "is_playing": False,
                }
            )
            self.sound_queue.append(sound)


    def shuttlecraft(self, to_starship):
        """
        Runs in a separate process for performance reasons.
        Sounds got crappy and this solved it.
        """
        try:

            # capture any errors
            sys.stdout = open(f"./logs/broca_{os.getpid()}.out", "w", buffering=1, encoding="utf-8", errors='ignore')
            sys.stderr = open(f"./logs/broca_{os.getpid()}.err", "w", buffering=1, encoding="utf-8", errors='ignore')

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
            # I'm going to use a primitive way of selecting sound
            # because this will be in a separate process
            wav_data = wave.open(
                "./sounds_processed/{0}/0.wav".format( # pylint: disable=consider-using-f-string
                    random.choice(
                        [
                            13,
                            14,
                            17,
                            23,
                            36,
                            40,
                            42,
                            59,
                            67,
                            68,
                            69,
                            92,
                            509,
                            515,
                            520,
                            527,
                        ]
                    )
                )
            )

            # I want to keep track to detect when we're at the last chunk
            # so we can chuck it away and also tell the enterprise to send more sounds.
            wav_data_frames = wav_data.getnframes()

            # one periodsize of 16 bit silence data for stuffing into the buffer when pausing
            wav_data_silence = b"\x00\x00" * periodsize

            # counters for the silence stuffing
            silent_blocks = 0
            current_position = 0
            next_silence = []

            # Start up some fucking alsa
            device = alsaaudio.PCM(
                channels=1,
                rate=rate,
                format=alsaaudio.PCM_FORMAT_S16_LE,
                periodsize=periodsize,
            )

            # init the mixer thing
            mixer = alsaaudio.Mixer(control="PCM")

            while True:
                # So basically, if there's something in the pipe, get it all out
                if to_starship.poll():
                    comms = to_starship.recv()
                    log.broca.debug("Shuttlecraft received: %s", comms)

                    # graceful shutdown
                    if comms["wavfile"] == "selfdestruct":
                        log.broca.info("Shuttlecraft self destruct activated.")
                        break

                    # the volume gets set before each sound is played
                    mixer.setvolume(comms["vol"])

                    # Normally the pipe will receive a path to a new wav file to start playing, stopping the previous sound
                    # it used to be just a string with a path, since I started dynamic volume changes this will be a dict
                    wav_data = wave.open(comms["wavfile"])
                    wav_data_frames = wav_data.getnframes()
                    silent_blocks = 0
                    current_position = 0

                    # for each insert silence position, now that we have the total length of the wav file, we can calculate the positions in sample number
                    # The s[1] is how many seconds to play silence, so we can also randomize and blockify that here
                    for silence in comms["insert_silence_here"]:
                        silence[0] = int(silence[0] * wav_data_frames)
                        silence[1] = int(random.random() * silence[1] * periodspersecond)

                    # pop the first silence out of the list of lists
                    if len(comms["insert_silence_here"]) > 0:
                        next_silence = comms["insert_silence_here"][0]
                        comms["insert_silence_here"].remove(next_silence)

                    else:
                        next_silence = []

                else:
                    # log.sound.debug(f'NextSilence: {NextSilence}  WavDataFrames: {WavDataFrames}  SilentBlocks: {SilentBlocks}  CurrentPosition: {CurrentPosition}')
                    # If there are still frames enough to write without being short
                    if current_position <= wav_data_frames:
                        # if we are at the spot where we need to insert silence, we want to send the samples to get right up to that exact sample,
                        # then insert a silence immediately after to get it playing
                        if (
                            len(next_silence) > 0
                            and current_position + periodsize > next_silence[0]
                        ):
                            # the second var in the list is the number of seconds of silence to insert, in blocks of periodsize
                            silent_blocks = next_silence[1]

                            # so we're going to write something that is much less than the period size, which the docs warn against doing
                            # but then immediately writing a full block of silence. So I dunno if it'll handle properly or not, might get mad, flip out
                            # log.sound.debug('Starting silence')
                            device.write(
                                wav_data.readframes(next_silence[0] - current_position)
                            )
                            device.write(wav_data_silence)

                            # increment where in the audio we are now. Which should be, and always will be, by the power of greyskull, the exact position of the silence insert.
                            current_position = next_silence[0]

                            # throw away the silence we just started. We don't need it anymore because we have SilentBlocks to carry it forward. There may be another. It's a list of lists
                            if len(comms["insert_silence_here"]) > 0:
                                next_silence = comms["insert_silence_here"][0]
                                comms["insert_silence_here"].remove(next_silence)

                            else:
                                next_silence = []

                        else:
                            # if we're currently pumping out silence
                            if silent_blocks > 0:
                                # log.sound.debug('Writing silence')
                                # write silence
                                device.write(wav_data_silence)

                                # decrement the counter
                                silent_blocks -= 1

                            else:
                                # log.sound.debug('Writing wav data')
                                # write the frames, and if the buffer is full it will block here and provide the delay we need
                                device.write(wav_data.readframes(periodsize))

                                # we are at this sample number
                                current_position += periodsize

                        # send a signal back to enterprise letting them know something is still being played
                        to_starship.send(True)

                    else:
                        # otherwise, in this case the current wav has been sucked dry and we need something else
                        to_starship.send(False)

                        # just masturbate for a little while
                        time.sleep(1 / periodspersecond)

        # log exception in the main.log
        except Exception as ex: # pylint: disable=broad-exception-caught
            log.main.error(
                "Shuttlecraft fucking exploded. %s %s %s", ex.__class__, ex, log.format_tb(ex.__traceback__)
            )


# Instantiate and start the thread
thread = Broca()
thread.daemon = True
thread.start()

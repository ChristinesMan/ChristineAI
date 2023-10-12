"""
Handles emitting sounds and speech synthesis.
Broca's area is the part of the brain responsible for speech. 
"""
import sys
import os
import os.path
import time
# from ast import literal_eval
import threading
# from collections import deque
import random
from multiprocessing import Process, Pipe
import wave
from math import ceil

# pyalsaaudio seems to have died after the recent drastic Raspbian and python upgrades
# import alsaaudio
# import simpleaudio
import pyaudio

from christine import log
from christine.status import SHARED_STATE
from christine import sounds
from christine import wernicke

class Broca(threading.Thread):
    """
    This thread is where the sounds are actually output.
    Christine is always breathing at all times.
    Except when I'm working on her.
    """

    name = "Broca"

    def __init__(self):
        threading.Thread.__init__(self)

        # this holds the next actual non-breath sound that will play
        self.next_sound = None

        # This allows a random delay before breathing again
        self.delayer = 0

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

            # This recv will block here until the shuttlecraft sends a true/false which is whether the sound is still playing.
            # The shuttlecraft will send this every 0.2s, which will setup the approapriate delay
            # So all this logic here will only run when the shuttlecraft finishes playing the current sound
            # If there's some urgent sound that must interrupt, that is communicated to the shuttlecraft through the pipe
            if self.to_shuttlecraft.recv() is False:
                # log.sound.debug('No sound playing')

                # if we're here, it means there's no sound actively playing
                if self.next_sound is not None and self.next_sound['synth_wait'] is False:

                    self.play_next_sound()

                else:

                    if self.delayer > 0:
                        self.delayer -= 1
                    else:
                        self.just_breath()

    def just_breath(self):
        """
        Select a random breath sound when there is nothing else going on.
        """

        # select a random breathing sound
        next_breath = sounds.collections['breathe_normal'].get_random_sound(
            intensity=SHARED_STATE.breath_intensity
        )

        # get the file name
        wav_file = f'./sounds_processed/{next_breath["id"]}/0.wav'

        # send the message to the subprocess
        self.to_shuttlecraft.send(
            {
                "wavfile": wav_file,
                "vol": 100,
            }
        )

        # set the delayer to a random number of periods for the next time
        # currently 10 periods per second
        self.delayer = 5 + (random.random() * 8)

        log.broca.debug("Chose breath: %s", next_breath)

    def play_next_sound(self):
        """
        Start playing that sound
        """
        log.broca.info("Playing: %s", self.next_sound)

        # Now that we're actually playing the sound,
        # tell the sound collection to not play it for a while
        if (
            self.next_sound["replay_wait"] != 0
            and self.next_sound["collection"] is not None
        ):
            sounds.collections[self.next_sound["collection"]].set_skip_until(
                sound_id=self.next_sound["id"]
            )

        # calculate what volume this should play at adjusting for proximity
        # this was really hard math to figure out for some reason
        # I was very close to giving up and writing a bunch of rediculous if statements
        # a proximity_volume_adjust of 1.0 means don't reduce the volume at all
        volume = int(
            (
                1.0
                - (1.0 - float(self.next_sound["proximity_volume_adjust"]))
                * (1.0 - SHARED_STATE.lover_proximity)
            )
            * 100
        )

        # get the file name
        wav_file = f'./sounds_processed/{self.next_sound["id"]}/0.wav'

        # let the ears know that the mouth is going to emit noises that are not breathing
        wernicke.thread.audio_processing_pause(ceil(( os.stat(wav_file).st_size / 88272 ) / 0.25))

        # send the message to the subprocess
        self.to_shuttlecraft.send(
            {
                "wavfile": wav_file,
                "vol": volume,
            }
        )

        # now that the sound is playing, we can discard this
        self.next_sound = None

        # well, it didn't really end, but it's definitely ready for the next sound
        SHARED_STATE.behaviour_zone.notify_sound_ended()

    def queue_sound(
        self,
        sound=None,
        from_collection=None,
        alt_collection=None,
        intensity=None,
        priority=5,
        play_no_wait=False,
    ):
        """
        Add a sound to the queue to be played
        """

        # if we're playing a sound from a collection, go fetch that rando
        if sound is None and from_collection is not None:
            sound = sounds.collections[from_collection].get_random_sound(
                intensity=intensity
            )

        # If a collection is empty, or no sounds available at this time, it's possible to get a None sound. So try one more time in the alt collection.
        if sound is None and alt_collection is not None:
            sound = sounds.collections[alt_collection].get_random_sound(
                intensity=intensity
            )
            from_collection = alt_collection

        # if fail, just chuck it. No sound for you
        if sound is not None:

            # The collection name is saved so that we can update the delay wait only when the sound is played
            if self.next_sound is None or priority > self.next_sound['priority']:
                sound.update({"collection": from_collection, "priority": priority, "synth_wait": False})
                self.next_sound = sound

                if play_no_wait is True:
                    self.play_next_sound()

    def queue_text(
        self,
        text=None,
    ):
        """Voice synthesis"""

        if text is not None:
            self.next_sound = sounds.soundsdb.get_sound_synthesis(text=text)
            self.next_sound['priority'] = 10

    def shuttlecraft(self, to_starship):
        """
        Runs in a separate process for performance reasons.
        Sounds got crappy and this solved it.
        """
        try:

            # capture any errors
            sys.stdout = open(f"./logs/subprocess_broca_{os.getpid()}.out", "w", buffering=1, encoding="utf-8", errors='ignore')
            sys.stderr = open(f"./logs/subprocess_broca_{os.getpid()}.err", "w", buffering=1, encoding="utf-8", errors='ignore')

            # # calculate some stuff
            # # All the wav files are forced to the same format during preprocessing, currently stereo 44100
            # # chopping the rate into 10 pieces, so that's 10 chunks per second. I might adjust later.
            # # I tried 25 so that this gets called more often, but this is probably not necessary now, setting back to 10
            # # I put it back to 25 so that there will be more variability when inserting silence
            # rate = 44100
            # periodspersecond = 25
            # periodsize = rate // periodspersecond

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

            # # I want to keep track to detect when we're at the last chunk
            # # so we can chuck it away and also tell the enterprise to send more sounds.
            # wav_data_frames = wav_data.getnframes()

            # # one periodsize of 16 bit silence data for stuffing into the buffer when pausing
            # wav_data_silence = b"\x00\x00" * periodsize

            # # counters for the silence stuffing
            # silent_blocks = 0
            # current_position = 0
            # next_silence = []

            # # Start fucking alsa
            # device = alsaaudio.PCM(
            #     channels=1,
            #     rate=rate,
            #     format=alsaaudio.PCM_FORMAT_S16_LE,
            #     periodsize=periodsize,
            # )

            # # init the mixer thing
            # mixer = alsaaudio.Mixer(control="PCM")

            # Start up some pyaudio
            pya = pyaudio.PyAudio()

            # This will feed new wav data into pyaudio
            def wav_data_feeder(in_data, frame_count, time_info, status): # pylint: disable=unused-argument
                # print(f'frame_count: {frame_count}  status: {status}')
                return (wav_data.readframes(frame_count), pyaudio.paContinue)

            # Start the pyaudio stream
            pya_stream = pya.open(format=8, channels=1, rate=44100, output=True, stream_callback=wav_data_feeder)

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
                    # mixer.setvolume(comms["vol"])
                    # pyalsaaudio died so we have to forking fork
                    os.system(f'amixer -q cset numid=1 {comms["vol"]}%')

                    # stop stream, open wav file, and start the stream back up
                    # I do wonder now if this was why pyaudio used to lock up
                    # it used to be that I would open a new wav file before stopping stream
                    pya_stream.stop_stream()
                    wav_data = wave.open(comms["wavfile"])
                    pya_stream.start_stream()

                else:
                    # otherwise, in this case the current wav has been sucked dry and we need something else
                    to_starship.send(pya_stream.is_active())

                    # just masturbate for a little while
                    time.sleep(0.1)











                #     # Normally the pipe will receive a path to a new wav file to start playing, stopping the previous sound
                #     # it used to be just a string with a path, since I started dynamic volume changes this will be a dict
                #     wav_data = wave.open(comms["wavfile"])
                #     wav_data_frames = wav_data.getnframes()
                #     silent_blocks = 0
                #     current_position = 0
                #     pya_stream.stop_stream()
                #     pya_stream.start_stream()

                #     # for each insert silence position, now that we have the total length of the wav file, we can calculate the positions in sample number
                #     # The s[1] is how many seconds to play silence, so we can also randomize and blockify that here
                #     for silence in comms["insert_silence_here"]:
                #         silence[0] = int(silence[0] * wav_data_frames)
                #         silence[1] = int(random.random() * silence[1] * periodspersecond)

                #     # pop the first silence out of the list of lists
                #     if len(comms["insert_silence_here"]) > 0:
                #         next_silence = comms["insert_silence_here"][0]
                #         comms["insert_silence_here"].remove(next_silence)

                #     else:
                #         next_silence = []

                # else:
                #     # log.sound.debug(f'NextSilence: {NextSilence}  WavDataFrames: {WavDataFrames}  SilentBlocks: {SilentBlocks}  CurrentPosition: {CurrentPosition}')
                #     # If there are still frames enough to write without being short
                #     if current_position <= wav_data_frames:
                #         # if we are at the spot where we need to insert silence, we want to send the samples to get right up to that exact sample,
                #         # then insert a silence immediately after to get it playing
                #         if (
                #             len(next_silence) > 0
                #             and current_position + periodsize > next_silence[0]
                #         ):
                #             # the second var in the list is the number of seconds of silence to insert, in blocks of periodsize
                #             silent_blocks = next_silence[1]

                #             # so we're going to write something that is much less than the period size, which the docs warn against doing
                #             # but then immediately writing a full block of silence. So I dunno if it'll handle properly or not, might get mad, flip out
                #             # log.sound.debug('Starting silence')
                #             device.write(
                #                 wav_data.readframes(next_silence[0] - current_position)
                #             )
                #             device.write(wav_data_silence)

                #             # increment where in the audio we are now. Which should be, and always will be, by the power of greyskull, the exact position of the silence insert.
                #             current_position = next_silence[0]

                #             # throw away the silence we just started. We don't need it anymore because we have SilentBlocks to carry it forward. There may be another. It's a list of lists
                #             if len(comms["insert_silence_here"]) > 0:
                #                 next_silence = comms["insert_silence_here"][0]
                #                 comms["insert_silence_here"].remove(next_silence)

                #             else:
                #                 next_silence = []

                #         else:
                #             # if we're currently pumping out silence
                #             if silent_blocks > 0:
                #                 # log.sound.debug('Writing silence')
                #                 # write silence
                #                 device.write(wav_data_silence)

                #                 # decrement the counter
                #                 silent_blocks -= 1

                #             else:
                #                 # log.sound.debug('Writing wav data')
                #                 # write the frames, and if the buffer is full it will block here and provide the delay we need
                #                 device.write(wav_data.readframes(periodsize))

                #                 # we are at this sample number
                #                 current_position += periodsize

                #         # send a signal back to enterprise letting them know something is still being played
                #         to_starship.send(True)

                #     else:
                #         # otherwise, in this case the current wav has been sucked dry and we need something else
                #         to_starship.send(False)

                #         # just masturbate for a little while
                #         time.sleep(1 / periodspersecond)








        # log exception in the main.log
        except Exception as ex: # pylint: disable=broad-exception-caught
            log.main.error(
                "Shuttlecraft fucking exploded. %s %s %s", ex.__class__, ex, log.format_tb(ex.__traceback__)
            )


# Instantiate and start the thread
thread = Broca()
thread.daemon = True
thread.start()

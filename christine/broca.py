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
import pyaudio

from christine import log
from christine.status import STATE
from christine import sounds
from christine import wernicke
from christine import behaviour

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
        # Init to a sorta high number to avoid starting too soon, should be about 15s
        self.delayer = 150

        # capture the priority of whatever sound is playing now
        self.playing_now_priority = 5

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
            if STATE.please_shut_down:
                log.broca.info("Thread shutting down")
                self.to_shuttlecraft.send({"wavfile": "selfdestruct", "vol": 0})
                break

            # This recv will block here until the shuttlecraft sends a true/false which is whether the sound is still playing.
            # The shuttlecraft will send this every 0.2s, which will setup the approapriate delay
            # So all this logic here will only run when the shuttlecraft finishes playing the current sound
            # If there's some urgent sound that must interrupt, that is communicated to the shuttlecraft through the pipe
            if self.to_shuttlecraft.recv() is False:
                # log.broca.debug('No sound playing')

                # if we're here, it means there's no sound actively playing
                if self.next_sound is not None and self.next_sound['synth_wait'] is False:

                    self.play_next_sound()

                else:

                    if self.delayer > 0:
                        self.delayer -= 1
                    else:
                        self.just_breath()

            else:

                # handle the case of a sound coming in that should interrupt the sound / breath currently playing
                if self.next_sound is not None and self.next_sound['play_no_wait'] is True and self.next_sound['synth_wait'] is False and self.next_sound['priority'] > self.playing_now_priority:

                    self.play_next_sound()


    def just_breath(self):
        """
        Select a random breath sound when there is nothing else going on.
        """

        # select a random breathing sound
        next_breath = sounds.db.get_random_sound(collection_name='breathing', intensity=STATE.breath_intensity)

        # Fail gracefully
        if next_breath is None:
            log.main.error('No breathing sound was available!')
            return

        # send the message to the subprocess
        self.to_shuttlecraft.send(
            {
                "wavfile": next_breath['file_path'],
                "vol": 100,
            }
        )

        # breaths have 0 priority, they can always be interrupted
        self.playing_now_priority = 0

        # set the delayer to a random number of periods for the next time
        # currently 10 periods per second
        self.delayer = 5 + (random.random() * 8)

        # log.broca.debug("Chose breath: %s", next_breath)

    def play_next_sound(self):
        """
        Start playing that sound
        """
        log.broca.info("Playing: %s", self.next_sound)

        # Now that we're actually playing the sound,
        # tell the sound collection to not play it for a while
        if self.next_sound["replay_wait"] != 0:
            sounds.db.set_skip_until(sound_id=self.next_sound["id"])

        # calculate what volume this should play at adjusting for proximity
        # this was really hard math to figure out for some reason
        # I was very close to giving up and writing a bunch of rediculous if statements
        # a proximity_volume_adjust of 1.0 means don't reduce the volume at all
        volume = int(
            (
                1.0
                - (1.0 - float(self.next_sound["proximity_volume_adjust"]))
                * (1.0 - STATE.lover_proximity)
            )
            * 100
        )

        # pop out the file path
        file_path = self.next_sound["file_path"]

        # if the file doesn't exist somehow, fail graceful like
        if os.path.isfile(file_path) is False:
            log.main.warning('Sound file %s does not exist.', file_path)
            self.next_sound = None
            return

        # let the ears know that the mouth is going to emit noises that are not breathing
        # since I stopped TTS from appending silence to synthesized voice audio I have noticed some garbage heard after speaking
        # so that's why I'm adjusting this by 0.5s.
        # the number of seconds in the wav file are estimated based on the file size, then 0.5s is added as padding,
        # then / 0.25 because blocks are 0.25s long.
        # So now that I made the wernicke send about 32 times more tiny blocks, increasing this
        wernicke.thread.audio_processing_pause(ceil( os.stat(file_path).st_size / 2100 ))

        # send the message to the subprocess
        self.to_shuttlecraft.send(
            {
                "wavfile": file_path,
                "vol": volume,
            }
        )

        # save the priority so that we can tell what can interrupt it
        self.playing_now_priority = self.next_sound['priority']

        # now that the sound is playing, we can discard this
        self.next_sound = None

        # well, it didn't really end, but it's definitely ready for the next sound
        behaviour.thread.notify_sound_ended()

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
            sound = sounds.db.get_random_sound(collection_name=from_collection, intensity=intensity)

        # If a collection is empty, or no sounds available at this time, it's possible to get a None sound. So try one more time in the alt collection.
        if sound is None and alt_collection is not None:
            sound = sounds.db.get_random_sound(collection_name=alt_collection, intensity=intensity)
            from_collection = alt_collection

        # if fail, just chuck it. No sound for you
        if sound is not None:

            # The collection name is saved so that we can see it in the logs
            if self.next_sound is None or priority > self.next_sound['priority']:
                sound.update({"collection": from_collection, "priority": priority, "synth_wait": False})

                # if we are requesting to interrupt a playing sound, and the sound playing is not as high priority, we can interrupt
                if play_no_wait is True and sound['priority'] > self.playing_now_priority:
                    sound['play_no_wait'] = True
                else:
                    sound['play_no_wait'] = False

                self.next_sound = sound

    def queue_text(self, text=None):
        """Voice synthesis"""

        if text is not None:

            sound = sounds.db.get_sound_synthesis(text=text)
            sound.update({"collection": "synth", "priority": 10, "play_no_wait": True})
            self.next_sound = sound

    def notify_synth_done(self):
        """The sounds module starts a voice synthesis process, and calls this when it's completed."""

        if self.next_sound is not None:
            self.next_sound['synth_wait'] = False

    def shuttlecraft(self, to_starship):
        """
        Runs in a separate process for performance reasons.
        Sounds got crappy and this solved it.
        """

        # capture any errors
        sys.stdout = open(f"./logs/subprocess_broca_{os.getpid()}.out", "w", buffering=1, encoding="utf-8", errors='ignore')
        sys.stderr = open(f"./logs/subprocess_broca_{os.getpid()}.err", "w", buffering=1, encoding="utf-8", errors='ignore')

        # The current wav file buffer thing
        # The pump is primed using some default sound.
        wav_data = wave.open("sounds/beep.wav")

        # # Start fucking alsa
        # # Oh, alsa died of 64bititis
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

# Instantiate and start the thread
thread = Broca()
thread.daemon = True
thread.start()

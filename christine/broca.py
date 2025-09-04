"""
Handles emitting sounds in the proper order.
Broca's area is the part of the brain responsible for speech. 
"""
import sys
import os
import os.path
import time
# from ast import literal_eval
import threading
import queue
import re
from multiprocessing import Process, Pipe

from christine import log
from christine.status import STATE
from christine.sounds import sounds_db
from christine.figment import Figment

class Broca(threading.Thread):
    """
    This thread is where the sounds are actually output.
    Christine is always breathing at all times.
    Except when I'm working on her.
    """

    name = "Broca"

    def __init__(self):
        super().__init__(daemon=True)

        # Direct broca-wernicke coordination via shared memory (set later by main)
        self.audio_coordination = None

        # queue up figments to feed into broca one at a time
        self.figment_queue = queue.Queue()

        # track wernicke pause state to prevent conflicts
        self.wernicke_paused_by_broca = False

        # regexes to detect certain text in non-spoken figments that should set off an emote
        self.re_emote_laugh = re.compile(
            r"tease|amusement|haha|laugh|chuckle|snicker|chortle|giggle|guffaw|smile|blush", flags=re.IGNORECASE
        )
        self.re_emote_grrr = re.compile(
            r"grrr|gasp|frustrat|treating you poorly|disrespecting your boundaries|anger", flags=re.IGNORECASE
        )
        self.re_emote_yawn = re.compile(
            r"yawn|sleep|tire|sigh", flags=re.IGNORECASE
        )

        # detect trailing punctuation, for inserting approapriate pauses
        self.re_period = re.compile(r"[\.;!]\s*$")
        self.re_question = re.compile(r'\?"?\s*$|\.{2,3}"?\s*$')
        self.re_comma = re.compile(r",\s*$")

        # the LLM has a strong tendency to repeat itself, as LLMs do
        self.repetition_destroyer = {}
        self.repetition_max_ttl = 5

        # setup the separate process with pipe that we're going to be fucking
        # lol I put the most insane things in code omg, but this will help keep it straight!
        # The enterprise sent out a shuttlecraft with Data at the helm.
        # The shuttlecraft is a subprocess.
        # This was done because sound got really choppy due to probably python bottlenecking
        # Note: Process creation moved to run() method to allow shared memory injection
        self.to_shuttlecraft = None
        self.to_starship = None
        self.shuttlecraft_process = None

    def run(self):

        # Create subprocess communication after shared memory is injected
        self.to_shuttlecraft, self.to_starship = Pipe()
        self.shuttlecraft_process = Process(
            target=self.shuttlecraft, args=(self.to_starship, self.audio_coordination)
        )
        
        # Start the shuttlecraft subprocess
        log.broca_main.info("Thread started - starting shuttlecraft subprocess")
        self.shuttlecraft_process.start()

        while True:

            try:

                # graceful shutdown
                if STATE.please_shut_down:
                    log.broca_main.info("Thread shutting down")
                    self.to_shuttlecraft.send({"action": "selfdestruct"})
                    break

                # the shuttlecraft takes one item at a time
                # DIRECT COORDINATION: No more signal-based wernicke coordination needed!
                # Audio coordination now happens directly via shared memory between subprocesses
                if self.to_shuttlecraft.poll(0.1):  # 100ms timeout
                    msg = self.to_shuttlecraft.recv()
                    log.broca_main.debug("Received: %s", msg)

                    if msg['action'] == 'idle':

                        # if we're here, it means there's no sound actively playing, not even a breath
                        # this user_is_speaking flag is set by the wernicke when it's time to shut up
                        if STATE.user_is_speaking is False:

                            # if there's something in the queue, play it
                            if self.figment_queue.qsize() > 0:
                                self.play_next_figment()
                else:
                    # No message available within timeout - continue processing to prevent backup
                    # This prevents the main thread from getting stuck waiting for shuttlecraft
                    pass

            # log the exception but keep the thread running
            except Exception as ex:
                log.main.exception(ex)
                log.play_sound()

    def play_next_figment(self):
        """Get the next figment from the queue and process it."""

        # import here to avoid circular import
        # pylint: disable=import-outside-toplevel
        from christine.parietal_lobe import parietal_lobe

        # wrapping this all in a try because interruptions shappen
        try:

            # get the next figment from the queue
            figment: Figment = self.figment_queue.get_nowait()

            # log it
            log.broca_main.debug('Pulled figment from queue: %s', figment)

            # figure out the type of figment and do the things
            if figment.pause_duration is not None:

                self.to_shuttlecraft.send(
                    {
                        "action": "pause",
                        "pause_duration": figment.pause_duration,
                    }
                )
                return

            elif figment.from_collection is not None:

                # sounds with a collection of "sex" tend to pile up quickly which causes sex noises long after the actions that caused them
                # so if the figment is "sex", let's pull figments out of the queue until the queue is either empty or there's something other than "sex"
                if "sex" in figment.from_collection:
                    while self.figment_queue.qsize() > 0:
                        next_figment: Figment = self.figment_queue.get_nowait()
                        log.broca_main.debug('In response to sex, pulled figment from queue: %s', next_figment)
                        if not "sex" in next_figment.from_collection:
                            log.broca_main.debug('Putting it back in queue and getting out of here.')
                            self.figment_queue.put_nowait(next_figment)
                            return

                # get the sound from the collection
                sound = sounds_db.get_random_sound(collection_name=figment.from_collection, intensity=figment.intensity)

                # if the sound is None, log it and move on
                if sound is None:
                    log.main.warning('No sound was available in collection %s.', figment.from_collection)
                    return

                # if the file doesn't exist somehow, fail graceful like
                if os.path.isfile(sound.file_path) is False:
                    log.main.warning('Sound file %s does not exist.', sound.file_path)
                    return

                # let the ears know that the mouth is going to emit noises that are not breathing
                # send the message to the subprocess with signal-based coordination
                # the subprocess will handle timing the wernicke pause precisely
                pause_wernicke = sound.pause_wernicke if sound.pause_wernicke is True else False

                # send the message to the subprocess
                self.to_shuttlecraft.send(
                    {
                        "action": "playwav",
                        "wavfile": sound.file_path,
                        "vol": 100,
                        "pause_wernicke": pause_wernicke,
                    }
                )

            elif figment.text is not None:

                # purge old stuff from the repetition destroyer and decrement
                for key in list(self.repetition_destroyer):
                    if self.repetition_destroyer[key] > 0:
                        self.repetition_destroyer[key] -= 1
                    else:
                        self.repetition_destroyer.pop(key)

                # standardize the sentence to letters only
                text_stripped = re.sub("[^a-zA-Z]", "", figment.text).lower()

                # if this sequence of letters has shown up anywhere in the past 5 responses, destroy it
                if text_stripped in self.repetition_destroyer:
                    self.repetition_destroyer[text_stripped] = self.repetition_max_ttl
                    log.parietal_lobe.info('Destroyed: %s', figment.text)
                    return

                # remember this for later destruction
                self.repetition_destroyer[text_stripped] = self.repetition_max_ttl

                if figment.should_speak is True:

                    # # # calculate what volume this should play at adjusting for proximity
                    # # # this was really hard math to figure out for some reason
                    # # # I was very close to giving up and writing a bunch of rediculous if statements
                    # # # a proximity_volume_adjust of 1.0 means don't reduce the volume at all
                    # volume = int(
                    #     (
                    #         1.0
                    #         - (1.0 - STATE.proximity_volume_adjust)
                    #         * (1.0 - STATE.lover_proximity)
                    #     )
                    #     * 100
                    # )

                    # in the case of synthesized speech, we need to block here until the file is ready
                    # this is because the file is generated in a separate thread
                    # the tts call should time out in 60s, so shouldn't get stuck
                    # wait for the wav file to be ready and also wait until it is ok to speak
                    # DIRECT COORDINATION: No need to check for wernicke signals here anymore! BOO-YA!
                    while figment.wav_file is None or STATE.user_is_speaking is True:
                        time.sleep(0.2)

                    # let the ears know that the mouth is going to emit noises that are not breathing
                    # send the message to the subprocess with signal-based coordination
                    # the subprocess will handle timing the wernicke pause precisely

                    # send the message to the subprocess
                    self.to_shuttlecraft.send(
                        {
                            "action": "playwav",
                            "wavfile": figment.wav_file,
                            "vol": 100,
                            "pause_wernicke": True,  # always pause for speech
                        }
                    )

                # notify the parietal lobe that something with text that was queued by it is now playing
                parietal_lobe.broca_figment_was_processed(figment)

        # this would usually occur when next_sound gets set to None by speaking being interrupted
        except TypeError as ex:
            log.broca_main.exception(ex)

    def accept_figment(self, figment: Figment):
        """Accept a figment from the parietal lobe and queue it up for processing."""

        # if the new figment is to be spoken,
        if figment.should_speak is True:

            # if a spoken figment gets through with no letters at all, drop it. Usually this is '" '
            if re.search(r'[a-zA-Z]', figment.text) is None:
                log.broca_main.warning("Empty string spoken figment.")
                return

            # start the thread asap to get the api call for synthesized speech going
            figment.start()

            # add a figment for an inhalation sound that will precede this spoken figment
            self.figment_queue.put_nowait(Figment(from_collection='inhalation'))
            log.broca_main.debug("Queued: Inhalation")

        # put the figment on the queue
        self.figment_queue.put_nowait(figment)
        log.broca_main.debug("Queued: %s", figment)

        # if the text is spoken and ends with certain punctuation, a pause is inserted after to allow time for interruption.
        if figment.should_speak is True:

            if self.re_question.search(figment.text):
                self.figment_queue.put_nowait(Figment(pause_duration=STATE.pause_question))
                log.broca_main.debug("Queued: Question Pause")
            elif self.re_period.search(figment.text):
                self.figment_queue.put_nowait(Figment(pause_duration=STATE.pause_period))
                log.broca_main.debug("Queued: Period Pause")
            elif self.re_comma.search(figment.text):
                self.figment_queue.put_nowait(Figment(pause_duration=STATE.pause_comma))
                log.broca_main.debug("Queued: Comma Pause")

        # in the case of unspoken text, let's look for emotes such as laughing, yawning, etc
        elif figment.text is not None:

            # figure out which emote
            from_collection = None
            if self.re_emote_laugh.search(figment.text):
                from_collection = 'laughing'
            elif self.re_emote_grrr.search(figment.text):
                from_collection = 'disgust'
            elif self.re_emote_yawn.search(figment.text):
                from_collection = 'sleepy'

            if from_collection is not None:

                # first, inspect the queue to see if the last thing we queued was a pause
                # if it was, we will insert the emote before that pause
                if self.figment_queue.qsize() > 0:
                    last_figment: Figment = self.figment_queue.queue[-1]
                    if last_figment.pause_duration is not None:
                        self.figment_queue.queue[-1] = Figment(from_collection=from_collection)
                        self.figment_queue.put_nowait(last_figment)
                    else:
                        self.figment_queue.put_nowait(Figment(from_collection=from_collection))

                    log.broca_main.debug("Queued: Emote %s", from_collection)

    def flush_figments(self):
        """Immediately stop speaking. Flush the queue."""

        # import here to avoid circular import
        # pylint: disable=import-outside-toplevel
        from christine.parietal_lobe import parietal_lobe
        # Direct coordination via shared memory - no need for wernicke import! YAY!

        # CRITICAL: Tell shuttlecraft to stop any ongoing audio immediately
        # This prevents audio from playing after interruption
        self.to_shuttlecraft.send({"action": "stop_audio"})

        # When flushing, wernicke coordination is now handled directly via shared memory
        # No need for manual wernicke restart - the shuttlecraft will clear the flag

        # keeps track of whether speaking was actually interrupted
        interrupted = False

        # pull everything out of the queue, and if there were any other spoken figments, tell parietal lobe it got interrupted
        # until interrupted gets set to true, we also want to flush any non-spoken thoughts into the parietal lobe
        # after interrupted, everything just gets chucked
        while self.figment_queue.qsize() > 0:

            # get the next figment
            figment: Figment = self.figment_queue.get_nowait()

            # if the figment is spoken, set the interrupted flag, and everything after this gets thrown out
            if figment.should_speak is True:
                interrupted = True

            # if we're not already interrupted, send the figment back to the parietal lobe
            if interrupted is False:
                if figment.text is not None:
                    parietal_lobe.broca_figment_was_processed(figment)
            else:
                log.parietal_lobe.info("Interrupted: %s", figment)

        # if we were interrupted at some point in the queue flush, let parietal lobe know it needs to file off the end nice and smooth
        if interrupted is True:
            parietal_lobe.broca_speech_interrupted()

    def shuttlecraft(self, to_starship, audio_coordination):
        """
        Runs in a separate process for performance reasons.
        Sounds got crappy and this solved it.
        """

        # capture any errors
        sys.stdout = open(f"./logs/subprocess_broca_{os.getpid()}.out", "w", buffering=1, encoding="utf-8", errors='ignore')
        sys.stderr = open(f"./logs/subprocess_broca_{os.getpid()}.err", "w", buffering=1, encoding="utf-8", errors='ignore')

        # pyalsaaudio seems to have died after the recent drastic Raspbian and python upgrades
        # import alsaaudio
        # pylint: disable=import-outside-toplevel
        import wave
        import random
        import pyaudio

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

        # The pyaudio stream is instantiated
        pya_stream = pya.open(format=8, channels=1, rate=44100, output=True, stream_callback=wav_data_feeder)

        # keep track of the last volume that was set, to avoid all the amixer forking
        # I miss pyalsaaudio
        last_volume = 100

        # So, often there's nothing playing from the speaker, and after 3-4s the speaker goes into standby mode
        # This causes some sounds to get cut off. So this var is an attempt to detect when that will be a problem
        # and play a sound to get it started back up
        # However, this might never get triggered with the breathing logic the way it is, so might remove later
        seconds_idle = 0.0
        seconds_idle_to_play_presound = 4.0

        # seconds to wait before breathing
        seconds_to_breathe = 0.5

        # The shuttlecraft is now in orbit. You said it, copilot!
        log.broca_shuttlecraft.info("Shuttlecraft ready.")

        while True:

            # ask the starship for the next thing to play if there is one
            to_starship.send({"action": "idle"})

            # just masturbate for a little while
            time.sleep(0.25)
            seconds_idle += 0.25

            # check the queue for anything new and pop one out
            if to_starship.poll():

                # if there was some communication in the pipe, probably is the next sound to play
                comms = to_starship.recv()
                log.broca_shuttlecraft.debug("Shuttlecraft received: %s", comms)

                # graceful shutdown
                if comms["action"] == "selfdestruct":

                    # make the subprocess exit
                    log.broca_shuttlecraft.info("Shuttlecraft self destruct activated.")
                    sys.exit()

                elif comms["action"] == "stop_audio":
                    
                    # IMMEDIATE AUDIO STOP for interruptions
                    # Stop the current stream immediately to prevent feedback
                    if pya_stream.is_active():
                        log.broca_shuttlecraft.info("STOP AUDIO - Interruption detected")
                        pya_stream.stop_stream()
                        # Signal back that audio has been stopped
                        to_starship.send({"action": "pause_wernicke_end"})

                elif comms["action"] == "playwav":

                    # if seconds_idle is greater than the threshold, play a sound to get the speaker started back up
                    if seconds_idle > seconds_idle_to_play_presound:
                        log.broca_shuttlecraft.debug("Beep! (idle %ss)", seconds_idle)
                        pya_stream.stop_stream()
                        wav_data = wave.open("sounds/beep.wav")
                        pya_stream.start_stream()

                        # wait until the stream flips to not active which means the beep is done
                        while pya_stream.is_active():
                            time.sleep(0.2)

                    # the volume gets set before each sound is played
                    # mixer.setvolume(comms["vol"])
                    # pyalsaaudio died so we have to forking fork
                    if comms["vol"] != last_volume:
                        log.broca_shuttlecraft.debug("Setting volume to %s", comms["vol"])
                        os.system(f'amixer -q cset numid=1 {comms["vol"]}%')
                        last_volume = comms["vol"]

                    # DIRECT WERNICKE COORDINATION - SHARED MEMORY
                    # if we need to pause wernicke, set shared memory flag now
                    if comms["pause_wernicke"]:
                        if audio_coordination is not None:
                            audio_coordination.value = 1  # Pause wernicke immediately
                        # small delay to ensure wernicke sees the flag before we start playing
                        time.sleep(0.01)  # Much shorter delay - just 10ms

                    # stop stream, open new wav file, and start the stream back up
                    log.broca_shuttlecraft.info("Play %s", comms["wavfile"])
                    pya_stream.stop_stream()
                    wav_data = wave.open(comms["wavfile"])
                    pya_stream.start_stream()

                    # wait until the stream flips to not active which means the sound is done
                    while pya_stream.is_active():
                        time.sleep(0.2)

                    # DIRECT WERNICKE COORDINATION - SHARED MEMORY
                    # if we paused wernicke, clear shared memory flag now
                    if comms["pause_wernicke"]:
                        if audio_coordination is not None:
                            audio_coordination.value = 0  # Resume wernicke immediately

                    # reset this counter
                    seconds_idle = 0.0

                elif comms["action"] == "pause":

                    # sleep here for the duration of the pause
                    log.broca_shuttlecraft.debug("Pause %s", comms["pause_duration"])
                    time.sleep(comms["pause_duration"])
                    log.broca_shuttlecraft.debug("Pause %s END", comms["pause_duration"])

                    # add to counter
                    seconds_idle += comms["pause_duration"]

            else:

                # nothing is playing, so increment the seconds_idle var
                seconds_idle += 0.25

                # if we've been idle for a while, choose a random breathing sound and play it
                if seconds_idle > seconds_to_breathe:
                    breath = sounds_db.get_random_sound(collection_name='breathing')
                    if breath is not None:
                        log.broca_shuttlecraft.debug("Breathing")

                        # breaths get played at 100 max volume
                        if last_volume != 100:
                            os.system('amixer -q cset numid=1 100%')
                            last_volume = 100

                        pya_stream.stop_stream()
                        wav_data = wave.open(breath.file_path)
                        pya_stream.start_stream()

                        # wait until the stream flips to not active which means the sound is done
                        while pya_stream.is_active():
                            time.sleep(0.25)

                        log.broca_shuttlecraft.debug("Breathing END")
                        seconds_idle = 0.0

                    # set cycles_to_breathe to a random number of seconds between 0.5 and 1.5 for the next time
                    seconds_to_breathe = 0.5 + random.random()

# Instantiate
broca = Broca()

# Note: Subprocess will be started in run() method after shared memory injection

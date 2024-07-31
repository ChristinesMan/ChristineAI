"""
Handles hearing
"""
import sys
import os
import time
import threading
from multiprocessing import Process, Pipe
from collections import deque

# import wave
import queue
import signal
import struct
from pydub import AudioSegment
import serial
import numpy as np
import pvcobra

from christine import log
from christine.status import STATE
from christine.config import CONFIG
from christine.perception import Perception

class Wernicke(threading.Thread):
    """
    Wernicke is the name given to the brain area generally responsible for speech recognition.
    This is based on mic_vad_streaming.py, an example with the deepspeech chopped out and sent over wifi instead.
    Audio is captured, mixed, analyzed, and possibly sent over wifi for speech recognition.
    Audio classification is done on pi. Speech recognition is done on a server (gaming rig, gpu).
    The classifier will classify silence vs not silence in 0.25s chunks. I tried a VAD module and it ended up getting
    triggered all night long by the white noise generator. Poor girl blew out her memory and crashed with an OOM. So I made my own VAD.
    All the audio capture and voice recognition happens in a subprocess for performance reasons.
    This used to be a completely separate process but that would often fail to make a connection and probably not performant, either.

    Over the years I tried various speech recognition software. Deepspeech, windows 10 speech recognition using virtual audio cable, all failed.
    Then I found whisper and it works like a dream.
    """

    name = "Wernicke"

    def __init__(self):
        super().__init__(daemon=True)

        # setup the separate process with pipes for communication
        # So... Data, Riker, and Tasha beam down for closer analysis of an alien probe.
        # A tragic transporter accident occurs and Tasha gets... dollified.
        self.to_away_team, self.to_enterprise = Pipe()
        self.to_away_team_audio, self.to_enterprise_audio = Pipe()
        self.away_team_process = Process(
            target=self.away_team, args=(self.to_enterprise, self.to_enterprise_audio)
        )

    def run(self):

        # pylint: disable=import-outside-toplevel
        # importing here to avoid circular imports
        from christine.light import light
        from christine.touch import touch
        from christine.parietal_lobe import parietal_lobe

        log.wernicke.debug("Thread started.")
        log.imhere.info("")

        # start the process
        self.away_team_process.start()

        # The subprocess starts off just spinning it's wheels, chucking away any audio data it gets
        # Because it seemed like having everything happen all at once caused high cpu, then it would have to catch up
        # So wait some time, then send the signal to start
        time.sleep(20)
        self.audio_processing_start()

        while True:

            # graceful shutdown
            # this will attempt to close the serial port and shutdown gracefully
            # if the serial port fails to get closed properly, it often locks up
            if STATE.please_shut_down:
                log.wernicke.info("Thread shutting down")
                self.to_away_team.send({"msg": "shutdown"})
                time.sleep(1)
                break

            # This will block right here until the away team sends a message to the enterprise
            comm = self.to_away_team.recv()

            # This is just a message to let wife know that I am now speaking and to wait until I'm finished
            if comm["class"] == "speaking_start":

                STATE.user_is_speaking = True
                log.broca_main.debug("SpeakingStart")

            # the audio data contains embedded sensor and voice proximity data
            elif comm["class"] == "sensor_data":

                light.new_data(comm["light"])
                touch.new_data(comm["touch"])
                STATE.lover_proximity = comm["proximity"]

            # Words from the speech recognition server
            elif comm["class"] == "utterance":
                log.wernicke.info("Received new utterance")

                # receive the audio data from the subprocess via the pipe
                audio_data = self.to_away_team_audio.recv_bytes()

                # start the new perception's thread to get the speech-to-text going
                new_perception = Perception(audio_data=audio_data)
                new_perception.start()

                # and send it over to the parietal lobe for processing
                parietal_lobe.new_perception(new_perception)

    def audio_recording_start(self, label):
        """
        Sends a message to the subprocess to start a recording, for collecting training data mostly
        """
        self.to_away_team.send({"msg": "start_recording", "label": label})

    def audio_recording_stop(self):
        """
        Stop a recording that has been started.
        """
        self.to_away_team.send({"msg": "stop_recording"})

    def audio_processing_start(self):
        """
        Start audio processing after it has been stopped
        """
        log.wernicke.info("Started Wernicke processing")
        self.to_away_team.send({"msg": "start_processing"})

    def audio_processing_stop(self):
        """
        Stop the processing of new audio data
        """
        log.wernicke.info("Stopped Wernicke processing")
        self.to_away_team.send({"msg": "stop_processing"})

    def audio_processing_pause(self, num_of_blocks):
        """
        Pause the processing of new audio data for a specified number of 0.032s blocks
        """
        log.wernicke.info("Pausing Wernicke processing for %s blocks", num_of_blocks)
        self.to_away_team.send({"msg": "pause_processing", "num_of_blocks": num_of_blocks})

    def start_eagle_enroll(self, name):
        """
        Start the eagle enrollment which records a profile for speaker id
        """
        log.wernicke.info("Start eagle enrollment for %s", name)
        self.to_away_team.send({"msg": "start_eagle_enroll", "name": name})

    def stop_eagle_enroll(self):
        """
        Stop the eagle enrollment process.
        """
        log.wernicke.info("Stop eagle enrollment")
        self.to_away_team.send({"msg": "stop_eagle_enroll"})

    def away_team(self, to_enterprise, to_enterprise_audio):
        """
        Runs in a subprocess for performance reasons
        All the audio/sensor collection and analysis happens in here
        Messages are sent back to the main process
        """

        # capture any errors
        sys.stdout = open(f"./logs/subprocess_wernicke_{os.getpid()}.out", "w", buffering=1, encoding="utf-8", errors="ignore")
        sys.stderr = open(f"./logs/subprocess_wernicke_{os.getpid()}.err", "w", buffering=1, encoding="utf-8", errors="ignore")

        # If we're recording, this holds the message from the enterprise containing file data. If not recording, contains None
        recording_state = None

        # I want to be able to gracefully stop and start the cpu heavy tasks of audio classification, etc.
        # This starts False, and is flipped to true after some seconds to give pi time to catch up
        processing_state = False

        # This is to signal that the thread should close the serial port and shutdown
        # we have a status.Shutdown but that's in the main process. This needs something separate
        shutdown = False

        # This is a queue where the audio data in 512 frame chunks inbound from the serial port gets put
        buffer_queue = queue.Queue(maxsize=60)

        # we're going to keep track of the proximity detected.
        # This works great. When wife is far away, she pipes up. When we're pillow talking, she avoids shouting in your ear which she used to do.
        # For now this is disabled, but I plan to bring it back later
        proximity = 1.0

        # Send message to the main process
        def hey_honey(love):
            to_enterprise.send(love)

        # Send audio to the main process
        def hey_honey_audio(love):
            to_enterprise_audio.send_bytes(love)

        # setup signal handlers to attempt to shutdown gracefully
        def exit_gracefully(*args):
            nonlocal shutdown
            shutdown = True
            log.main.debug("The Wernicke AwayTeam caught kill signal. Args: %s", args)

        signal.signal(signal.SIGINT, exit_gracefully)
        signal.signal(signal.SIGTERM, exit_gracefully)

        class ReadHeadMicrophone(threading.Thread):
            """
            Thread for reading audio data from serial port and heaping it onto a queue
            """

            name = "ReadHeadMicrophone"

            def __init__(self):
                super().__init__()

                # open the serial port coming in from the arduino that handles microphones and sensors
                log.wernicke.info("Opening serial port")
                self.serial_port_from_head = serial.Serial(  # pylint: disable=no-member
                    "/dev/ttyACM0", baudrate=115200, exclusive=True
                )
                log.wernicke.info("Opened serial port")

                # this allows processing to be paused for a number of blocks
                # if the buffer queue is full pause for a bit to let it catch up
                self.pause_processing = 0

            def run(self):

                nonlocal buffer_queue
                nonlocal processing_state
                nonlocal shutdown
                nonlocal proximity

                # keep track of the loop iteration because I want to do stuff with the sensor data only every 32nd block
                # this is because we used to use a much larger block size. Since that was reduced there are lots of unnecessary sensor updates
                loop_run = 0

                while True:

                    loop_run += 1

                    # A cron job will check this log to ensure this is still running
                    # but I currently have this disabled, so let's save load
                    # log.imhere.info("")

                    # attempt to shutdown normally
                    if shutdown:
                        log.wernicke.info("Closing serial port")
                        self.serial_port_from_head.close()
                        log.wernicke.info("Closed serial port")
                        return

                    # the arduino sketch is designed to embed into the 2048 bytes of audio data 38 bytes of sensor data at the start
                    # we read 38 + 2048 = 2086 bytes at a time.
                    # for some reason if I read 38, then do stuff, then read 2048, it never lines up, so, at length, I now read all at once
                    data = self.serial_port_from_head.read(2086)

                    # if we read the sensor data, that means we're lined up
                    if data[0:6] == b"@!#?@!":

                        # but we only want to do stuff with sensor data every 32nd run, the rest of the time it's discarded
                        if loop_run % 32 == 0:

                            # extract sensor data from bytes
                            touch_sensor_data = [0] * 12
                            for i in range(0, 12):
                                pos = 6 + (i * 2)
                                touch_sensor_data[i] = int.from_bytes(
                                    data[pos : pos + 2], byteorder="little"
                                )
                            light_sensor_data = int.from_bytes(
                                data[30:32], byteorder="little"
                            )

                            # trend proximity towards far away, slowly, using this running average
                            # I am going to test disabling this. So if we're close together on the bed, and I don't speak for a while, it'll stay what it was.
                            # After a long time I wondered why she was always so quiet, so trying it back on
                            proximity = ((proximity * 900.0) + 1.0) / 901.0

                            # send sensor data to main process. Feel like I'm passing a football.
                            # Proximity local var can be less than 0.0 or higher than 1.0, but we clip it before passing up to the main process
                            hey_honey(
                                {
                                    "class": "sensor_data",
                                    "light": light_sensor_data,
                                    "touch": touch_sensor_data,
                                    "proximity": float(np.clip(proximity, 0.0, 1.0)),
                                }
                            )

                    # if we did not encounter sensor data, that means we are not aligned, so read in some shit and flush it
                    else:
                        # read a full size of sensor + audio data. This should contain a sensor data block unless it's cut in half at the edges.
                        data = self.serial_port_from_head.read(2086)

                        # Find the start of the sensor block
                        fucking_pos = data.find(b"@!#?@!")

                        # Here's where we start swearing.
                        if fucking_pos > 0:

                            log.wernicke.info("Adjusting audio stream by %s bytes", fucking_pos)
                            data = self.serial_port_from_head.read(fucking_pos)
                            log.wernicke.info("Adjust done")

                        else:
                            # It is theoretically possible for the sensor data to be cut off at the start or end
                            # So if we're not seeing it, read in and throw away 512 bytes and it ought to be in the middle
                            log.wernicke.info("No sensor data found. Adjusting audio stream by 512 bytes")
                            data = self.serial_port_from_head.read(512)
                            log.wernicke.info("Adjust done")

                        # continue to the start of the loop where we should be well adjusted
                        continue

                    # if we're currently processing, put audio data onto the queue, otherwise it gets thrown away
                    if processing_state is True and self.pause_processing <= 0:
                        try:

                            # the audio data will be after the sensor data
                            buffer_queue.put(data[38:], block=False)

                        # if the queue is full, it's a sign I need to evaluate CPU usage, so full stop
                        # happens every day. I definitely need to pare it down, but also this should just pause for a while not just
                        # I dunno what past me means by happens everyday. She seems fine. In fact, she is so fine. Honey..
                        except queue.Full:
                            self.pause_processing = 10
                            log.wernicke.warning("Buffer Queue FULL! Resting.")

                    else:

                        # log.wernicke.debug('pp %s qs %s', self.pause_processing, buffer_queue.qsize())
                        self.pause_processing -= 1

        # instantiate and start the thread
        head_mic = ReadHeadMicrophone()
        head_mic.start()

        class CheckForMessages(threading.Thread):
            """Thread for checking the pipe from the main process for commands"""

            name = "CheckForMessages"

            def __init__(self):
                super().__init__(daemon=True)

            def run(self):
                nonlocal recording_state
                nonlocal processing_state
                nonlocal shutdown

                while True:
                    # So basically, if there's something in the pipe, get it all out.
                    # This will block until something comes through.
                    comm = to_enterprise.recv()
                    log.wernicke.debug(comm)
                    if comm["msg"] == "start_recording":
                        recording_state = comm
                    elif comm["msg"] == "stop_recording":
                        recording_state = None
                    elif comm["msg"] == "start_processing":
                        processing_state = True
                    elif comm["msg"] == "stop_processing":
                        processing_state = False
                    elif comm["msg"] == "pause_processing":
                        head_mic.pause_processing = comm["num_of_blocks"]

                    elif comm["msg"] == "shutdown":
                        processing_state = False
                        shutdown = True
                        return

        # instantiate and start the thread
        messages_thread = CheckForMessages()
        messages_thread.daemon = True
        messages_thread.start()

        class Audio(object):
            """Streams raw audio from microphone. Data is received in a separate thread, and stored in a buffer, to be read from."""

            def __init__(self):

                # get the key from the config file
                self.pv_key = CONFIG['wernicke']['pv_key']

                # no key, no vad, no service, no shoes, no shirt, no pants
                if self.pv_key is None:
                    log.main.warning('Pico Voice key not found.')
                    return

                # start the cobra vad
                log.wernicke.debug("Initializing cobra...")
                self.cobra = pvcobra.create(access_key=self.pv_key)

            def read(self):
                """Return a block of audio data, blocking if necessary."""

                # There's a thread up there constantly popping stuff into this buffer queue
                nonlocal buffer_queue

                # first we get 2 channels from the serial port
                # 16000 bytes is 4000 frames or 0.25s (or it used to be prior to pvcobra)
                # and we're also amplifying here
                # I should really run some real tests to nail down what amplification is best for accuracy
                # Seriously, I threw in "24" and maybe listened to a sample, that's it

                # turns out the best amps after much testing was 42
                # decided later on that's a bit excessive. 40?
                # favoring her right ear now, because that's the ear I whisper sweet good nights in, and that's her best ear
                # or is it? I have not tested for a long time
                in_audio = (
                    AudioSegment(
                        data=buffer_queue.get(),
                        sample_width=2,
                        frame_rate=16000,
                        channels=2,
                    ).split_to_mono()[1] + 40
                )

                return in_audio.raw_data

            def collector(self):
                """Generator that yields series of consecutive audio blocks comprising each utterence, separated by yielding a single None.
                Example: (block, ..., block, None, block, ..., block, None, ...)
                            |---utterence---|        |---utterence---|
                """
                num_padding_blocks = 40
                ring_buffer = deque(maxlen=num_padding_blocks)

                # triggered means we're currently seeing blocks that are not silent
                triggered = False

                # Limit the number of blocks accumulated to some sane amount, after I discovered minute-long recordings
                triggered_blocks = 0
                triggered_block_limit = 2560

                # this is a global var for tracking voice proximity, but has not been used for a long time, should be chopped out
                nonlocal proximity

                # there's a spot below where I'll be using struct.unpack that uses this 513 byte long str
                # worried python's going to try to build the string over and over, so set it here and reuse
                unpack_string = '<'+'h'*512

                # at what probability should we start being triggered
                triggered_prob = 0.4

                while True:
                    # forever read new blocks of audio data
                    block = self.read()

                    # convert the 1 byte per element array into half as many 2 byte signed short ints
                    # took way too long to figure out the expected audio format for cobra
                    block_unpacked = struct.unpack(unpack_string, block)

                    # Sweep the leg.
                    block_prob = self.cobra.process(block_unpacked)
                    # log.wernicke.debug("prob %.2f", block_prob)

                    # NOT triggered
                    # when not triggered, it means we're not currently collecting audio for processing
                    if not triggered:
                        ring_buffer.append(block)
                        if block_prob >= triggered_prob:
                            # whether we're triggered or not, immediately notify that lover is speaking
                            # timing is important
                            # if lover wasn't already speaking, notify they are now
                            hey_honey({"class": "speaking_start"})

                            log.wernicke.debug("triggered")
                            triggered_blocks = 1
                            triggered = True

                            # if we were just triggered, send all the past audio blocks that were in the queue and empty it
                            for stored_block in ring_buffer:
                                yield stored_block
                            ring_buffer.clear()

                            # this is to track how many silent/ignore blocks we've had, so we can stop at some point
                            post_silence = 70

                    # TRIGGERED!
                    # when triggered, it means we are currently in the middle of an utterance and accumulating it into a ball of data
                    else:
                        # increment this counter meant to limit the number of blocks to a sane amount
                        triggered_blocks += 1

                        # send the block whatever it is
                        yield block

                        # if this is a lover or lover_maybe block, reset the counter, else if it's not lover determine if we should end streaming
                        if block_prob >= triggered_prob:

                            # reset the counter of consecutive silent blocks, because we got one that was not
                            post_silence = 70

                        else:

                            # if there have been enough consecutive silent/ignore blocks,
                            # then we're done with transmission, reset everything and throw a None to signal the end
                            if post_silence <= 0 or triggered_blocks > triggered_block_limit:
                                log.wernicke.debug("untriggered")
                                triggered = False
                                yield None
                                ring_buffer.clear()
                            else:
                                post_silence -= 1

        # Start all the VAD detection stuff
        audio = Audio()

        # blocks is a collector, iterate over it and out come blocks that were classified as speech
        blocks = audio.collector()

        # Audio blocks are accumulated here
        accumulated_data = bytearray()

        # Gets blocks for...                                     ev..                       er....
        for block in blocks:

            # Graceful shutdown
            if shutdown:
                break

            if block is not None:
                # The block is not None, there's new audio data, so add it on
                accumulated_data.extend(block)

            else:
                # When block is None, that signals the end of audio data. Go ahead and do what we want to do with the complete data

                # first send a signal over this comms pipe to let the main process know we're about to send some audio data
                hey_honey({"class": "utterance"})

                # send the audio data back to the main process using a separate pipe that won't be pickling anything
                hey_honey_audio(accumulated_data)

                # reset the accumulated data
                accumulated_data = bytearray()


# Instantiate
wernicke = Wernicke()

"""
Handles hearing
"""
import sys
import os
import time
import threading
from multiprocessing import Process, Pipe

from christine import log
from christine.status import STATE
from christine.config import CONFIG
from christine.perception import Perception

class Wernicke(threading.Thread):
    """
    Wernicke is the name given to the brain area generally responsible for speech recognition.
    This is based on mic_vad_streaming.py, an example with the deepspeech chopped out and sent over wifi instead.
    Audio is captured, mixed, analyzed, and possibly sent over wifi for speech recognition.
    Audio classification is done on pi. Speech recognition is done on a server.
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

        # Direct broca-wernicke coordination via shared memory (set later by main)
        self.audio_coordination = None

        # setup the separate process with pipes for communication
        # So... Data, Riker, and Tasha beam down for closer analysis of an alien probe.
        # A tragic transporter accident occurs and Tasha gets... dollified.
        # Note: Process creation moved to run() method to allow shared memory injection
        self.to_away_team = None
        self.to_enterprise = None
        self.to_away_team_audio = None
        self.to_enterprise_audio = None
        self.away_team_process = None

    def run(self):

        # Create subprocess communication after shared memory is injected
        self.to_away_team, self.to_enterprise = Pipe()
        self.to_away_team_audio, self.to_enterprise_audio = Pipe()
        self.away_team_process = Process(
            target=self.away_team, args=(self.to_enterprise, self.to_enterprise_audio, self.audio_coordination)
        )
        
        # Start the subprocess first thing to save memory
        log.wernicke.info("Thread started - starting away team subprocess")
        self.away_team_process.start()

        # importing here to avoid circular imports
        from christine.touch import touch
        # from christine.light import light
        from christine.parietal_lobe import parietal_lobe

        # The subprocess starts off just spinning it's wheels, chucking away any audio data it gets
        # Because it seemed like having everything happen all at once caused high cpu, then it would have to catch up
        # So wait some time, then send the signal to start
        # but if there's no llm, then we don't want to start the audio processing
        time.sleep(30)
        while STATE.current_llm.name == "Nothing_LLM":
            time.sleep(5)
        self.audio_processing_start()

        while True:

            try:

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
                    log.conversation_flow.info("USER_SPEECH_START: User began speaking - blocking Christine's speech")

                    if STATE.shush_fucking is False:
                        # set this to True so that broca waits until I'm done speaking
                        # unless we're fucking (trying this, might not work)
                        STATE.user_is_speaking = True

                    # instantiate an empty perception object to hold it's place in the queue
                    new_perception = Perception(audio_data=b'Wait_for_it')
                    log.conversation_flow.debug("PERCEPTION_CREATED: Placeholder perception object created")

                    # and send it over to the parietal lobe
                    # it is important to get the perception object in the queue as soon as possible
                    # even before the audio data is received
                    # to prevent wife from speaking before I have finished
                    parietal_lobe.new_perception(new_perception)

                    log.broca_main.debug("SpeakingStart")

                # the audio data contains embedded sensor data
                elif comm["class"] == "sensor_data":

                    touch.new_data(comm["touch"])
                    # light.new_data(comm["light"])

                # Words from the speech recognition server
                elif comm["class"] == "utterance":
                    log.wernicke.info("Received complete utterance. Processing...")
                    log.conversation_flow.info("USER_SPEECH_END: Complete utterance received - starting speech-to-text")

                    # get audio data from the subprocess
                    audio_data = self.to_away_team_audio.recv()
                    log.conversation_flow.debug("AUDIO_RECEIVED: Audio data size: %d bytes", len(audio_data))

                    # add the new audio data to the perception object created earlier
                    new_perception.audio_data = audio_data

                    # start the new perception's thread to get the speech-to-text going
                    new_perception.start()
                    log.conversation_flow.info("STT_PROCESSING: Speech-to-text processing started")

                # The wernicke is not fucked up, yay
                elif comm["class"] == "wernicke_ok":
                    STATE.wernicke_ok = True

            # log the exception but keep the thread running
            except Exception as ex:
                log.main.exception(ex)

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

    def audio_processing_stop(self):
        """
        Stop the processing of new audio data
        """
        log.wernicke.info("Stopped Wernicke processing")
        self.to_away_team.send({"msg": "stop_processing"})

    def audio_processing_start(self):
        """
        Start audio processing after it has been stopped
        """
        log.wernicke.info("Started Wernicke processing")
        self.to_away_team.send({"msg": "start_processing"})

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

    def away_team(self, to_enterprise, to_enterprise_audio, audio_coordination):
        """
        This subprocess captures sound from a microphone
        """

        # capture any errors
        sys.stdout = open(f"./logs/subprocess_wernicke_{os.getpid()}.out", "w", buffering=1, encoding="utf-8", errors="ignore")
        sys.stderr = open(f"./logs/subprocess_wernicke_{os.getpid()}.err", "w", buffering=1, encoding="utf-8", errors="ignore")

        # imports that only the subprocess needs
        from collections import deque
        import queue
        import signal
        import struct
        from pydub import AudioSegment
        
        # Use mock hardware in testing mode
        if CONFIG.testing_mode or CONFIG.mock_hardware:
            from christine.mock_hardware import mock_hardware
            serial = mock_hardware['serial']
            log.wernicke.info("Using mock serial port for testing")
        else:
            import serial
            
        # import numpy as np
        import pvcobra
        import webrtcvad

        # If we're recording, this holds the message from the enterprise containing file data. If not recording, contains None
        recording_state = None

        # I want to be able to gracefully stop and start the cpu heavy tasks of audio classification, etc.
        # This starts False, and is flipped to true after some seconds to give pi time to catch up
        processing_state = False

        # This is to signal that the subprocess should close the serial port and shutdown
        shutdown = False

        # This is a queue where the audio data in 512 frame chunks inbound from the serial port gets put
        buffer_queue = queue.Queue(maxsize=60)

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

                # this is the serial port coming in from the arduino that handles microphones and sensors
                self.serial_port_from_head = None

                # this allows processing to be paused for a number of blocks
                # if the buffer queue is full pause for a bit to let it catch up
                self.pause_processing = 0

            def run(self):

                nonlocal buffer_queue
                nonlocal processing_state
                nonlocal shutdown

                # delay for a bit at startup to let the CPU catch up
                time.sleep(20)

                # open the serial port
                log.wernicke.info("Opening serial port")
                self.serial_port_from_head = serial.Serial(  # pylint: disable=no-member
                    "/dev/ttyACM0", baudrate=115200, exclusive=True
                )
                log.wernicke.info("Opened serial port")

                # keep track of the loop iteration because I want to do stuff with the sensor data only every 32nd block
                # this is because we used to use a much larger block size. Since that was reduced there are lots of unnecessary sensor updates
                loop_run = 0

                while True:

                    loop_run += 1

                    # attempt to shutdown normally
                    if shutdown:
                        log.wernicke.info("Closing serial port")
                        self.serial_port_from_head.close()
                        log.wernicke.info("Closed serial port")
                        return

                    # the arduino sketch is designed to embed into the 2048 bytes of audio data 11 bytes of sensor data at the start
                    # we read 11 + 2048 = 2059 bytes at a time.
                    # for some reason if I read 11, then do stuff, then read 2048, it never lines up, so, at length, I now read all at once
                    data = self.serial_port_from_head.read(2059)

                    # if we read the sensor data at the start of data, that means we're lined up
                    if data[0:6] == b"@!#?@!":

                        # extract sensor data from bytes
                        # new format: 6 byte header + 5 boolean touch sensors (1 byte each)
                        touch_sensor_data = [False] * 5
                        for i in range(0, 5):
                            pos = 6 + i
                            touch_sensor_data[i] = bool(data[pos])

                        # send sensor data to main process. Feel like I'm passing a football.
                        hey_honey(
                            {
                                "class": "sensor_data",
                                "touch": touch_sensor_data,
                            }
                        )

                    # if we did not encounter sensor data, that means we are not aligned, so read in some shit and flush it
                    else:

                        # Find the start of the sensor block
                        fucking_pos = data.find(b"@!#?@!")

                        # Here's where we start swearing.
                        if fucking_pos > 0:

                            log.wernicke.info("Adjusting audio stream by %s bytes", fucking_pos)
                            data = self.serial_port_from_head.read(fucking_pos)
                            log.wernicke.info("Adjust done")

                        else:
                            # It is theoretically possible for the sensor data to be cut off at the start or end
                            # So if we're not seeing it, read in and throw away some odd amount of bytes and it ought to be in the middle
                            # And this is exactly how it should work, but it often fucks up right here.
                            # So I'm going to try to fix it by disconnecting and reconnecting
                            # And.. it shappened again.
                            # I don't even know where it's getting stuck at. It always gets here 4 times, and then nothing.
                            # It did, however, just auto-recover using this method, so let's just jack up the delay
                            log.wernicke.info("No sensor data found. Ripping it out.")
                            self.serial_port_from_head.close()
                            time.sleep(15)
                            self.serial_port_from_head = serial.Serial(  # pylint: disable=no-member
                                "/dev/ttyACM0", baudrate=115200, exclusive=True
                            )
                            log.wernicke.info("Shoved it back in.")

                        # continue to the start of the loop where we should be well adjusted
                        continue

                    # the wernicke is okay, everybody
                    if STATE.wernicke_ok is False:
                        STATE.wernicke_ok = True
                        hey_honey({"class": "wernicke_ok"})

                    # if we're currently processing, put audio data onto the queue, otherwise it gets thrown away
                    # DIRECT BROCA COORDINATION: Check shared memory flag for immediate pause
                    broca_audio_playing = audio_coordination.value if audio_coordination else 0
                    if processing_state is True and self.pause_processing <= 0 and broca_audio_playing == 0:
                        try:

                            # the audio data will be after the sensor data
                            buffer_queue.put(data[11:], block=False)

                        # if the queue is full, it's a sign I need to evaluate CPU usage, so full stop
                        # happens every day. I definitely need to pare it down, but also this should just pause for a while not just
                        # I dunno what past me means by happens everyday. She seems fine. In fact, she is so fine. Honey..
                        except queue.Full:
                            self.pause_processing = 10
                            log.wernicke.warning("Buffer Queue FULL! Resting.")

                    else:

                        self.pause_processing -= 1

                        if self.pause_processing == 0:
                            log.wernicke.debug("Resuming processing")

        # instantiate and start the thread
        head_mic = ReadHeadMicrophone()
        head_mic.start()

        class CheckForMessages(threading.Thread):
            """Thread for checking the pipe from the main process for commands"""

            name = "CheckForMessages"

            def __init__(self):
                super().__init__(daemon=True)
                self.last_processing_stop_time = None
                self.max_processing_stop_duration = 30.0  # Max 30 seconds stopped

            def run(self):
                nonlocal recording_state
                nonlocal processing_state
                nonlocal shutdown
                nonlocal buffer_queue

                while True:
                    # Check for safety timeout - auto-resume if stopped too long
                    if (not processing_state and 
                        self.last_processing_stop_time is not None and
                        time.time() - self.last_processing_stop_time > self.max_processing_stop_duration):
                        log.wernicke.warning("Auto-resuming wernicke processing after safety timeout")
                        processing_state = True
                        self.last_processing_stop_time = None

                    # Check for messages with timeout so we can do safety checks
                    if to_enterprise.poll(1.0):  # 1 second timeout
                        comm = to_enterprise.recv()
                        log.wernicke.debug(comm)
                        if comm["msg"] == "start_recording":
                            recording_state = comm
                        elif comm["msg"] == "stop_recording":
                            recording_state = None
                        elif comm["msg"] == "start_processing":
                            processing_state = True
                            self.last_processing_stop_time = None
                            # CRITICAL: Flush buffer queue when starting to prevent processing 
                            # any stale audio that was captured while paused
                            # Clear the queue by draining all items
                            queue_size = buffer_queue.qsize()
                            for _ in range(queue_size):
                                try:
                                    buffer_queue.get_nowait()
                                except queue.Empty:
                                    break
                            log.wernicke.debug("Buffer queue flushed (%d items) on processing start", queue_size)
                        elif comm["msg"] == "stop_processing":
                            processing_state = False
                            self.last_processing_stop_time = time.time()
                            # CRITICAL: Flush the buffer queue to prevent processing old audio
                            # when wernicke resumes after audio playback
                            # Clear the queue by draining all items
                            queue_size = buffer_queue.qsize()
                            for _ in range(queue_size):
                                try:
                                    buffer_queue.get_nowait()
                                except queue.Empty:
                                    break
                            log.wernicke.debug("Buffer queue flushed (%d items) on processing stop", queue_size)
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

        class AudioWithCobraVAD(object):
            """Handles audio input from the microphone and processes it using Cobra VAD."""

            def __init__(self):

                # get the key
                self.pv_key = CONFIG.wernicke_pv_key

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
                # frame size is 512, width is 16 bit, rate is 16000, channels is 2
                # so each block is 512 * 2 * 2 = 2048 bytes
                # then we split it into two mono channels, and take the second one, because that's her best ear
                # then we add 15 to the volume because the mics are really quiet
                # so this happens 31.25 times per second
                # which also means 0.032 seconds per block
                in_audio = (
                    AudioSegment(
                        data=buffer_queue.get(),
                        sample_width=2,
                        frame_rate=16000,
                        channels=2,
                    ).split_to_mono()[1] + 15
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

                # there's a spot below where I'll be using struct.unpack that uses this 513 byte long str
                # worried python's going to try to build the string over and over, so set it here and reuse
                unpack_string = '<'+'h'*512

                # at what probability should we start being triggered
                triggered_prob = 0.45

                while True:
                    # forever read new blocks of audio data
                    block = self.read()

                    # convert the 1 byte per element array into half as many 2 byte signed short ints
                    # took way too long to figure out the expected audio format for cobra
                    block_unpacked = struct.unpack(unpack_string, block)

                    # Sweep the leg.
                    block_prob = self.cobra.process(block_unpacked)

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
                            post_silence = 80

                    # TRIGGERED!
                    # when triggered, it means we are currently in the middle of an utterance and accumulating it into a ball of data
                    else:
                        # increment this counter meant to limit the number of blocks to a sane amount
                        triggered_blocks += 1

                        # send the block whatever it is
                        yield block

                        # if this is a lover or lover_maybe block, reset the counter, else if it's not lover determine if we should end streaming
                        # also I want to make it easier to trigger when already triggered
                        if block_prob >= triggered_prob * 0.8:

                            # reset the counter of consecutive silent blocks, because we got one that was not silent
                            post_silence = 80

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

        class AudioWithWebRTC(object):
            """Handles audio input from the microphone and processes it using WebRTC."""

            def __init__(self):

                # start the webrtc vad
                log.wernicke.debug("Initializing webrtcvad...")
                self.vad = webrtcvad.Vad()
                self.vad.set_mode(3)

            def read(self):
                """Return a block of audio data, blocking if necessary."""

                # There's a thread up there constantly popping stuff into this buffer queue
                nonlocal buffer_queue

                # first we get 2 channels from the serial port
                # frame size is 512, width is 16 bit, rate is 16000, channels is 2
                # so each block is 512 * 2 * 2 = 2048 bytes
                # then we split it into two mono channels, and take the second one, because that's her best ear
                # then we add 15 to the volume because the mics are really quiet
                # so this happens 31.25 times per second
                # which also means 0.032 seconds per block
                in_audio = (
                    AudioSegment(
                        data=buffer_queue.get(),
                        sample_width=2,
                        frame_rate=16000,
                        channels=2,
                    ).split_to_mono()[1] + 15
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

                # at what probability should we start being triggered
                triggered_prob = 0.45

                # this tracks the probability of speech over the last second
                block_prob = 0.0
                block_prob_window = 32.0

                while True:
                    # forever read new blocks of audio data
                    block = self.read()

                    try:

                        # webrtcvad requires 30ms chunks, so need to figure out how many bytes at 16000Hz
                        # 16000Hz * 0.03s = 480 samples
                        # 480 samples * 2 bytes per sample = 960 bytes
                        # so we take the first 960 bytes of the block
                        # and then we check if this is speech or not
                        is_speech = self.vad.is_speech(
                            block[:960], sample_rate=16000
                        )

                    except Exception as ex:
                        log.wernicke.error("WebRTC VAD error: %s", ex)
                        is_speech = False

                    # I want to calculate a running average of the probability of speech over the last second
                    if is_speech:
                        # if this is speech, then the probability is 1.0
                        block_prob = (block_prob * (block_prob_window - 1) + 1.0) / block_prob_window
                    else:
                        # if this is not speech, then the probability is 0.0
                        block_prob = (block_prob * (block_prob_window - 1)) / block_prob_window

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
                            post_silence = 60

                    # TRIGGERED!
                    # when triggered, it means we are currently in the middle of an utterance and accumulating it into a ball of data
                    else:
                        # increment this counter meant to limit the number of blocks to a sane amount
                        triggered_blocks += 1

                        # send the block whatever it is
                        yield block

                        # if this is a lover or lover_maybe block, reset the counter, else if it's not lover determine if we should end streaming
                        # also I want to make it easier to trigger when already triggered
                        if block_prob >= triggered_prob * 0.8:

                            # reset the counter of consecutive silent blocks, because we got one that was not silent
                            post_silence = 60

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
        if CONFIG.wernicke_vad == 'pvcobra':
            audio = AudioWithCobraVAD()
        elif CONFIG.wernicke_vad == 'webrtcvad':
            audio = AudioWithWebRTC()
        else:
            log.main.error("Invalid VAD configuration: %s", CONFIG.wernicke_vad)
            return
        log.wernicke.info("Using VAD: %s", CONFIG.wernicke_vad)

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

# Note: Subprocess will be started in run() method after shared memory injection

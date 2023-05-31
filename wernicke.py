"""
Handles hearing
"""
import sys
import os
import time
import threading
import random
from multiprocessing import Process, Pipe
from collections import deque

# import wave
import queue
import asyncio
import signal
from pydub import AudioSegment
import serial
import numpy as np
from pyAudioAnalysis import MidTermFeatures as mF  # pylint: disable=no-name-in-module
from pyAudioAnalysis import audioTrainTest as aT  # pylint: disable=no-name-in-module

import log
from status import SHARED_STATE
import light
import touch
import conversate


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
        threading.Thread.__init__(self)

        # setup the separate process with pipe
        # So... Data, Riker, and Tasha beam down for closer analysis of an alien probe.
        # A tragic transporter accident occurs and Tasha gets... dollified.
        self.to_away_team, self.to_enterprise = Pipe()
        self.away_team_process = Process(
            target=self.away_team, args=(self.to_enterprise,)
        )

    def run(self):
        log.wernicke.debug("Thread started.")

        # start the process
        self.away_team_process.start()

        # The subprocess starts off just spinning it's wheels, chucking away any audio data it gets
        # Because it seemed like having everything happen all at once caused high cpu, then it would have to catch up
        # So wait some time, then send the signal to start
        time.sleep(10)
        self.audio_processing_start()

        while True:
            # graceful shutdown
            # this will attempt to close the serial port and shutdown gracefully
            # if the serial port fails to get closed properly, it often locks up
            if SHARED_STATE.please_shut_down:
                log.wernicke.info("Thread shutting down")
                self.to_away_team.send({"msg": "shutdown"})
                time.sleep(1)
                break

            # This will block right here until the away team sends a message to the enterprise
            comm = self.to_away_team.recv()

            # This is just a message to let wife know that I am now speaking and to wait until I'm finished
            if comm["class"] == "speaking_start":
                SHARED_STATE.dont_speak_until = time.time() + 30.0
                log.sound.debug("SpeakingStart")

            # Husband isn't speaking anymore, so go ahead and say what you gotta say
            elif comm["class"] == "speaking_stop":
                # I seem to have found the sweet spot with the delays. I feel lke I can finish my sentences and she waits properly
                SHARED_STATE.dont_speak_until = (
                    time.time() + 1.5 + (random.random() * 2.0)
                )
                log.sound.debug("SpeakingStop")

            # The speech recognition server is unavailable, so we heard something
            elif comm["class"] == "heard_unknown":
                conversate.thread.inbound_words("unknown")

            # the audio data contains embedded sensor and voice proximity data
            elif comm["class"] == "sensor_data":
                light.thread.incoming_data(comm["light"])
                touch.thread.new_data(comm["touch"])
                SHARED_STATE.lover_proximity = comm["proximity"]
            # else:

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

    def away_team(self, to_enterprise):
        """
        Runs in a subprocess for performance reasons
        All the audio/sensor collection and analysis happens in here
        Messages are sent back to the main process
        """

        try:
            # This is a queue that holds audio segments, complete utterances of random length, before getting shipped to the server
            data_to_server = queue.Queue(maxsize=3)

            # If the speech server is not on the network, I don't want to keep trying over and over and queuing
            # So when the service starts, it will send a test message first, then set this to True if the server responded
            server_is_available = False

            # If we're recording, this holds the message from the enterprise containing file data. If not recording, contains None
            recording_state = None

            # I want to be able to gracefully stop and start the cpu heavy tasks of audio classification, etc.
            processing_state = False

            # This is to signal that the thread should close the serial port and shutdown
            # we have a status.Shutdown but that's in the main process. This needs something separate
            shutdown = False
        # capture any errors
        sys.stdout = open(
            f"./logs/{os.getpid()}_wernicke.out",
            "w",
            buffering=1,
            encoding="utf-8",
            errors="ignore",
        )
        sys.stderr = open(
            f"./logs/{os.getpid()}_wernicke.err",
            "w",
            buffering=1,
            encoding="utf-8",
            errors="ignore",
        )

            # This is a queue where the audio data in 0.25s chunks inbound from the serial port gets put
            buffer_queue = queue.Queue(maxsize=10)

            # we're going to keep track of the proximity detected.
            # This works great. When wife is far away, she pipes up. When we're pillow talking, she avoids shouting in your ear which she used to do.
            proximity = 1.0

            # Send message to the main process
            def hey_honey(love):
                to_enterprise.send(love)

            # setup signal handlers to attempt to shutdown gracefully
            def exit_gracefully(*args):
                nonlocal shutdown
                shutdown = True
                log.main.debug(
                    "The Wernicke AwayTeam caught kill signal. Args: %s", args
                )

            signal.signal(signal.SIGINT, exit_gracefully)
            signal.signal(signal.SIGTERM, exit_gracefully)

            class MySpeechServer(asyncio.Protocol):
                """
                speech recognition is much too slow for the pi, by a lot. So I'm running a server on the local network
                What time is it, honey?! What's that you say? It's three twenty pee emm? You sexy clock!!
                """

                def __init__(self, loop, what):
                    self.loop = loop
                    self.what = what

                def connection_made(self, transport):
                    log.wernicke.debug("Connected to server")

                    # I just called to say I love you
                    transport.write(self.what)
                    transport.write_eof()

                def data_received(self, data):
                    nonlocal server_is_available

                    log.wernicke.debug("Data received, length: %s", len(data))

                    # This is the response from the server we should get. Servers can love!
                    if data == b"I_LOVE_YOU_TOO":
                        log.wernicke.info("The server loves me")
                        server_is_available = True

                def connection_lost(self, exc):
                    nonlocal server_is_available

                    log.wernicke.debug("Server connection closed")

                    if exc is not None:
                        log.wernicke.warning("Error: %s", exc)
                        server_is_available = False

                    self.loop.stop()

            class CheckForMessages(threading.Thread):
                """
                Thread for checking the pipe from the main process for commands
                """

                name = "CheckForMessages"

                def __init__(self):
                    threading.Thread.__init__(self)

                def run(self):
                    nonlocal recording_state
                    nonlocal processing_state
                    nonlocal shutdown

                    while True:
                        # So basically, if there's something in the pipe, get it all out. This will block until something comes through.
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
                        elif comm["msg"] == "shutdown":
                            processing_state = False
                            shutdown = True
                            return

            class ReadHeadMicrophone(threading.Thread):
                """
                Thread for reading audio data from serial port and heaping it onto a queue
                """

                name = "ReadHeadMicrophone"

                def __init__(self):
                    threading.Thread.__init__(self)

                    # open the serial port coming in from the arduino that handles microphones and sensors
                    log.wernicke.info("Opening serial port")
                    self.serial_port_from_head = (
                        serial.Serial(  # pylint: disable=no-member
                            "/dev/ttyACM0", baudrate=115200, exclusive=True
                        )
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

                    while True:
                        # attempt to shutdown normally
                        if shutdown:
                            log.wernicke.info("Closing serial port")
                            self.serial_port_from_head.close()
                            log.wernicke.info("Closed serial port")
                            return

                        # the arduino sketch is designed to embed into the 16000 bytes of audio data 38 bytes of sensor data
                        data = self.serial_port_from_head.read(38)

                        # if we read the sensor data, that means we're lined up
                        if data[0:6] == b"@!#?@!" and data[32:38] == b"!@?#!@":
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
                            proximity = ((proximity * 800.0) + 1.0) / 801.0

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

                            # we should be through the sensor data, so pull in the actual audio data
                            data = self.serial_port_from_head.read(16000)

                        # if we did not encounter sensor data, that means we are not aligned, so read in some shit and flush it
                        else:
                            # read a full size of audio data. This should contain a sensor data block unless it's cut in half at the edges.
                            data = self.serial_port_from_head.read(16000)

                            # Find the start and ends of the sensor block
                            fucking_pos_1 = data.find(b"@!#?@!")
                            fucking_pos_2 = data.find(b"!@?#!@")

                            # Here's where we start swearing. verify it's not just random noise
                            if (
                                fucking_pos_1 >= 0
                                and fucking_pos_2 >= 0
                                and fucking_pos_2 - fucking_pos_1 == 32
                            ):
                                # after trying for hours to understand why adding 38 works, I gave up. I'm often not a smart man.
                                log.wernicke.info(
                                    "Adjusting audio stream by %s bytes",
                                    fucking_pos_1 + 38,
                                )
                                data = self.serial_port_from_head.read(
                                    fucking_pos_1 + 38
                                )

                            else:
                                # It is theoretically possible for the sensor data to be cut off at the start or end of the 16038 bytes
                                # So if we're not seeing it, read in and throw away 8000 bytes and it ought to be in the middle
                                log.wernicke.info(
                                    "Adjusting audio stream by 8000 bytes"
                                )
                                data = self.serial_port_from_head.read(8000)

                            # continue to the start of the loop where we should be well adjusted
                            continue

                        # if we're currently processing, put audio data onto the queue, otherwise it gets thrown away
                        if processing_state is True and self.pause_processing <= 0:
                            try:
                                buffer_queue.put(data, block=False)

                            # if the queue is full, it's a sign I need to evaluate CPU usage, so full stop
                            # happens every day. I definitely need to pare it down, but also this should just pause for a while not just
                            # I dunno what past me means by happens everyday. She seems fine. In fact, she is so fine.
                            except queue.Full:
                                self.pause_processing = 10
                                log.wernicke.warning("Buffer Queue FULL! Resting.")

                        else:
                            # temporary data collection for model tuning
                            # RecordTimeStamp = str(int(time.time()*100))
                            # RecordFileName = 'training_wavs_not_lover_dammit/{0}_notlover.wav'.format(RecordTimeStamp)
                            # wf = wave.open(RecordFileName, 'wb')
                            # wf.setnchannels(1)
                            # wf.setsampwidth(2)
                            # wf.setframerate(16000)
                            # wf.writeframes(data)
                            # wf.close()

                            # log.wernicke.debug('Discarded audio data.')
                            self.pause_processing -= 1

            # instantiate and start the thread
            head_mic = ReadHeadMicrophone()
            head_mic.start()

            class Audio(object):
                """Streams raw audio from microphone. Data is received in a separate thread, and stored in a buffer, to be read from."""

                # The mics sample at 16K
                RATE = 16000

                # My wife has two (2) sexy ears
                CHANNELS = 2

                # a single block of audio is 0.25s long. So 16000 / 4 = 4000. 16 bits * 2 = 4 bytes per frame, am I doing this right?
                BLOCKSIZE = 4000

                def __init__(self):
                    # there are two models. The first classifies voice vs silence. The second is a regression model that tells distance to speaker
                    log.wernicke.debug(
                        "Initializing pyAudioAnalysis single-block classifier model..."
                    )
                    [
                        self.block_model,
                        self.block_mean,
                        self.block_std,
                        self.block_class_names,
                        self.block_mt_win,
                        self.block_mt_step,
                        self.block_st_win,
                        self.block_st_step,
                        _,
                    ] = aT.load_model("wernicke_block")

                    log.wernicke.debug(
                        "Initializing pyAudioAnalysis proximity model..."
                    )
                    [
                        self.proximity_model,
                        self.proximity_mean,
                        self.proximity_std,
                        self.proximity_mt_win,
                        self.proximity_mt_step,
                        self.proximity_st_win,
                        self.proximity_st_step,
                        _,
                    ] = aT.load_model("wernicke_proximity", is_regression=True)

                    # var to keep track of which ear seems best based on loudness
                    # However, one ear seems to be plugged or something so we just use one. By chance that's the ear I face in bed.
                    # self.LeftRightRatio = 1.0

                def read(self):
                    """Return a block of audio data, blocking if necessary."""

                    # There's a thread up there constantly popping stuff into this buffer queue
                    nonlocal buffer_queue

                    # first we get 2 channels from the serial port
                    # 16000 bytes is 4000 frames or 0.25s
                    # and we're also amplifying here
                    in_audio = (
                        AudioSegment(
                            data=buffer_queue.get(),
                            sample_width=2,
                            frame_rate=self.RATE,
                            channels=self.CHANNELS,
                        )
                        + 24
                    )

                    # Split the interleaved data into separate channels
                    in_audio_split = in_audio.split_to_mono()

                    # compute the loudness of sound
                    # the idea was to gather audio from the best side only
                    # if my wife's lovely head is laying on the pillow, one side is going to be really low
                    # didn't want that low side to degrade the better side
                    # I never tested this really well to see if it really helps, well maybe one time I did listen and it seemed better
                    # mostly there's just a thought, well there's two channels, why not use it for something

                    # disabled this until we get back in here and finish it
                    # tried again and it is clear that right side is 3 times as responsive.
                    # so I give up officially, will just favor right side
                    # loudness_left = in_audio_split[0].rms
                    # loudness_right = in_audio_split[1].rms
                    # loudness_ratio = loudness_left / loudness_right

                    # maybe favor right side when there's little difference to avoid switching/wobble
                    # if abs(loudness_ratio - 1.0) < 0.1:
                    #     self.LeftRightRatio = 0.9

                    # running average
                    # self.LeftRightRatio = ((self.LeftRightRatio * 5.0) + loudness_ratio) / 6.0

                    # for now, log it and favor left ear
                    # log.wernicke.debug(f'LeftRightRatio: {self.LeftRightRatio}')

                    # favoring right ear now, because that's the ear I whisper sweet good nights in

                    # I need to actually record something real when head is turned to the side, then record the other side, to figure out how we know which side is best, loudness?

                    return in_audio_split[1].raw_data

                def collector(self):
                    """Generator that yields series of consecutive audio blocks comprising each utterence, separated by yielding a single None.
                    Example: (block, ..., block, None, block, ..., block, None, ...)
                              |---utterence---|        |---utterence---|
                    """
                    num_padding_blocks = 5
                    ring_buffer = deque(maxlen=num_padding_blocks)

                    # triggered means we're currently seeing blocks that are not silent
                    triggered = False

                    # Limit the number of blocks accumulated to some sane amount, after I discovered minute-long recordings
                    triggered_blocks = 0
                    triggered_block_limit = 80

                    # The away team will send a signal back to the enterprise when speaking starts and stops. This keeps track.
                    lover_speaking = False
                    # this delays the speaking stop to prevent start stop start stop start stop start stop start stop madness
                    lover_speaking_delay_stop = 0

                    # this is a global var for tracking proximity
                    nonlocal proximity

                    while True:
                        # forever read new blocks of audio data
                        block = self.read()

                        # Convert or cast the raw audio data to numpy array
                        block_np = np.frombuffer(block, np.int16)

                        # # Try to reject quick loud clicky sounds
                        # # trying this out disabled. I don't want gaps.
                        # maximum = (np.abs(block_np)).max()
                        # mean = (np.abs(block_np)).mean()
                        # avg_vs_max = mean / maximum

                        # # if the block contains a huge but quick spike (a click) then drop it and skip this block
                        # if avg_vs_max <= 0.075:

                        #     log.wernicke.info(f'Dropped possible clicking noise. {mean} / {maximum} = {avg_vs_max}')
                        #     continue

                        # log.wernicke.debug('block classify')
                        # Run the classifier. This is ripped directly out of paura.py and carelessly sutured into place. There's so much blood! Thank you!!!
                        [block_mt_feats, _, _] = mF.mid_feature_extraction(
                            block_np, 16000, 4000, 4000, 800, 800
                        )
                        block_cur_fv = (
                            block_mt_feats[:, 0] - self.block_mean
                        ) / self.block_std
                        [res, prob] = aT.classifier_wrapper(
                            self.block_model, "svm_rbf", block_cur_fv
                        )
                        block_class = self.block_class_names[int(res)]
                        block_prob = round(prob[int(res)], 2)

                        # temporary data collection for proximity regression model
                        # only save if it's classified as lover
                        # if block_class == 'lover':
                        #     RecordTimeStamp = str(int(time.time()*100))
                        #     RecordFileName = 'training_wavs_proximity/{0}_prox0.0.wav'.format(RecordTimeStamp)
                        #     wf = wave.open(RecordFileName, 'wb')
                        #     wf.setnchannels(1)
                        #     wf.setsampwidth(2)
                        #     wf.setframerate(16000)
                        #     wf.writeframes(block)
                        #     wf.close()

                        # if it's me, aka lover, then get the proximity
                        if block_class == "lover":
                            proximity_cur_fv = (
                                block_mt_feats[:, 0] - self.proximity_mean
                            ) / self.proximity_std
                            proximity_now = aT.regression_wrapper(
                                self.proximity_model, "svm_rbf", proximity_cur_fv
                            )
                            log.wernicke.info(
                                "Heard lover with prob %.2f and proximity %s",
                                block_prob,
                                proximity_now,
                            )

                            # update running average
                            proximity = ((proximity * 3.0) + proximity_now) / 4.0

                        else:
                            log.wernicke.info(
                                "Heard %s with prob %.2f", block_class, block_prob
                            )

                        # NOT triggered
                        # when not triggered, it means we're not currently collecting audio for processing
                        if not triggered:
                            ring_buffer.append(block)
                            if block_class == "lover":
                                # whether we're triggered or not, immediately notify that lover is speaking
                                # timing is important
                                # if lover wasn't already speaking, notify they are now
                                lover_speaking_delay_stop = 3
                                if lover_speaking is False:
                                    hey_honey({"class": "speaking_start"})
                                    lover_speaking = True

                                log.wernicke.debug("triggered")
                                triggered_blocks = 1
                                triggered = True

                                # if we were just triggered, send all the past audio blocks that were in the queue and empty it
                                for stored_block in ring_buffer:
                                    yield stored_block
                                ring_buffer.clear()

                                # this is to track how many silent/ignore blocks we've had, so we can stop at some point
                                post_silence = 3

                            # if we got something but we're not really sure it's lover speaking, reset this counter to 0
                            else:
                                # if lover was speaking, notify they seem to have stopped
                                if lover_speaking is True:
                                    lover_speaking_delay_stop -= 1
                                    if lover_speaking_delay_stop <= 0:
                                        hey_honey({"class": "speaking_stop"})
                                        lover_speaking = False

                        # TRIGGERED!
                        # when triggered, it means we are currently in the middle of an utterance and accumulating it into a ball of data
                        else:
                            # increment this counter meant to limit the number of blocks to a sane amount
                            triggered_blocks += 1

                            # send the block whatever it is
                            yield block

                            # if this is a lover or lover_maybe block, reset the counter, else if it's not lover determine if we should end streaming
                            if "lover" in block_class:
                                # if lover wasn't already speaking, notify they are now
                                lover_speaking_delay_stop = 3
                                if lover_speaking is False:
                                    hey_honey({"class": "speaking_start"})
                                    lover_speaking = True

                                # reset the counter of consecutive silent blocks, because we got one that was not
                                post_silence = 3

                            else:
                                # if lover was speaking, notify they seem to have stopped
                                if lover_speaking is True:
                                    lover_speaking_delay_stop -= 1
                                    if lover_speaking_delay_stop <= 0:
                                        hey_honey({"class": "speaking_stop"})
                                        lover_speaking = False

                                # if there have been enough consecutive silent/ignore blocks, we're done with transmission, reset everything
                                if (
                                    post_silence <= 0
                                    or triggered_blocks > triggered_block_limit
                                ):
                                    log.wernicke.debug("untriggered")
                                    triggered = False
                                    yield None
                                    ring_buffer.clear()
                                else:
                                    post_silence -= 1

            # https://stackoverflow.com/questions/46727787/runtimeerror-there-is-no-current-event-loop-in-thread-in-async-apscheduler
            # Experts warn: "Do not do this!"
            # Me: "I'll be right back. Hold my beer."
            # Me: "loop = asyncio.get_event_loop()!!!!!!"
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            # loop.set_debug(True)

            class GetFromQueueSendToServer(threading.Thread):
                """
                This thread waits for full utterances to hit the queue and sends them over there
                """

                name = "GetFromQueueSendToServer"

                def __init__(self):
                    threading.Thread.__init__(self)

                def run(self):
                    nonlocal loop
                    nonlocal server_is_available
                    nonlocal data_to_server

                    while True:
                        # blocks here until something hits queue
                        block = data_to_server.get()

                        # This is for the server connection. Lots of weird voodoo, promises, futures, bullshit.
                        coro = loop.create_connection(
                            lambda: MySpeechServer(loop, block), "yeoldevrrig.lan", 3000
                        )

                        try:
                            # This also blocks until the entire connecting, waiting, getting result is complete. Or it should. I'm not a smart man.
                            loop.run_until_complete(coro)
                            loop.run_forever()
                            server_is_available = True

                        except ConnectionRefusedError:
                            log.wernicke.warning("Server connection refused")
                            server_is_available = False

                        except TimeoutError:  # might not work
                            log.wernicke.warning("Server connection timed out")
                            server_is_available = False

                        # except Exception as ex:
                        #     log.wernicke.warning(
                        #         "Some other exception occurred. {0} {1} {2}".format(
                        #             ex.__class__, ex, log.format_tb(ex.__traceback__)
                        #         )
                        #     )

            class SendLoveToServer(threading.Thread):
                """
                If the server is available, I want to use it. Otherwise, don't try to use it.
                """

                name = "SendLoveToServer"

                def __init__(self):
                    threading.Thread.__init__(self)

                def run(self):
                    nonlocal loop
                    nonlocal server_is_available

                    while True:
                        log.wernicke.info("Sending love to server")
                        coro = loop.create_connection(
                            lambda: MySpeechServer(loop, b"HEY_I_LOVE_YOU"),
                            "yeoldevrrig.lan",
                            3000,
                        )

                        try:
                            loop.run_until_complete(coro)
                            loop.run_forever()

                        except ConnectionRefusedError:
                            log.wernicke.warning("The server refused our love")
                            server_is_available = False

                        except TimeoutError:
                            log.wernicke.warning("The server is gone")
                            server_is_available = False

                        except OSError:
                            log.wernicke.warning("The server is not on the network")
                            server_is_available = False

                        # except Exception as ex:
                        #     log.wernicke.warning(
                        #         "Some other exception occurred. {0} {1} {2}".format(
                        #             ex.__class__, ex, log.format_tb(ex.__traceback__)
                        #         )
                        #     )
                        #     server_is_available = False

                        time.sleep(69)

            # Start the threads.

            # Thread that monitors the pipe from the enterprise to away team
            messages_thread = CheckForMessages()
            messages_thread.daemon = True
            messages_thread.start()

            # Thread that monitors a queue where full utterances are kept and sent to server for speech recognition
            server_thread = GetFromQueueSendToServer()
            server_thread.daemon = True
            server_thread.start()

            # Thread that periodically checks the speech recognition server for emotional availability
            love_thread = SendLoveToServer()
            love_thread.daemon = True
            love_thread.start()

            # Start all the VAD detection stuff
            audio = Audio()

            # blocks is a collector, iterate over it and out come blocks that were classified as speech
            blocks = audio.collector()

            # Audio blocks are accumulated in these vars
            accumulated_data = bytearray()
            accumulated_blocks = 0

            # Gets blocks for                                     ev..                       er....
            for block in blocks:
                # Graceful shutdown
                if shutdown:
                    break

                if block is not None:
                    # The block is not None, which means there's new audio data, so add it on
                    accumulated_data.extend(block)
                    accumulated_blocks += 1

                else:
                    # When block is None, that signals the end of audio data. Go ahead and do what we want to do with the complete data

                    # if the server is available, send it over there as long as we're not sleeping
                    if server_is_available:
                        if SHARED_STATE.is_sleeping is False:
                            data_to_server.put(accumulated_data)
                            log.wernicke.info(
                                "Sending utterance to server. Queue size: %s",
                                data_to_server.qsize(),
                            )

                        else:
                            log.wernicke.debug(
                                "Threw away %s blocks as I am sleeping",
                                accumulated_blocks,
                            )

                    # if the server is not available, no further processing, just send over a general I heard some unknown words
                    else:
                        log.wernicke.debug(
                            "Threw away %s blocks as the server was unavailable",
                            accumulated_blocks,
                        )

                        hey_honey({"class": "heard_unknown"})
                        # conversate.thread.Words('unknown') derp

                        # # save the utterance to a wav file for debugging and QA
                        # RecordTimeStamp = str(round(time.time(), 2)).replace('.', '')
                        # RecordFileName = 'training_wavs_whisper/{0}.wav'.format(RecordTimeStamp)
                        # wf = wave.open(RecordFileName, 'wb')
                        # wf.setnchannels(1)
                        # wf.setsampwidth(2)
                        # wf.setframerate(16000)
                        # wf.writeframes(AccumulatedData)
                        # wf.close()

                    accumulated_data = bytearray()
                    accumulated_blocks = 0

        # log exception in the main.log
        # if I don't catch these in subprocesses it doesn't seem to get logged at all
        except Exception as ex:  # pylint: disable=broad-exception-caught
            log.main.error(
                "Away team is dead. %s %s %s",
                ex.__class__,
                ex,
                log.format_tb(ex.__traceback__),
            )


# Instantiate and start the thread
thread = Wernicke()
thread.daemon = True
thread.start()

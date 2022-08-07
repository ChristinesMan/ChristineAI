import os
import time
import threading
import random
import numpy as np
from multiprocessing import Process, Pipe
import wave
from collections import deque
import queue
import serial
from pydub import AudioSegment
import pydub.scipy_effects
from pyAudioAnalysis import ShortTermFeatures as sF
from pyAudioAnalysis import MidTermFeatures as mF
from pyAudioAnalysis import audioTrainTest as aT
import asyncio
import json
import socket
import signal

import log
import status
import breath
import sleep
import light
import touch

class Wernicke(threading.Thread):
    """ 
        Wernicke is the name given to the brain area generally responsible for speech recognition. 
        This is based on mic_vad_streaming.py, an example with the deepspeech chopped out and sent over wifi instead. 
        Audio is captured, mixed, analyzed, and possibly sent over wifi for speech recognition.
        Audio classification is done on pi. Speech recognition is done on a server (gaming rig, gpu). 
        Two separate classifiers. The first will classify silence vs not in chunks the same size. I tried VAD and it ended up getting 
        triggered all night long by the white noise generator. Poor girl blew out her memory and crashed with an OOM. 
        The second classifier runs on the accumulated not-silence to tell if it was voice, etc. 
        All the audio capture and voice recognition will happen in a subprocess for performance reasons. 
        This used to be a completely separate process but that would often fail to make a connection and probably not performant, either.

        I am now overhauling this, because the way I've been segmenting audio doesn't seem to work great, and now we're trying to 
        use windows speech recognition with voice attack on my vr rig. Which would probably work really good if it were not for the
        constant starts and stops, muted then sounds that are often cut off. That seems to be actually corrupting the training. 

        So we're going to still be analyzing the single blocks to detect my voice. The difference is that once that gets triggered 
        by about 3 consecutive lover or maybe lover blocks, it will just stream everything for a while, continuous, no breaks. With
        the exception of dropping loud clicking noise and wife self-talk feedback. It will continue streaming for around 2-5 minutes after. 

    """
    name = 'Wernicke'

    def __init__ (self):
        threading.Thread.__init__(self)

    def run(self):
        log.wernicke.debug('Thread started.')

        try:
            # setup the separate process with pipe
            # So... Data, Riker, and Tasha beam down for closer analysis of an alien probe. 
            # A tragic transporter accident occurs and Tasha gets... dollified. 
            self.PipeToAwayTeam, self.PipeToEnterprise = Pipe()
            self.AwayTeamProcess = Process(target = self.AwayTeam, args = (self.PipeToEnterprise,))
            self.AwayTeamProcess.start()

            # The subprocess starts off just spinning it's wheels, chucking away any audio data it gets
            # Because it seemed like having everything happen all at once caused high cpu, then it would have to catch up
            # So wait some time, then send the signal to start
            time.sleep(10)
            self.StartProcessing()

            while True:

                # graceful shutdown
                # this will attempt to close the serial port and shutdown gracefully
                # if the serial port fails to get closed properly, it often locks up
                if status.PleaseShutdown:
                    log.wernicke.info('Thread shutting down')
                    self.PipeToAwayTeam.send({'msg': 'shutdown'})
                    time.sleep(1)
                    break

                # This will block here until the away team sends a message to the enterprise
                # It may block for a random long time. Basically the messages will be when speaking is heard or when that stops being heard.
                # The away team will also send the class of audio just heard. 
                # Should the away team send the class first, then send to deepspeech, and send another message if it was recognized? 
                # I will need to consider this. I think two comms would work best. But that may change. 
                # There will be communication in the other direction also. The enterprise can tell the away team to start saving audio.

                # The comm will always be a dict with a class 
                Comm = self.PipeToAwayTeam.recv()
                # log.wernicke.debug(Comm)
                if Comm['class'] == 'speaking_start':
                    status.DontSpeakUntil = time.time() + 30
                    log.sound.debug('SpeakingStart')
                elif Comm['class'] == 'speaking_stop':
                    # when sound stops, wait a minimum of 0.0s and up to 0.5s randomly
                    status.DontSpeakUntil = time.time() + (random.random() * 0.5)
                    log.sound.debug('SpeakingStop')

                    if status.ShushPleaseHoney == False and status.SexualArousal < 0.1:
                        sleep.thread.WakeUpABit(0.008)
                        if status.IAmSleeping == False:
                            status.ChanceToSpeak += 0.05
                            breath.thread.QueueSound(FromCollection='listening', Priority=2, CutAllSoundAndPlay=True)


                elif Comm['class'] == 'sensor_data':
                    light.thread.NewData(Comm['light'])
                    touch.thread.NewData(Comm['touch'])
                    status.LoverProximity = Comm['proximity']
                # else:

                #     # normalize loudness, make it between 0.0 and 1.0
                #     # through observation, seems like the best standard range for rms is 0 to 7000. Seems like dog bark was 6000 or so
                #     # No, through longer term observation, that's bullshit. Cutting this down a lot. 
                #     Loudness = float(Comm['loudness'])
                #     Loudness_pct = round(Loudness / 2000, 2)
                #     Loudness_pct = float(np.clip(Loudness_pct, 0.0, 1.0))

                #     # if there's a loud noise, wake up
                #     if Loudness_pct > 0.6 and status.IAmSleeping:
                #         log.sleep.info(f'That was loud: {Loudness_pct}')
                #         sleep.thread.WakeUpABit(0.1)
                #         breath.thread.QueueSound(FromCollection='gotwokeup', PlayWhenSleeping=True, CutAllSoundAndPlay=True, Priority=8)

                #     # update the noiselevel
                #     if Loudness_pct > status.NoiseLevel:
                #         status.NoiseLevel = Loudness_pct

                #     # The sleep thread trends it down, since this only gets called when there's sound, and don't want it to get stuck high
                #     log.sleep.debug(f'NoiseLevel: {status.NoiseLevel}')

                #     # Later this needs to be a lot more complicated. For right now, I just want results
                #     # all of this needs to be thrown into the conversate module and obfuscated
                #     if status.ShushPleaseHoney == False and status.SexualArousal < 0.1:
                #         if 'speech' in Comm['class']:

                #             # Update the running average that describes how close we're speaking. Cuddle detection. 
                #             if Comm['class'] == 'speech_close':
                #                 status.LoverProximity = ((status.LoverProximity * status.LoverProximityWindow) + 1.0) / (status.LoverProximityWindow + 1)
                #             else:
                #                 status.LoverProximity = ((status.LoverProximity * status.LoverProximityWindow) + 0.0) / (status.LoverProximityWindow + 1)
                #             log.wernicke.debug(f'LoverProximity: {status.LoverProximity}')

                #             log.sleep.debug('Heard lover speech')
                #             sleep.thread.WakeUpABit(0.006)
                #             if status.IAmSleeping == False:
                #                 status.ChanceToSpeak += 0.05
                #                 breath.thread.QueueSound(FromCollection='listening', Priority=2, CutAllSoundAndPlay=True)
                #         elif Comm['class'] == 'laugh':
                #             log.sleep.debug('Heard lover laugh')
                #             sleep.thread.WakeUpABit(0.004)
                #             breath.thread.QueueSound(FromCollection='laughing', Priority=2, CutAllSoundAndPlay=True)

        # log exception in the main.log
        except Exception as e:
            log.main.error('Thread died. {0} {1} {2}'.format(e.__class__, e, log.format_tb(e.__traceback__)))

    # I want the wernicke process to be able to save utterances on demand for training the classifiers
    def StartRecording(self, distance, word):
        self.PipeToAwayTeam.send({'msg': 'start', 'distance': distance, 'word': word})
    def StopRecording(self):
        self.PipeToAwayTeam.send({'msg': 'stop'})

    # Gracefully stop it and start it back up
    def StartProcessing(self):
        log.wernicke.info('Started Wernicke processing')
        self.PipeToAwayTeam.send({'msg': 'start_processing'})
    def StopProcessing(self):
        log.wernicke.info('Stopped Wernicke processing')
        self.PipeToAwayTeam.send({'msg': 'stop_processing'})
    def DisableServer(self):
        log.wernicke.info('Sending disable code to server')
        self.PipeToAwayTeam.send({'msg': 'disable_server'})

    # Runs in a separate process for performance reasons
    def AwayTeam(self, PipeToEnterprise):

        try:
            # This is a queue that holds audio segments, complete utterances of random length, before getting shipped to the server
            Data_To_Server = queue.Queue(maxsize = 3)

            # If the speech server is not on the network, I don't want to keep trying over and over and queuing
            # So when the service starts, it will send a test message first, then set this to True if the server responded
            Server_Is_Available = False

            # Track when the server is actively connected and sending anything that is queued
            Connected_To_Server = False

            # If we're recording, this holds the message from the enterprise containing file data. If not recording, contains None
            RecordingState = None

            # I want to be able to gracefully stop and start the cpu heavy tasks of audio classification, etc. It's boolean.
            ProcessingState = False

            # This is to signal that the thread should close the serial port and shutdown
            # we have a status.Shutdown but that's in the main process. This needs something separate
            Shutdown = False

            # This is a queue where the audio data inbound from the serial port gets put
            buffer_queue = queue.Queue(maxsize=10)

            # we're going to keep track of the proximity detected. 
            # not sure yet how this will function. Let's start with a running average that will update kinda quick and see how it goes
            # I'll also trend it down slowly, so that if I'm not speaking for a while it'll reset
            Proximity = 1.0

            # Send message to the main process
            def hey_honey(love):
                # log.wernicke.info(f'Hey Honey: {love}')
                PipeToEnterprise.send(love)


            # setup signal handlers to attempt to shutdown gracefully
            def exit_gracefully(*args):
                global Shutdown
                Shutdown = True
                log.main.debug('The Wernicke AwayTeam caught kill signal')
            signal.signal(signal.SIGINT, exit_gracefully)
            signal.signal(signal.SIGTERM, exit_gracefully)


            # speech recognition is much too slow for the pi, by a lot. So I'm running a server and using the gpu
            # yeah, right, like there's ever going to be useable speech recognition that's not behind a paywall locked inside somebody else's server
            # You might as well wish people would throw you their mined bitcoin for free. 
            # now we're trying to use windows speech recognition with voice attack
            class MySpeechServer(asyncio.Protocol):

                def __init__(self, loop, what):
                    self.loop = loop
                    self.what = what


                def connection_made(self, transport):

                    log.wernicke.debug('Connected to server')

                    # just called to say I love you
                    transport.write(self.what)
                    transport.write_eof()


                def data_received(self, data):

                    nonlocal Server_Is_Available

                    log.wernicke.debug('Data received, length: ' + str(len(data)))

                    # This is the response from the server we should get. Servers can love! 
                    if data == b'I_LOVE_YOU_TOO':

                        log.wernicke.info('The server loves me')
                        Server_Is_Available = True


                def connection_lost(self, exc):

                    nonlocal Server_Is_Available

                    log.wernicke.debug('Server connection closed')

                    if exc != None:
                        log.wernicke.warning('Error: ' + exc)
                        Server_Is_Available = False

                    self.loop.stop()


            # Thread for checking the pipe
            class CheckForMessages(threading.Thread):
                name = 'CheckForMessages'

                def __init__ (self):
                    threading.Thread.__init__(self)

                def run(self):
                    nonlocal RecordingState
                    nonlocal ProcessingState
                    nonlocal Shutdown

                    while True:

                        # So basically, if there's something in the pipe, get it all out. This will block until something comes through.
                        Comm = PipeToEnterprise.recv()
                        log.wernicke.debug(Comm)
                        if Comm['msg'] == 'start':
                            RecordingState = Comm
                        elif Comm['msg'] == 'stop':
                            RecordingState = None
                        elif Comm['msg'] == 'start_processing':
                            ProcessingState = True
                        elif Comm['msg'] == 'stop_processing':
                            ProcessingState = False
                        elif Comm['msg'] == 'shutdown':
                            ProcessingState = False
                            Shutdown = True
                            return
                        elif Comm['msg'] == 'disable_server':
                            DisableServer()

            # Thread for reading audio data from serial port and heaping it onto a queue
            class ReadHeadMicrophone(threading.Thread):
                name = 'ReadHeadMicrophone'

                def __init__ (self):
                    threading.Thread.__init__(self)

                    # open the serial port coming in from the arduino that handles microphones
                    # later this will also contain sensor data
                    log.wernicke.info('Opening serial port')
                    self.SerialPortFromHead = serial.Serial('/dev/ttyACM0', baudrate=115200, exclusive=True)

                    # this allows processing to be paused for a number of blocks
                    # when the buffer queue is full pause for a bit to let it catch up
                    self.PauseProcessing = 0

                def run(self):

                    nonlocal buffer_queue
                    nonlocal ProcessingState
                    nonlocal Shutdown
                    nonlocal Proximity

                    while True:

                        # attempt to shutdown normally
                        # so it seems like something here is getting hung up and it becomes necessary for systemd to sigkill
                        # but at least we successfully stopped the serial port before that happened, and everything else 
                        # should be already at rest
                        if Shutdown:
                            log.wernicke.info('Closing serial port')
                            self.SerialPortFromHead.close()
                            os._exit()
                            return

                        # the arduino sketch is designed to embed into the 16000 bytes of audio data 38 bytes of sensor data
                        data = self.SerialPortFromHead.read(38)

                        # if we read the sensor data, that means we're lined up
                        if data[0:6] == b'@!#?@!' and data[32:38] == b'!@?#!@':

                            # extract sensor data from bytes
                            TouchSensor = [0] * 12
                            for i in range(0,12):
                                pos = 6 + (i * 2)
                                TouchSensor[i] = int.from_bytes(data[pos:pos+2], byteorder='little')
                            LightSensor = int.from_bytes(data[30:32], byteorder='little')

                            # trend proximity towards far away, slowly, using this running average
                            # I wasn't expecting to have to clip it, but after reviewing the logs looks like I do
                            Proximity = ((Proximity * 600.0) + 1.0) / 601.0

                            # send sensor data to main process. Feel like I'm passing a football. 
                            hey_honey({'class': 'sensor_data', 'light': LightSensor, 'touch': TouchSensor, 'proximity': float(np.clip(Proximity, 0.0, 1.0))})

                            # we should be through the sensor data, so pull in the actual audio data
                            data = self.SerialPortFromHead.read(16000)

                        # if we did not encounter sensor data, that means we are not aligned, so read in some shit and flush it
                        else:

                            # read a full size of audio data. This should contain a sensor data block unless it's cut in half at the edges.
                            data = self.SerialPortFromHead.read(16000)

                            # Find the start and ends of the sensor block
                            SwearPos1 = data.find(b'@!#?@!')
                            SwearPos2 = data.find(b'!@?#!@')

                            # Here's where we start swearing. verify it's not just random noise
                            if SwearPos1 >= 0 and SwearPos2 >= 0 and SwearPos2 - SwearPos1 == 32:

                                # after trying for hours to understand why adding 38 works, I gave up. I'm often not a smart man. 
                                log.wernicke.warning(f'Adjusting audio stream by {SwearPos1 + 38} bytes')
                                data = self.SerialPortFromHead.read(SwearPos1 + 38)

                            else:
                                # It is theoretically possible for the sensor data to be cut off at the start or end of the 16038 bytes
                                # So if we're not seeing it, read in and throw away 8000 bytes and it ought to be in the middle
                                log.wernicke.warning(f'Adjusting audio stream by 8000 bytes')
                                data = self.SerialPortFromHead.read(8000)

                            # continue to the start of the loop where we should be well adjusted
                            continue

                        # if we're currently processing, put audio data onto the queue, otherwise it gets thrown away
                        if ProcessingState == True and self.PauseProcessing <= 0:

                            try:

                                buffer_queue.put(data, block=False)

                            # if the queue is full, it's a sign I need to evaluate CPU usage, so full stop
                            # happens every day. I definitely need to pare it down, but also this should just pause for a while not just
                            except queue.Full:

                                self.PauseProcessing = 10
                                log.wernicke.warning('Buffer Queue FULL! Resting.')

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

                            log.wernicke.debug('Discarded audio data.')
                            self.PauseProcessing -= 1


            # instantiate and start the thread
            HeadMic = ReadHeadMicrophone()
            HeadMic.start()

            class Audio(object):
                """Streams raw audio from microphone. Data is received in a separate thread, and stored in a buffer, to be read from."""

                # FORMAT = pyaudio.paInt16
                # Network/VAD rate-space
                RATE = 16000
                CHANNELS = 2
                BLOCKSIZE = 4000

                def __init__(self):

                    log.wernicke.debug('Initializing pyAudioAnalysis single-block classifier model...')
                    [self.block_model, self.block_MEAN, self.block_STD, self.block_class_names, self.block_mt_win, self.block_mt_step, self.block_st_win, self.block_st_step, _] = aT.load_model("wernicke_block")

                    log.wernicke.debug('Initializing pyAudioAnalysis proximity model...')
                    [self.proximity_model, self.proximity_MEAN, self.proximity_STD, self.proximity_mt_win, self.proximity_mt_step, self.proximity_st_win, self.proximity_st_step, _] = aT.load_model("wernicke_proximity", is_regression=True)

                    log.wernicke.debug(f'block_MEAN: {self.block_MEAN}')
                    log.wernicke.debug(f'block_STD: {self.block_STD}')
                    log.wernicke.debug(f'block_mt_win: {self.block_mt_win}')
                    log.wernicke.debug(f'block_mt_step: {self.block_mt_step}')
                    log.wernicke.debug(f'block_st_win: {self.block_st_win}')
                    log.wernicke.debug(f'block_st_step: {self.block_st_step}')

                    log.wernicke.debug(f'proximity_MEAN: {self.proximity_MEAN}')
                    log.wernicke.debug(f'proximity_STD: {self.proximity_STD}')
                    log.wernicke.debug(f'proximity_mt_win: {self.proximity_mt_win}')
                    log.wernicke.debug(f'proximity_mt_step: {self.proximity_mt_step}')
                    log.wernicke.debug(f'proximity_st_win: {self.proximity_st_win}')
                    log.wernicke.debug(f'proximity_st_step: {self.proximity_st_step}')

                    # var to keep track of which ear seems best based on loudness
                    self.LeftRightRatio = 1.0

                def read(self):
                    """Return a block of audio data, blocking if necessary."""

                    # There's a thread up there constantly popping stuff into this buffer queue
                    nonlocal buffer_queue

                    # first we get 2 channels from the serial port
                    # 16000 bytes is 4000 frames or 0.25s
                    in_audio = AudioSegment(data=buffer_queue.get(), sample_width=2, frame_rate=self.RATE, channels=self.CHANNELS) + 24

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
                    # num_padding_blocks = 3
                    # ring_buffer = deque(maxlen=num_padding_blocks)

                    # triggered means we're currently seeing blocks that are not silent
                    triggered = False

                    # this tracks how many consecutive blocks contain lover noises
                    # so that we can trigger streaming only after that happens several times
                    lover_blocks = 0

                    # The away team will send a signal back to the enterprise when speaking starts and stops. This keeps track. 
                    lover_speaking = False
                    # this delays the speaking stop to prevent start stop start stop start stop start stop start stop madness
                    lover_speaking_delay_stop = 0

                    # this is a global var for tracking proximity
                    nonlocal Proximity

                    while True:
                        # forever read new blocks of audio data
                        block = self.read()

                        # Convert or cast the raw audio data to numpy array
                        block_np = np.frombuffer(block, np.int16)

                        # Try to reject quick loud clicky sounds
                        maximum = (np.abs(block_np)).max()
                        mean = (np.abs(block_np)).mean()
                        avg_vs_max = mean / maximum

                        # if the block contains a huge but quick spike (a click) then drop it and skip this block
                        if avg_vs_max <= 0.075:

                            log.wernicke.debug(f'Dropped possible clicking noise. {mean} / {maximum} = {avg_vs_max}')
                            continue


                        # Run the classifier. This is ripped directly out of paura.py and carelessly sutured into place. There's so much blood! Thank you!!! 
                        [block_mt_feats, _, _] = mF.mid_feature_extraction(block_np, 16000, 4000, 4000, 800, 800)
                        block_cur_fv = (block_mt_feats[:, 0] - self.block_MEAN) / self.block_STD
                        [res, prob] = aT.classifier_wrapper(self.block_model, "svm_rbf", block_cur_fv)
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
                        if block_class == 'lover':
                            proximity_cur_fv = (block_mt_feats[:, 0] - self.proximity_MEAN) / self.proximity_STD
                            proximity_now = aT.regression_wrapper(self.proximity_model, "svm_rbf", proximity_cur_fv)
                            log.wernicke.debug(f'Heard lover with prob {block_prob:.2f} and proximity {proximity_now}')

                            # update running average
                            Proximity = ((Proximity * 6.0) + proximity_now) / 7.0


                        # NOT triggered
                        # when not triggered, it means we're not currently streaming audio for processing
                        if not triggered:
                            # ring_buffer.append(block)
                            if 'lover' in block_class:

                                # whether we're triggered or not, immediately notify that lover is speaking
                                # timing is important
                                # if lover wasn't already speaking, notify they are now
                                lover_speaking_delay_stop = 3
                                if lover_speaking == False:
                                    hey_honey({'class': 'speaking_start'})
                                    lover_speaking = True

                                # we want to wait until we have a certain number of lover blocks before we really get going
                                lover_blocks += 1
                                if lover_blocks >= 2:

                                    log.wernicke.debug('triggered')
                                    triggered = True

                                    # if we were just triggered, send all the past audio blocks that were in the queue and empty it
                                    # for f in ring_buffer:
                                    #     yield f
                                    yield block
                                    # ring_buffer.clear()

                                    # this is to track how many silent/ignore blocks we've had, so we can stop streaming at some point
                                    post_silence = 200

                            # if we got something but we're not really sure it's lover speaking, reset this counter to 0
                            else:
                                lover_blocks = 0

                                # if lover was speaking, notify they seem to have stopped
                                if lover_speaking == True:
                                    lover_speaking_delay_stop -= 1
                                    if lover_speaking_delay_stop <= 0:
                                        hey_honey({'class': 'speaking_stop'})
                                        lover_speaking = False

                        # TRIGGERED! 
                        # when triggered, it means we are currently streaming everything to the server, so just send it all
                        else:

                            # send the block whatever it is
                            yield block

                            # if this is a lover block, reset the counter, else if it's not lover determine if we should end streaming
                            if 'lover' in block_class:

                                # if lover wasn't already speaking, notify they are now
                                lover_speaking_delay_stop = 3
                                if lover_speaking == False:
                                    hey_honey({'class': 'speaking_start'})
                                    lover_speaking = True

                                # reset the counter of consecutive silent blocks, because we got one that was not
                                post_silence = 200

                            else:
    
                                # if lover was speaking, notify they seem to have stopped
                                if lover_speaking == True:
                                    lover_speaking_delay_stop -= 1
                                    if lover_speaking_delay_stop <= 0:
                                        hey_honey({'class': 'speaking_stop'})
                                        lover_speaking = False
    
                                # if there have been enough consecutive silent/ignore blocks, we're done with transmission, reset everything
                                if post_silence <= 0:
                                    log.wernicke.debug('untriggered')
                                    triggered = False
                                    lover_blocks = 0
                                    # ring_buffer.clear()
                                else:
                                    post_silence -= 1


            # https://stackoverflow.com/questions/46727787/runtimeerror-there-is-no-current-event-loop-in-thread-in-async-apscheduler
            # Experts warn: "Do not do this!" 
            # Me: "Hold my beer." 
            # Me: "loop = asyncio.get_event_loop()!!!!!!"
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            loop.set_debug(True)


            # speech recognition is much too slow for the pi, by a lot. So I'm running a server and using the gpu
            # yeah, right, like there's ever going to be useable speech recognition that's not behind a paywall locked inside somebody else's server
            # You might as well wish people would throw you their mined bitcoin for free. 
            # now we're trying to use windows speech recognition with voice attack
            # now we're going to stream audio to an ffplay.exe process
            # when something doesn't work I go out and find something new
            class ConnectAndSendAudio(threading.Thread):
                name = 'ConnectAndSendAudio'

                def __init__ (self):
                    threading.Thread.__init__(self)

                def run(self):

                    nonlocal Server_Is_Available
                    nonlocal Connected_To_Server
                    nonlocal Data_To_Server

                    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as ServerConnection:

                        # set this global since we are definitely connected and this needs data
                        Connected_To_Server = True

                        while True:

                            try:

                                # blocks here until something hits queue, and if it times out, fuck off
                                data = Data_To_Server.get(timeout=20)

                                # send the new block of audio data
                                log.wernicke.debug('Sending ' + str(len(data)) + ' bytes')
                                ServerConnection.sendto(data, ('192.168.0.22', 3001))

                            except queue.Empty:

                                # if the queue times out, we're done here
                                log.wernicke.debug('Timed out waiting for Data_To_Server')

                                # and bust out of the infinite loop
                                break

                    log.wernicke.debug('End of ConnectAndSendAudio thread')
                    Connected_To_Server = False


            # If the server is available, I want to use it. Otherwise, don't try to use it
            class SendLoveToServer(threading.Thread):
                name = 'SendLoveToServer'

                def __init__ (self):
                    threading.Thread.__init__(self)

                def run(self):
                    nonlocal loop
                    nonlocal Server_Is_Available

                    while True:
                    
                        log.wernicke.info('Sending love to server')
                        coro = loop.create_connection(lambda: MySpeechServer(loop, b'HEY_I_LOVE_YOU'), '192.168.0.22', 3000)

                        try:
                            loop.run_until_complete(coro)
                            loop.run_forever()

                        except ConnectionRefusedError:
                            log.wernicke.warning('The server refused our love')
                            Server_Is_Available = False

                        except TimeoutError:
                            log.wernicke.warning('The server is gone')
                            Server_Is_Available = False

                        except Exception as e:
                            log.wernicke.warning('Some other exception occurred. {0} {1} {2}'.format(e.__class__, e, log.format_tb(e.__traceback__)))
                            Server_Is_Available = False

                        time.sleep(300)


            # Sometimes I want to use the "server" for playing VR
            def DisableServer():

                nonlocal loop
                nonlocal Server_Is_Available

                if Server_Is_Available == True:

                    log.wernicke.info('Sending disable code to server')
                    coro = loop.create_connection(lambda: MySpeechServer(loop, b'HE_WANTS_TO_PLAY_VR'), '192.168.0.22', 3000)

                    try:
                        loop.run_until_complete(coro)
                        loop.run_forever()
                        Server_Is_Available = False

                    except ConnectionRefusedError:
                        log.wernicke.warning('The server refused our love')

                    except TimeoutError:
                        log.wernicke.warning('The server is gone')

                else:
                    log.wernicke.debug(f'Server_Is_Available: {Server_Is_Available}')

            # Start the threads.
            CheckForMessagesThread = CheckForMessages()
            CheckForMessagesThread.daemon = True
            CheckForMessagesThread.start()

            # Disabled because we gave up on doing speech recognition off-pi for a while
            # SendLoveToServerThread = SendLoveToServer()
            # SendLoveToServerThread.daemon = True
            # SendLoveToServerThread.start()

            # Start all the VAD detection stuff
            audio = Audio()

            # blocks is a collector, iterate over it and out come blocks
            blocks = audio.collector()

            # Gets blocks for                                                               ev..                                                                         er.... 
            for block in blocks:

                # Graceful shutdown
                if Shutdown:
                    break

                # if the server is available, use that to classify the new audio data, save pi cpu
                if Server_Is_Available:

                    Data_To_Server.put(block)
                    log.wernicke.info('Adding block to server queue. Queue size: {0}'.format(Data_To_Server.qsize()))

                    # if we're not connected to the server, well, connect
                    if not Connected_To_Server:

                        # we're not really connected, but if I don't put this here we'll end up with not sexy double pumping
                        Connected_To_Server = True

                        # starts a thread
                        ConnectAndSendAudioThread = ConnectAndSendAudio()
                        ConnectAndSendAudioThread.daemon = True
                        ConnectAndSendAudioThread.start()

                # if the server is not available, just do a basic "you spoke, apparently"
                # else:

                    # figure out what we wanna do when server not available

                    # Pop the result over to main process
                    # hey_honey(result)


        # log exception in the main.log
        except Exception as e:
            log.main.error('Thread died. {0} {1} {2}'.format(e.__class__, e, log.format_tb(e.__traceback__)))


# Instantiate and start the thread
thread = Wernicke()
thread.daemon = True
thread.start()

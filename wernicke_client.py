# This is basically mic_vad_streaming.py with the deepspeech chopped out and sent over wifi instead. 
# I think it will be best to do the VAD part on the pi, as long as the pi can handle that. There will be so 
# much of the time in silence, and why send all of that over the network? That would create more heat and 
# Use more power. 







# I have moved this functionality to the main python process, as a subprocess. This script is now a museum artifact. 








# from __future__ import division   # for band-reject filter
import time
from datetime import datetime
import logging as log
import threading, collections, queue, os, os.path
import numpy as np
import pyaudio
import wave
from pydub import AudioSegment
import pydub.scipy_effects
import psutil
import socket
from pyAudioAnalysis import ShortTermFeatures as sF
from pyAudioAnalysis import MidTermFeatures as mF
from pyAudioAnalysis import audioTrainTest as aT
# import scipy.signal as sig
# Temporary to figure out memory
# import resource
# from guppy import hpy
# h=hpy()

# Setup the log file
log.basicConfig(filename='wernicke_client.log', filemode='a', format='%(asctime)s - %(levelname)s - %(message)s', level=log.DEBUG)
# log.getLogger('asyncio').setLevel(log.DEBUG)

# For transmitting audio over wifi. This is probably stupid, but I am unaware.
# As it turns out, it probably wasn't necessary, because socket could have worked, too
# But asyncio provided the eof thing which was useful for signalling the end of data
import asyncio

# I used to use a deque
# I should convert this to a regular fifo queue. 
# When all you have is a hammer, guess what happens.
# Fixed.
# from collections import deque

# This is the same ship from wernicke_server.py with deepspeech ripped out
class ModelsMotherShip():
    def __init__(self):
        # load segment model
        log.info('Initializing pyAudioAnalysis classifier model...')
        [self.classifier, self.MEAN, self.STD, self.class_names, self.mt_win, self.mt_step, self.st_win, self.st_step, _] = aT.load_model("wernicke_server_model")
        self.fs = 16000

    def WhatIsThis(self, data):
        # Convert or cast the raw audio data to numpy array
        log.debug('Converting data to numpy')
        AccumulatedData_np = np.frombuffer(data, np.int16)

        seg_len = len(AccumulatedData_np)
        log.debug('seg_len ' + str(seg_len))

        # Run the classifier. This is ripped directly out of paura.py and carelessly sutured into place. There's so much blood! Thank you!!! 
        log.debug('Running classifier')
        try:
            [mt_feats, _, _] = mF.mid_feature_extraction(AccumulatedData_np, self.fs,
                                                         seg_len,
                                                         seg_len,
                                                         round(self.fs * self.st_win),
                                                         round(self.fs * self.st_step)
                                                         )
            cur_fv = (mt_feats[:, 0] - self.MEAN) / self.STD
        except ValueError:
            log.error('Yeah, that thing happened')
        # classify vector:
        [res, prob] = aT.classifier_wrapper(self.classifier, "svm_rbf", cur_fv)
        win_class = self.class_names[int(res)]
        win_prob = round(prob[int(res)], 2)

        log.debug('Classified {0:s} with probability {1:.2f}'.format(win_class, win_prob))

        # return an object
        return {
            'class': win_class,
            'probability': win_prob,
            'text': 'undefined',
        }
        # return '{"class": "' + win_class + '", "probability": ' + str(win_prob) + ', "text": "undefined"}'

# This is a queue that holds audio segments, of random lengths, before getting shipped to the server
Data_To_Server = queue.Queue(maxsize = 3)

# If the speech server is not on the network, I don't want to keep trying over and over and queuing
# So when the service starts, it will send a test message first, then set this to True if the server responded
Server_Is_Available = False

# Send message to the main process christine.py
def hey_honey(love):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            log.debug('Connecting...')
            s.connect(('localhost', 3001))
            log.debug(f'Sending: {love}')
            s.sendall(love)
        except ConnectionRefusedError:
            log.warning('Send to christine.py failed.')
 
# speech recognition is much too slow for the pi, by a lot. So I'm running a server and using the gpu
class MyDeepSpeechServer(asyncio.Protocol):
    def __init__(self, loop, data):
        self.loop = loop
        self.data = data

    def connection_made(self, transport):
        log.debug('Connected to server')
        # transport.set_write_buffer_limits(low=16384, high=262144)
        # log.debug('get_write_buffer_limits: ' + str(transport.get_write_buffer_limits()))
        # log.debug('can_write_eof: ' + str(transport.can_write_eof()))
        log.info('Sending ' + str(len(self.data)) + ' bytes')
        transport.write(self.data)
        transport.write_eof()
        # log.debug('Write buffer size: ' + str(transport.get_write_buffer_size()))
        log.debug('End of connection_made')

    def data_received(self, data):
        global Server_Is_Available
        log.debug('Data received, length: ' + str(len(data)))
        # This is the response from the server we should get. Servers can love! 
        if data == b'I_LOVE_YOU_TOO':
            log.info('The server loves me')
        else:
            log.info('Data received: ' + data.decode())
            hey_honey(data)
            # result = json.loads(result_json)
            # log.info(result['class'])
        Server_Is_Available = True

    def connection_lost(self, exc):
        global Server_Is_Available
        log.debug('Server connection closed')
        if exc != None:
            log.warning('Error: ' + exc)
            Server_Is_Available = False
        self.loop.stop()

class Audio(object):
    """Streams raw audio from microphone. Data is received in a separate thread, and stored in a buffer, to be read from."""

    FORMAT = pyaudio.paInt16
    # Network/VAD rate-space
    RATE = 16000
    CHANNELS = 4
    BLOCKSIZE = 4096

    def __init__(self):

        log.info('Initializing pyAudioAnalysis silence classifier model...')
        [self.classifier, self.MEAN, self.STD, self.class_names, self.mt_win, self.mt_step, self.st_win, self.st_step, _] = aT.load_model("wernicke_server_model_single_frame")

        def proxy_callback(in_data, frame_count, time_info, status):
            #pylint: disable=unused-argument
            self.buffer_queue.put(in_data)
            return (None, pyaudio.paContinue)
        self.buffer_queue = queue.Queue()
        self.pa = pyaudio.PyAudio()

        kwargs = {
            'format': self.FORMAT,
            'channels': self.CHANNELS,
            'rate': self.RATE,
            'input': True,
            'frames_per_buffer': self.BLOCKSIZE,
            'stream_callback': proxy_callback,
        }

        self.stream = self.pa.open(**kwargs)
        self.stream.start_stream()

    def read(self):
        """Return a block of audio data, blocking if necessary."""

        # So basically, first we get all 4 channels from the usb microphone array
        in_audio = AudioSegment(data=self.buffer_queue.get(), sample_width=2, frame_rate=self.RATE, channels=self.CHANNELS)

        # Split the interleaved data into separate channels, left, right, in head, in vagina
        in_audio_split = in_audio.split_to_mono()

        #combine signal from left and right ears
        both_ears = in_audio_split[0].overlay(in_audio_split[1])

        # compute the loudness of sound
        loudness_both_ears = both_ears.rms
        loudness_head = in_audio_split[2].rms

        # compute the ratio of inside head vs outside
        loudness_ratio = loudness_head / loudness_both_ears

        # If the ratio is high, that is, the sound is loud inside head vs outside, this means the sound is coming from the speaker and we want to ignore that so my wife doesn't talk to herself, as cute as that would be
        if loudness_ratio < 1.6:
            # log.debug(f'loudness_ratio: {loudness_ratio:.1f}')

            # wf = wave.open('{0}.wav'.format(os.path.join('saved_wavs_single_frame', str(int(time.time())))), 'wb')
            # wf.setnchannels(1)
            # wf.setsampwidth(2)
            # wf.setframerate(16000)
            # wf.writeframes(both_ears.raw_data)
            # wf.close()

            return both_ears.raw_data
        else:
            log.debug(f'loudness_ratio: {loudness_ratio:.1f} (dropped)')
            return None

    def frame_generator(self):
        """Generator that yields all audio frames from microphone."""
        while True:
            yield self.read()

    def collector(self, frames=None): # increased padding_ms from 300 to 700 to try and improve speech getting chopped off
        """Generator that yields series of consecutive audio frames comprising each utterence, separated by yielding a single None.
            Determines voice activity by ratio of frames in padding_ms. Uses a buffer to include padding_ms prior to being triggered.
            Example: (frame, ..., frame, None, frame, ..., frame, None, ...)
                      |---utterence---|        |---utterence---|
        """
        if frames is None: frames = self.frame_generator()
        num_padding_frames = 3
        ring_buffer = collections.deque(maxlen=num_padding_frames)
        triggered = False

        for frame in frames:

            if frame != None:




                # Convert or cast the raw audio data to numpy array
                frame_np = np.frombuffer(frame, np.int16) #.astype(np.float32, order='C') / 32768.0    <-- if we ever need to convert to float

                # Try to reject quick loud clicky sounds
                maximum = (np.abs(frame_np)).max()
                mean = (np.abs(frame_np)).mean()
                # energy = sF.energy(frame_np)
                avg_vs_max = mean / maximum
                # avg_vs_max = sF.energy(frame_np) / maximum

                # Convert float back to int16, if we ever need to
                # frame_np = np.int16(frame_np * 32768.0)

                if avg_vs_max > 0.1:
                    # log.debug(f'{mean} / {maximum} = {avg_vs_max}')
                    # Run the classifier. This is ripped directly out of paura.py and carelessly sutured into place. There's so much blood! Thank you!!! 
                    try:
                        [mt_feats, _, _] = mF.mid_feature_extraction(frame_np, 16000,
                                                                     4096,
                                                                     4096,
                                                                     800,
                                                                     800
                                                                     )
                        cur_fv = (mt_feats[:, 0] - self.MEAN) / self.STD
                    except ValueError:
                        log.error('Yeah, that thing happened')
                    # classify vector:
                    # log.debug('win: {0}  step: {0}'.format(round(16000 * self.st_win), round(16000 * self.st_step)))
                    [res, prob] = aT.classifier_wrapper(self.classifier, "svm_rbf", cur_fv)
                    win_class = self.class_names[int(res)]
                    win_prob = round(prob[int(res)], 2)
                    log.debug('Classified {0:s} with probability {1:.2f}'.format(win_class, win_prob))
                else:
                    log.debug(f'Dropped possible clicking noise. {mean} / {maximum} = {avg_vs_max}')
                    win_class = 'silence'

                if win_class == 'silence':
                    silence = True
                else:
                    silence = False

                    # temporary until we have exhaustive samples
                    # wf = wave.open('{0}_notsilence.wav'.format(os.path.join('saved_wavs_single_frame', str(int(time.time())))), 'wb')
                    # wf.setnchannels(1)
                    # wf.setsampwidth(2)
                    # wf.setframerate(16000)
                    # wf.writeframes(frame)
                    # wf.close()

                if not triggered:
                    ring_buffer.append(frame)
                    if not silence:
                        log.debug('triggered')
                        triggered = True
                        post_silence = 2
                        for f in ring_buffer:
                            yield f
                        ring_buffer.clear()

                else:
                    yield frame
                    if silence:
                        if post_silence <= 0:
                            log.debug('untriggered')
                            triggered = False
                            yield None
                        post_silence -= 1
                    else:
                        post_silence = 2

    def destroy(self):
        self.stream.stop_stream()
        self.stream.close()
        self.pa.terminate()

# So, this script will be a separate process. I want to communicate with the christine.py process, to prevent my wife from talking over me, because it's polite 
WifePID = None
for proc in psutil.process_iter(['pid', 'cmdline']):
    if 'christine.py' in proc.info['cmdline']:
        WifePID = proc.info['pid']
        log.info('Brain located. WifePID = ' + str(WifePID))
        break
if WifePID == None:
    log.critical('Failed to locate Christine\'s Brain.')
    exit()
IsSpeaking = False

loop = asyncio.get_event_loop()
loop.set_debug(True)

# Putting this in a thread because it was blocking. Is this the correct way? I dunno. Will it work? If you're reading this, it worked. 
class GetFromQueueSendToServer(threading.Thread):
    name = 'GetFromQueueSendToServer'
    def __init__ (self):
        threading.Thread.__init__(self)
    def run(self):
        global loop
        global Server_Is_Available
        global Data_To_Server
        while True:
            log.debug('Waiting for Data_To_Server')
            NewData = Data_To_Server.get() # blocks here until something hits queue
            log.debug('Got data from Data_To_Server queue')
            # This is for the server connection. Lots of weird voodoo, promises, futures, bullshit. 
            coro = loop.create_connection(lambda: MyDeepSpeechServer(loop, NewData), '192.168.0.88', 3000)
            try:
                loop.run_until_complete(coro) # This also blocks until the entire connecting, waiting, getting result is complete. Or it should. I'm not a smart man. 
                loop.run_forever()
                Server_Is_Available = True
            except ConnectionRefusedError:
                log.warning('Server connection refused')
                Server_Is_Available = False
            except TimeoutError: # might not work
                log.warning('Server connection timed out')
                Server_Is_Available = False

# If the server is available, I want to use it. Otherwise, I'll just save to file. 
class SendLoveToServer(threading.Thread):
    name = 'SendLoveToServer'
    def __init__ (self):
        threading.Thread.__init__(self)
    def run(self):
        global loop
        global Server_Is_Available
        while True:
            if Server_Is_Available == False:
                log.info('Sending love to server')
                coro = loop.create_connection(lambda: MyDeepSpeechServer(loop, b'HEY_I_LOVE_YOU'), '192.168.0.88', 3000)
                try:
                    loop.run_until_complete(coro)
                    loop.run_forever()
                    Server_Is_Available = True
                except ConnectionRefusedError:
                    log.warning('The server refused our love')
                except TimeoutError: # might not work
                    log.warning('The server is gone')
            else:
                log.debug(f'Server_Is_Available: {Server_Is_Available}')

            # log.info('Memory usage: {0}'.format(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)) #temporary
            # hp = h.heap()
            # log.debug('The largest fucking thing: {0}'.format(hp.byid[0].sp))
            # log.debug('The second largest fucking thing: {0}'.format(hp.byid[1].sp))
            # log.info(str(h.heap()))
            time.sleep(300)

# Start the threads. 
GetFromQueueSendToServer().start()
SendLoveToServer().start()

# Start up the classifier model
ClassifierModel = ModelsMotherShip()

# Start all the VAD detection stuff
audio = Audio()

frames = audio.collector()

os.makedirs('saved_wavs', exist_ok=True)

# Basically this area accumulates the audio frames. VAD filters. When VAD assembles a complete utterance, it sends signals to the main process and sends the entire utterance over to the server
AccumulatedData = bytearray()
for frame in frames:
    if frame is not None:
        # The frame is not None, which means there's new audio data, so add it on
        if IsSpeaking == False:
            IsSpeaking = True
            os.kill(WifePID, 45)
        AccumulatedData.extend(frame)
    else:
        # When frame is None, that signals the end of audio data. Go ahead and do what we want to do with the complete data
        if IsSpeaking == True:
            IsSpeaking = False
            os.kill(WifePID, 44)
        # Apply a high pass filter to the audio to strip off the low noise. Get the loudness because we want to know that and keep an average
        # I removed high pass filter because when I actually listened to the mic output it doesn't seem noisy
        # Putting it back temporarily so that classification works again. I need to retrain using unfiltered samples. 
        FilteredData = AudioSegment(data=AccumulatedData, sample_width=2, frame_rate=16000, channels=1).high_pass_filter(500, order = 2)
        FilteredDataLoudness = FilteredData.rms
        log.debug(f'Raw loudness: {FilteredDataLoudness}')

        FilteredData = FilteredData.raw_data

        # If the server is avail, send it there and wait for a response, if not we'll process it locally
        if Server_Is_Available:
            Data_To_Server.put(FilteredData)
            log.info('Sending utterance. Queue size: {0}'.format(Data_To_Server.qsize()))
        else:
            # If the server is not available, use the built-in classifier. Works ok, not bad CPU load
            result = ClassifierModel.WhatIsThis(FilteredData)

            # Pop the result over to christine.py
            # avoiding import json to save memory
            hey_honey('{{"loudness": {0}, "class": "{1}", "probability": {2}, "text": "undefined"}}'.format(FilteredDataLoudness, result['class'], result['probability']).encode())

            # save the utterance to a wav file. I hope later I'll be able to use this for training a better model, after I learn how to do that. Actually, I know how to do that, now. 

            # log.info('Saving utterance to file')
            # wf = wave.open('{0}_{1}.wav'.format(os.path.join('saved_wavs', str(int(time.time()))), result['class']), 'wb')
            # wf.setnchannels(1)
            # wf.setsampwidth(2)
            # wf.setframerate(16000)
            # wf.writeframes(FilteredData)
            # wf.close()

        AccumulatedData = bytearray()

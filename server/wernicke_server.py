import time
import logging as log
import asyncore
import threading, collections, queue, os, os.path
import deepspeech
import numpy as np
import scipy
import wave
import asyncio
from pyAudioAnalysis import ShortTermFeatures as sF
from pyAudioAnalysis import MidTermFeatures as mF
from pyAudioAnalysis import audioTrainTest as aT
import struct
import json

# Setup the log file
log.basicConfig(filename='wernicke_server.log', filemode='a', format='%(asctime)s - %(levelname)s - %(message)s', level=log.DEBUG)
# log.getLogger('asyncio').setLevel(log.DEBUG)

class ModelsMotherShip():
    def __init__(self):
        self.BEAM_WIDTH = 500
        self.LM_ALPHA = 0.75
        self.LM_BETA = 1.85
        self.model_dir = 'DeepSpeech/data/wernicke/model/'
        self.model_file = os.path.join(self.model_dir, 'output_graph.pb')
        # self.model_dir = 'deepspeech-0.6.0-models/'
        # self.model_file = os.path.join(self.model_dir, 'output_graph.pbmm')
        self.lm_file = os.path.join(self.model_dir, 'lm.binary')
        self.trie_file = os.path.join(self.model_dir, 'trie')

        self.save_dir = 'saved_wavs'
        os.makedirs(self.save_dir, exist_ok=True)

        # load segment model
        log.info('Initializing pyAudioAnalysis classifier model...')
        [self.classifier, self.MEAN, self.STD, self.class_names, self.mt_win, self.mt_step, self.st_win, self.st_step, _] = aT.load_model("wernicke_server_model")
        self.fs = 16000

        log.info('Initializing deepspeech model...')
        self.model = deepspeech.Model(self.model_file, self.BEAM_WIDTH)
        # Temporarily disabling this. I don't think I have nearly enough samples to start doing LM and trie files, etc
        self.model.enableDecoderWithLM(self.lm_file, self.trie_file, self.LM_ALPHA, self.LM_BETA)

        log.info('Models ready.')

    def WhatIsThis(self, data):
        # There are two completely separate models, one is a classifier that uses pyaudioanalysis, the other is a deepspeech model

        # Convert or cast the raw audio data to numpy array
        log.debug('Converting data to numpy')
        if len(data) % 2 != 0:
            log.critical('Data length: {0}'.format(len(data)))
            log.critical('Data: {0}'.format(data))
            return { #bullshit
                'loudness': 0.0,
                'class': 'bullshit',
                'probability': 1.0,
                'text': 'fuckitall',
            }
        AccumulatedData_np = np.frombuffer(data, np.int16)

        # Get the loudness, hope this works
        rms = np.sqrt(np.mean(AccumulatedData_np**2))
        log.debug(f'Raw loudness: {rms}')
        # normalize it, make it between 0.0 and 1.0. 
        # rms = round((rms - 20.0) / 45, 2)
        # rms = float(np.clip(rms, 0.0, 1.0))

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
            log.critical('Data length: {0}'.format(len(data)))
            log.critical('Data: {0}'.format(data))
            return { #bullshit
                'loudness': 0.0,
                'class': 'bullshit',
                'probability': 1.0,
                'text': 'fuckitall',
            }
        # classify vector:
        [res, prob] = aT.classifier_wrapper(self.classifier, "svm_rbf", cur_fv)
        win_class = self.class_names[int(res)]
        win_prob = round(prob[int(res)], 2)

        log.info('Classified {0:s} with probability {1:.2f}'.format(win_class, win_prob))

        # Run the accumulated audio data through deepspeech, if it's speech
        if win_class == 'lover':
            log.debug('Running deepspeech model')
            text = self.model.stt(AccumulatedData_np)
            log.info('Recognized: %s', text)
        else:
            text = 'undefined'

        # Save the utterance to a wav file. I hope later I'll be able to use this for training a better model, after I learn how to do that. 

        # log.debug('Saving wav file')
        # wf = wave.open(os.path.join(self.save_dir, str(int(time.time())) + '_' + win_class + '_' + text.replace(' ', '_') + '.wav'), 'wb')
        # wf.setnchannels(1)
        # wf.setsampwidth(2)
        # wf.setframerate(16000)
        # wf.writeframes(data)
        # wf.close()

        # return an object
        return {
            'loudness': rms,
            'class': win_class,
            'probability': win_prob,
            'text': text,
        }

# Start up the models
AllTheModels = ModelsMotherShip()

# The wernicke_client.py connects to this script and sends audio data. This is where it's received and processed. 
class AudioAnalysisServer(asyncio.Protocol):

    def connection_made(self, transport):
        peername = transport.get_extra_info('peername')
        log.info('Connection from {}'.format(peername))
        self.transport = transport
        self.AccumulatedData = bytearray()

    def data_received(self, data):
        log.debug('Data received, length: ' + str(len(data)))
        self.AccumulatedData.extend(data)

    def eof_received(self):
        if self.AccumulatedData == b'HEY_I_LOVE_YOU':
            # Say it back, because you mean it
            log.info('Received: HEY_I_LOVE_YOU')
            log.info('Sending: I_LOVE_YOU_TOO')
            self.transport.write(b'I_LOVE_YOU_TOO')
        else:
            # Classify and analyze, lift weights. 
            log.info('Processing data')
            result = AllTheModels.WhatIsThis(self.AccumulatedData)
            result_json = json.dumps(result)

            # Send result
            log.info('Sending back result: ' + result_json)
            self.transport.write(result_json.encode())

        # Close the connection
        log.debug('Close the client socket')
        self.transport.close()

        # Reset the bytearray back to 0
        self.AccumulatedData = bytearray()

    def connection_lost(self, exc):
        log.info('The client closed the connection')

loop = asyncio.get_event_loop()
# Each client connection will create a new protocol instance
coro = loop.create_server(AudioAnalysisServer, '192.168.0.88', 3000)
server = loop.run_until_complete(coro)

# Serve requests until Ctrl+C is pressed
log.info('Serving on {}'.format(server.sockets[0].getsockname()))
try:
    loop.run_forever()
except KeyboardInterrupt:
    pass

# Close the server
server.close()
loop.run_until_complete(server.wait_closed())
loop.close()

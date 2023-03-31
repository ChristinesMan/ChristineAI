import time
import logging as log
# import asyncore
import threading, collections, queue, os, os.path
# from multiprocessing import Process, Pipe
import whisper
import numpy as np
import scipy
import wave
import asyncio
# from pyAudioAnalysis import ShortTermFeatures as sF
# from pyAudioAnalysis import MidTermFeatures as mF
# from pyAudioAnalysis import audioTrainTest as aT
import json
import requests

# Setup the log file
log.basicConfig(filename='wernicke_server.log', filemode='a', format='%(asctime)s - %(levelname)s - %(message)s', level=log.INFO)
# log.getLogger('asyncio').setLevel(log.DEBUG)

# Queue for audio waiting for decoding or analysis
Audio_Queue = queue.Queue(maxsize=10)

# This thread waits for full utterances to hit the queue and sends them over there
class Audio_Queue_Processor(threading.Thread):
    name = 'Audio_Queue_Processor'

    def __init__ (self):
        threading.Thread.__init__(self)

        self.save_dir = 'saved_wavs'
        os.makedirs(self.save_dir, exist_ok=True)

        # load whisper model
        log.info('Initializing whisper model...')
        self.whisper_model = whisper.load_model("base.en")

    def run(self):

        while True:

            # blocks here until something hits queue
            Audio_Data = Audio_Queue.get()

            # convert the int16 data to the format that whisper expects, which is float32 on CPU. For GPU maybe it's float16.
            Audio_Data_np = np.frombuffer(Audio_Data, np.int16).astype(np.float32, order='C') / 32768.0

            # put the audio data into the magic black box
            Transcribe_Result = whisper.transcribe(model=self.whisper_model, audio=Audio_Data_np, language='en', fp16=False)

            log.info(Transcribe_Result)

            # send the words over to the http server
            # she will say "OK" but we'll just throw the response away
            requests.post('http://christine.wifi/wernicke/whisper', data={'words': Transcribe_Result['text']})

            # # temp data saving
            # wf = wave.open(os.path.join(self.save_dir, str(int(time.time())) + '.wav'), 'wb')
            # wf.setnchannels(1)
            # wf.setsampwidth(2)
            # wf.setframerate(16000)
            # wf.writeframes(Audio_Data)
            # wf.close()


# The wernicke.py module on pi connects to this script and sends audio data. This is where it's received. 
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

        # the client (my wife) sends these little love notes to the server to verify whether the server is available or not
        if self.AccumulatedData == b'HEY_I_LOVE_YOU':
            # Say it back, because you mean it
            log.info('Received: HEY_I_LOVE_YOU')
            log.info('Sending: I_LOVE_YOU_TOO')
            self.transport.write(b'I_LOVE_YOU_TOO')

        # we'll be accepting the audio data and putting it on a queue. 
        # so we respond right away as to not block. 
        # The audio analysis results will be sent back via http calls.
        # In the future I want multiprocessing to enable concurrent processing
        else:

            Audio_Queue.put(self.AccumulatedData, block=False)
            self.transport.write(b'OKAY_DOKAY')

        # Close the connection
        log.debug('Close the client socket')
        self.transport.close()

        # Reset the bytearray back to 0
        self.AccumulatedData = bytearray()

    def connection_lost(self, exc):
        log.debug('The client closed the connection')


if __name__ == "__main__":

    # Start the threads.
    Audio_Queue_Processor_Thread = Audio_Queue_Processor()
    Audio_Queue_Processor_Thread.daemon = True
    Audio_Queue_Processor_Thread.start()


    # loops, events, coroutines, promises, and other incomprehensible gibberish
    # A fine black box

    loop = asyncio.get_event_loop()
    # Each client connection will create a new protocol instance
    coro = loop.create_server(AudioAnalysisServer, '0.0.0.0', 3000)
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

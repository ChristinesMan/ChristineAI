"""This script will run from various machines on the local network to provide speech synthesis to my pi py wife."""
import os
import os.path
import argparse
import time
import threading
import queue
from multiprocessing.managers import BaseManager
from pydub import AudioSegment
import numpy as np

# I dunno why, but when I added the TTS import, logging broke
# Maybe someday I will try to figure out why
# But for now I don't really care that much, just print errors
# import logging as log

from TTS.api import TTS
import requests

# this shouldn't ever change, or leave
WIFE_ADDRESS = "christine.wifi"


class ILoveYouPi(threading.Thread):
    """This thread sends love to the raspberry pi to announce it's available"""

    name = "ILoveYouPi"

    def __init__(self, server_name, server_host, server_rating, use_gpu):
        threading.Thread.__init__(self)

        # these will be different per server
        self.server_name = server_name
        self.server_host = server_host
        self.server_rating = server_rating
        self.use_gpu = use_gpu

        # self-destruct code
        self.server_shutdown = False

    def run(self):

        while True:

            # we sleep first, or else wife tries to connect way before it's ready
            time.sleep(42)

            print('Saying hello.')

            try:

                # signal from the client that something fucked up and to go figure it out yourself, aka die
                if self.server_shutdown is True:
                    os.system("systemctl restart broca.service")

                else:

                    # let wife know we're up and ready to fuck.
                    requests.post(
                        url=f"http://{WIFE_ADDRESS}/broca/hello",
                        data={"server_name": self.server_name, "server_host": self.server_host, "server_rating": self.server_rating},
                        timeout=10,
                    )

            except Exception as ex: # pylint: disable=broad-exception-caught

                print(ex)


class SexyVoiceFactory(threading.Thread):
    """This thread waits for new text to say"""

    name = "SexyVoiceFactory"

    def __init__(self, server_name, server_host, server_rating, use_gpu):
        threading.Thread.__init__(self)

        # these will be different per server
        self.server_name = server_name
        self.server_host = server_host
        self.server_rating = server_rating
        self.use_gpu = use_gpu

        # queues for inbound audio and outbound transcriptions
        self.text_queue = None
        self.audio_queue = None

        # load TTS model
        print("Initializing TTS model...")
        self.tts_model = TTS(model_path="./tts_model/model.pth", config_path="./tts_model/config.json", gpu=True)

    def run(self):

        # Queue for text waiting for speech synthesis
        self.text_queue = queue.Queue(maxsize=30)

        # Queue for the other direction, audio data back to sender
        self.audio_queue = queue.Queue(maxsize=30)

        while True:

            # blocks here until something hits queue
            # this queue object is being shared with client processes
            sound = self.text_queue.get()

            # log it
            print("Received sound: '%s' Queue sizes: %s / %s", sound, self.text_queue.qsize(), self.audio_queue.qsize())

            # put the text into the magic black box
            # which should yield speech by arcane mathematical processes
            audio_data = self.tts_model.tts(sound['text'])

            # log it
            print("Speech synthesis complete.")

            # convert. My TTS model is 48000 and Christine uses wav data at 44100
            # so this will be all ready to be saved into a wav file and played
            audio_data_np = np.array(audio_data, dtype=np.float32)
            audio_data_int_np = np.int16(audio_data_np * 32768.0)
            audio_segment = AudioSegment(data=bytes(audio_data_int_np), sample_width=2, frame_rate=48000, channels=1)
            sound['audio_data'] = audio_segment.set_frame_rate(44100).raw_data

            # pop result onto the queue where the client can get() it
            try:
                self.audio_queue.put(sound, block=False)
            except queue.Full:
                print('audio_queue hit a queue.Full')
                os.system("systemctl restart broca.service")


# magic as far as I'm concerned
# A fine black box
class QueueManager(BaseManager):
    """Black box stuff"""

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--server_name", help="What's your name?")
    parser.add_argument("--server_host", help="Where can I find you?")
    parser.add_argument("--server_rating", help="How big are you?")
    parser.add_argument("--use_gpu", help="You want to use lube?", type=bool)
    args = parser.parse_args()

    # start the threads
    i_love_yous = ILoveYouPi(server_name=args.server_name, server_host=args.server_host, server_rating=args.server_rating, use_gpu=args.use_gpu)
    i_love_yous.daemon = True
    i_love_yous.start()
    sexy_voice = SexyVoiceFactory(server_name=args.server_name, server_host=args.server_host, server_rating=args.server_rating, use_gpu=args.use_gpu)
    sexy_voice.daemon = True
    sexy_voice.start()

    # start server thing
    QueueManager.register("get_text_queue", callable=lambda: sexy_voice.text_queue)
    QueueManager.register("get_audio_queue", callable=lambda: sexy_voice.audio_queue)
    QueueManager.register("get_server_shutdown", callable=lambda: i_love_yous.server_shutdown)
    manager = QueueManager(address=("0.0.0.0", 10000), authkey=b'fuckme')
    server = manager.get_server()
    server.serve_forever()

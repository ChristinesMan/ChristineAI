"""This script will run from various machines on the local network to provide audio analysis to my pi py wife."""
import os
import os.path
import argparse
import time
import logging as log
import threading
import queue
from multiprocessing.managers import BaseManager
import wave
import whisper
import numpy as np

# import scipy
# from pyAudioAnalysis import ShortTermFeatures as sF
# from pyAudioAnalysis import MidTermFeatures as mF
# from pyAudioAnalysis import audioTrainTest as aT
import requests

# this shouldn't ever change, or leave
WIFE_ADDRESS = "christine.wifi"

# Setup the log file
log.basicConfig(
    filename="wernicke_server.log",
    filemode="a",
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=log.DEBUG,
)


class ILoveYouPi(threading.Thread):
    """This thread sends love to the raspberry pi to announce it's available to process audio
    The plan is to have several of these server processes on the network as backup.
    The wife can keep track of what's available and use the server with the best rating.
    """

    name = "ILoveYouPi"

    def __init__(self, server_name, server_host, server_rating, server_model):
        threading.Thread.__init__(self)

        # these will be different per server
        self.server_name = server_name
        self.server_host = server_host
        self.server_rating = server_rating
        self.server_model = server_model

        # self-destruct code
        self.server_shutdown = False

    def run(self):
        while True:

            # we sleep first, or else wife tries to connect way before it's ready
            time.sleep(69)

            log.debug('Saying hello.')

            try:

                # signal from the client that something fucked up and to go figure it out yourself, aka die
                if self.server_shutdown is True:
                    os.system("systemctl restart wernicke.service")

                else:

                    # let wife know we're up. And so hard for you.
                    requests.post(
                        url=f"http://{WIFE_ADDRESS}/wernicke/hello",
                        data={"server_name": self.server_name, "server_host": self.server_host, "server_rating": self.server_rating},
                        timeout=10,
                    )

            except Exception as ex: # pylint: disable=broad-exception-caught

                log.warning(ex)


class SausageFactory(threading.Thread):
    """This thread waits for new audio data.
    When audio pops into one queue, it does processing and barfs up the result into another queue.
    So it's kind of like a sausage factory.
    Fucken A dude, now I'm going to call it that."""

    name = "SausageFactory"

    def __init__(self, server_name, server_host, server_rating, server_model):
        threading.Thread.__init__(self)

        # these will be different per server
        self.server_name = server_name
        self.server_host = server_host
        self.server_rating = server_rating
        self.server_model = server_model

        # queues for inbound audio and outbound transcriptions
        self.audio_queue = None
        self.result_queue = None

        # load whisper model
        log.info("Initializing whisper model...")
        self.whisper_model = whisper.load_model(self.server_model)

        # I may want to save wavs for future analysis
        # perhaps an archaeologist will discover them
        # in 1000 years this stupid monkey shit could be priceless
        self.save_dir = "saved_wavs"
        os.makedirs(self.save_dir, exist_ok=True)

    def run(self):

        # Queue for audio waiting for decoding or analysis
        self.audio_queue = queue.Queue(maxsize=30)

        # Queue for the other direction, responses back to sender
        self.result_queue = queue.Queue(maxsize=30)

        while True:
            # blocks here until something hits queue
            # this queue object is being shared with client processes
            audio_data = self.audio_queue.get()

            # log it
            log.debug("Received audio. Queue sizes: %s / %s", self.audio_queue.qsize(), self.result_queue.qsize())

            # convert the int16 data to the format that whisper expects, which is float32 on CPU. For GPU maybe it's float16. I dunno.
            audio_data_np = (
                np.frombuffer(audio_data, np.int16).astype(np.float32, order="C") / 32768.0
            )

            # put the audio data into the magic black box
            transcribe_result = whisper.transcribe(
                model=self.whisper_model, audio=audio_data_np, language="en", fp16=False
            )

            # # log it
            log.info(transcribe_result)

            # if the no_speech_prob is very high, just drop it
            # I also need to review the logs later and deal with phantoms
            # "Thanks for watching!" is obviously a glitch in the whisper training
            # "Go to Beadaholique.com for all of your beading supplies needs!"
            # Um, I would never say such ridiculous things.
            for transcribe_segment in transcribe_result["segments"]:
                if transcribe_segment["no_speech_prob"] > 35.0:
                    log.info(
                        "DROP due to no_speech_prob %s%%: %s",
                        int(transcribe_segment["no_speech_prob"] * 100),
                        transcribe_segment["text"],
                    )

                else:
                    log.info(
                        "ACCEPT, no_speech_prob %s%%: %s",
                        int(transcribe_segment["no_speech_prob"] * 100),
                        transcribe_segment["text"],
                    )

                    # pop result onto the queue where the client can get() it
                    # been having issues with queue.Full, so going to catch that
                    # I think there's just more than 10 segments, so upping that too
                    try:
                        self.result_queue.put(transcribe_segment["text"], block=False)
                    except queue.Full:
                        log.error('result hit a queue.Full')
                        os.system("systemctl restart wernicke.service")

            # temp data saving
            try:
                wav_file = wave.open(
                    os.path.join(self.save_dir, f"{int(time.time())}{transcribe_result['text'].replace(' ', '_').lower()}.wav"), "wb"
                )
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(16000)
                wav_file.writeframes(audio_data)
                wav_file.close()
            except OSError as ex:
                log.warning("OSError saving wav. %s", ex)


# magic as far as I'm concerned
# A fine black box
class QueueManager(BaseManager):
    """Black box stuff"""

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--server_name", help="What's your name?")
    parser.add_argument("--server_host", help="Where can I find you?")
    parser.add_argument("--server_rating", help="How big are you?")
    parser.add_argument("--server_model", help="Are you beautiful?")
    args = parser.parse_args()

    # start the threads
    i_love_yous = ILoveYouPi(server_name=args.server_name, server_host=args.server_host, server_rating=args.server_rating, server_model=args.server_model)
    i_love_yous.daemon = True
    i_love_yous.start()
    sausages = SausageFactory(server_name=args.server_name, server_host=args.server_host, server_rating=args.server_rating, server_model=args.server_model)
    sausages.daemon = True
    sausages.start()

    # start server thing
    QueueManager.register("get_audio_queue", callable=lambda: sausages.audio_queue)
    QueueManager.register("get_result_queue", callable=lambda: sausages.result_queue)
    QueueManager.register("get_server_shutdown", callable=lambda: i_love_yous.server_shutdown)
    manager = QueueManager(address=("0.0.0.0", 3000), authkey=b'fuckme')
    server = manager.get_server()
    server.serve_forever()

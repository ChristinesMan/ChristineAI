"""This script will run from various machines on the local network to provide speech synthesis to my pi py wife."""
import os
import os.path
import argparse
import time
import threading
import queue
from multiprocessing.managers import BaseManager
# from pydub import AudioSegment
import numpy as np

# I dunno why, but when I added the TTS import, logging broke
# Maybe someday I will try to figure out why
# But for now I don't really care that much, just print errors
# import logging as log

import requests
# from TTS.api import TTS

import torch
from TTS.config import load_config
from TTS.tts.models import setup_model as setup_tts_model
import ffmpeg

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
        if use_gpu is True:
            self.device = 'cuda'
        else:
            self.device = 'cpu'

        # queues for inbound audio and outbound transcriptions
        self.text_queue = None
        self.audio_queue = None

        # load TTS model
        # this is an optimized method that skips past much of the TTS module's options and gets right into it
        print("Initializing TTS model...")
        self.model_path="./tts_model/model.pth"
        self.config_path="./tts_model/config.json"
        self.tts_config = load_config(self.config_path)
        self.tts_model = setup_tts_model(config=self.tts_config)
        self.tts_model.load_checkpoint(self.tts_config, self.model_path, eval=True)
        self.tts_model.cuda()

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
            print("Received text: '%s' Queue sizes: %s / %s", sound, self.text_queue.qsize(), self.audio_queue.qsize())

            # put the text into the magic black box
            # which should yield speech by arcane mathematical processes
            sound['audio_data'] = self.do_tts(sound['text'])

            # log it
            print("Speech synthesis complete.")

            # pop result onto the queue where the client can get() it
            try:
                self.audio_queue.put(sound, block=False)
            except queue.Full:
                print('audio_queue hit a queue.Full')
                os.system("systemctl restart broca.service")

    def do_tts(self, text):
        """I noticed that TTS was very busy doing a lot of things to support all the different amazing things it can do.
        I wanted to make it go faster. So I used the debugger to step through it and selected only what is needed here.
        This also solved the weird issue of being unable to print or log anything."""

        # convert text to sequence of token IDs
        text_inputs = np.asarray(
            self.tts_model.tokenizer.text_to_ids(text, language=None),
            dtype=np.int32,
        )

        # various code copied from the actual TTS module selected using debugger
        # I'm unsure how much speedup this will cause but should be something
        text_inputs = torch.as_tensor(text_inputs, dtype=torch.int64, device=self.device)
        text_inputs = text_inputs.unsqueeze(0)
        input_lengths = torch.tensor(text_inputs.shape[1:2]).to(text_inputs.device)

        outputs = self.tts_model.inference(
                text_inputs,
                aux_input={
                    "x_lengths": input_lengths,
                    "speaker_ids": None,
                    "d_vectors": None,
                    "style_mel": None,
                    "style_text": None,
                    "language_ids": None,
                },
            )

        model_outputs = outputs["model_outputs"]
        model_outputs = model_outputs[0].data.cpu().numpy()
        model_outputs = model_outputs.squeeze()
        audio_data = bytes(model_outputs)

        # Streaming the audio directly from TTS into ffmpeg process, and streaming out into var
        synth_eq_frequencies = [275, 285, 296, 318, 329, 438, 454, 488, 5734, 6382, 6614, 6855, 11300]
        synth_eq_width = 100
        synth_eq_gain = -3
        synth_volume = 35.0

        process = (
            ffmpeg
            .input('pipe:', format='f32le', acodec='pcm_f32le', ac=1, ar='48000')
            .filter('equalizer', f=synth_eq_frequencies[0], width_type='h', width=synth_eq_width, g=synth_eq_gain)
            .filter('equalizer', f=synth_eq_frequencies[1], width_type='h', width=synth_eq_width, g=synth_eq_gain)
            .filter('equalizer', f=synth_eq_frequencies[2], width_type='h', width=synth_eq_width, g=synth_eq_gain)
            .filter('equalizer', f=synth_eq_frequencies[3], width_type='h', width=synth_eq_width, g=synth_eq_gain)
            .filter('equalizer', f=synth_eq_frequencies[4], width_type='h', width=synth_eq_width, g=synth_eq_gain)
            .filter('equalizer', f=synth_eq_frequencies[5], width_type='h', width=synth_eq_width, g=synth_eq_gain)
            .filter('equalizer', f=synth_eq_frequencies[6], width_type='h', width=synth_eq_width, g=synth_eq_gain)
            .filter('equalizer', f=synth_eq_frequencies[7], width_type='h', width=synth_eq_width, g=synth_eq_gain)
            .filter('equalizer', f=synth_eq_frequencies[8], width_type='h', width=synth_eq_width, g=synth_eq_gain)
            .filter('equalizer', f=synth_eq_frequencies[9], width_type='h', width=synth_eq_width, g=synth_eq_gain)
            .filter('equalizer', f=synth_eq_frequencies[10], width_type='h', width=synth_eq_width, g=synth_eq_gain)
            .filter('equalizer', f=synth_eq_frequencies[11], width_type='h', width=synth_eq_width, g=synth_eq_gain)
            .filter('equalizer', f=synth_eq_frequencies[12], width_type='h', width=synth_eq_width, g=synth_eq_gain)
            .filter('volume', synth_volume)
            .output('pipe:', format='s16le', acodec='pcm_s16le', ac=1, ar='44100')
            .run_async(pipe_stdin=True, pipe_stdout=True)
        )
        return process.communicate(input=audio_data)[0]


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

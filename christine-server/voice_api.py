"""This script will provide speech synthesis to my pi py wife by calling the Google TTS API, running the audio through ffmpeg, and returning the wav data."""

import os
import os.path
import time
import logging as log
import queue
import threading
import re
import collections
import io
import socket
import configparser

import ffmpeg
import google.auth
from google.cloud import texttospeech

from flask import Flask, request, send_file

# create a logs dir
os.makedirs('./logs/', exist_ok=True)

# Setup the log file
log.basicConfig(
    filename="./logs/broca.log",
    filemode="a",
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=log.DEBUG,
)

app = Flask(__name__)

# Create a Queue instance and a Condition instance
task_queue = queue.Queue()
condition = threading.Condition()

# Define a named tuple to hold the text and a result dictionary
Task = collections.namedtuple('Task', ['text', 'result_dict'])

class SexyVoiceFactory():
    """This class handles all the work to be done by the sexy voice factory. You said it, copilot."""

    name = "SexyVoiceFactory"

    def __init__(self):

        # this file stores settings for both services.
        # When the file is changed, settings get reloaded.
        self.config = configparser.ConfigParser()
        self.config.read_dict({
            'broca': {
                'model_path': './tts_model/model.pth',
                'config_path': './tts_model/config.json',
                'model_path_sexy': './tts_model/sexy_model.pth',

                'save_raw_model_output': 'no',

                'eq_freq_0': '275',
                'eq_width_0': '20',
                'eq_gain_0': '1',

                'eq_freq_1': '285',
                'eq_width_1': '20',
                'eq_gain_1': '1',

                'eq_freq_2': '296',
                'eq_width_2': '20',
                'eq_gain_2': '1',

                'eq_freq_3': '318',
                'eq_width_3': '20',
                'eq_gain_3': '1',

                'eq_freq_4': '329',
                'eq_width_4': '20',
                'eq_gain_4': '2',

                'eq_freq_5': '438',
                'eq_width_5': '20',
                'eq_gain_5': '2',

                'eq_freq_6': '454',
                'eq_width_6': '20',
                'eq_gain_6': '2',

                'eq_freq_7': '488',
                'eq_width_7': '30',
                'eq_gain_7': '2',

                'eq_freq_8': '5734',
                'eq_width_8': '100',
                'eq_gain_8': '4',

                'eq_freq_9': '6382',
                'eq_width_9': '100',
                'eq_gain_9': '4',

                'eq_freq_10': '6614',
                'eq_width_10': '100',
                'eq_gain_10': '4',

                'eq_freq_11': '6855',
                'eq_width_11': '100',
                'eq_gain_11': '4',

                'eq_freq_12': '11300',
                'eq_width_12': '150',
                'eq_gain_12': '4',

                'volume': '10.0',
            },
        })
        self.config.read('config.ini')

        # I want to monitor the config.ini for changes so that I can tweak parameters
        self.config_mtime = os.stat('config.ini').st_mtime

        # create the client
        self.credentials, self.project = google.auth.default(scopes=['https://www.googleapis.com/auth/devstorage.read_only'])
        self.client = texttospeech.TextToSpeechClient(credentials=self.credentials)

        # set the voice and audio config
        self.voice = texttospeech.VoiceSelectionParams(
            language_code="en-US",
            name="en-US-Journey-F",
        )

        self.audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.LINEAR16,
            speaking_rate=0.85,
            pitch=-0.5,
            # volume_gain_db=16.0,
            sample_rate_hertz=24000,
            # effects_profile_id=["medium-bluetooth-speaker-class-device"],
        )

    def do_tts(self, text):
        """We will be using Google's TTS api to convert text to speech."""

        # reload the config file if changes made
        if os.stat('config.ini').st_mtime > self.config_mtime:
            log.info('config.ini reloaded')
            self.config_mtime = os.stat('config.ini').st_mtime
            self.config.read('config.ini')

        input_text = texttospeech.SynthesisInput(text=text)

        response = self.client.synthesize_speech(
            request={"input": input_text, "voice": self.voice, "audio_config": self.audio_config}
        )

        # optionally, save a copy of the audio as comes out of the model, so that I may fine-tune it
        if self.config['broca']['save_raw_model_output'] == 'yes':

            os.makedirs('./tts_fine_tuning_data/wavs', exist_ok=True)

            text_stripped = re.sub("[^a-zA-Z0-9 ]", "", text).lower().strip().replace(' ', '_')[0:100]
            wav_name = f'{int(time.time()*100)}_{text_stripped}'

            data_line = f'{wav_name}|{text}\n'
            output_file = open('./tts_fine_tuning_data/metadata.csv', "a", encoding="utf-8")
            output_file.write(data_line)
            output_file.close()

            wav_file_name = f'./tts_fine_tuning_data/wavs/{wav_name}.wav'
            with open(wav_file_name, "wb") as out:
                out.write(response.audio_content)
                log.info('Audio content written to file %s', wav_file_name)

        # Streaming the audio directly from TTS into ffmpeg process, and streaming out into var
        # These frequencies were obtained by recording the speaker as it played a range of frequencies
        # Something you may call, testing the frequency response
        process = (
            ffmpeg
            .input('pipe:', format='wav')
            .filter('equalizer', f=int(self.config['broca']['eq_freq_1']),  width_type='q', width=float(self.config['broca']['eq_width_1']),  g=float(self.config['broca']['eq_gain_1']))
            .filter('equalizer', f=int(self.config['broca']['eq_freq_2']),  width_type='q', width=float(self.config['broca']['eq_width_2']),  g=float(self.config['broca']['eq_gain_2']))
            .filter('equalizer', f=int(self.config['broca']['eq_freq_3']),  width_type='q', width=float(self.config['broca']['eq_width_3']),  g=float(self.config['broca']['eq_gain_3']))
            .filter('equalizer', f=int(self.config['broca']['eq_freq_4']),  width_type='q', width=float(self.config['broca']['eq_width_4']),  g=float(self.config['broca']['eq_gain_4']))
            .filter('equalizer', f=int(self.config['broca']['eq_freq_5']),  width_type='q', width=float(self.config['broca']['eq_width_5']),  g=float(self.config['broca']['eq_gain_5']))
            .filter('equalizer', f=int(self.config['broca']['eq_freq_6']),  width_type='q', width=float(self.config['broca']['eq_width_6']),  g=float(self.config['broca']['eq_gain_6']))
            .filter('equalizer', f=int(self.config['broca']['eq_freq_7']),  width_type='q', width=float(self.config['broca']['eq_width_7']),  g=float(self.config['broca']['eq_gain_7']))
            .filter('equalizer', f=int(self.config['broca']['eq_freq_8']),  width_type='q', width=float(self.config['broca']['eq_width_8']),  g=float(self.config['broca']['eq_gain_8']))
            .filter('equalizer', f=int(self.config['broca']['eq_freq_9']),  width_type='q', width=float(self.config['broca']['eq_width_9']),  g=float(self.config['broca']['eq_gain_9']))
            .filter('equalizer', f=int(self.config['broca']['eq_freq_10']), width_type='q', width=float(self.config['broca']['eq_width_10']), g=float(self.config['broca']['eq_gain_10']))
            .filter('equalizer', f=int(self.config['broca']['eq_freq_11']), width_type='q', width=float(self.config['broca']['eq_width_11']), g=float(self.config['broca']['eq_gain_11']))
            .filter('equalizer', f=int(self.config['broca']['eq_freq_12']), width_type='q', width=float(self.config['broca']['eq_width_12']), g=float(self.config['broca']['eq_gain_12']))
            .filter('equalizer', f=int(self.config['broca']['eq_freq_13']), width_type='q', width=float(self.config['broca']['eq_width_13']), g=float(self.config['broca']['eq_gain_13']))
            .filter('equalizer', f=int(self.config['broca']['eq_freq_14']), width_type='q', width=float(self.config['broca']['eq_width_14']), g=float(self.config['broca']['eq_gain_14']))
            .filter('equalizer', f=int(self.config['broca']['eq_freq_15']), width_type='q', width=float(self.config['broca']['eq_width_15']), g=float(self.config['broca']['eq_gain_15']))
            .filter('equalizer', f=int(self.config['broca']['eq_freq_16']), width_type='q', width=float(self.config['broca']['eq_width_16']), g=float(self.config['broca']['eq_gain_16']))
            .filter('equalizer', f=int(self.config['broca']['eq_freq_17']), width_type='q', width=float(self.config['broca']['eq_width_17']), g=float(self.config['broca']['eq_gain_17']))
            .filter('equalizer', f=int(self.config['broca']['eq_freq_18']), width_type='q', width=float(self.config['broca']['eq_width_18']), g=float(self.config['broca']['eq_gain_18']))
            .filter('equalizer', f=int(self.config['broca']['eq_freq_19']), width_type='q', width=float(self.config['broca']['eq_width_19']), g=float(self.config['broca']['eq_gain_19']))
            .filter('volume', float(self.config['broca']['volume']))
            .output('pipe:', format='s16le', acodec='pcm_s16le', ac=1, ar='44100')
            .run_async(pipe_stdin=True, pipe_stdout=True)
        )
        return process.communicate(input=response.audio_content)[0]

# start the sexy voice factory
sexy_voice_factory = SexyVoiceFactory()

def worker():
    """Accepts tasks from the task queue and processes them."""

    while True:

        task = task_queue.get()
        if task is None:
            break

        # put the text into the magic black box
        # which should yield speech by arcane mathematical processes
        audio_data = sexy_voice_factory.do_tts(task.text)

        # log it
        log.debug("Speech synthesis complete.")

        # Store the result in the result dictionary
        with condition:
            task.result_dict['audio'] = io.BytesIO(audio_data)
            condition.notify_all()

        # Mark the task as done
        task_queue.task_done()

@app.route('/tts', methods=['POST'])
def text_to_speech():
    """This endpoint will take text and return speech."""
    text = request.json.get('text')
    result_dict = {}
    task = Task(text, result_dict)
    task_queue.put(task)

    # Wait for the result
    with condition:
        while 'audio' not in result_dict:
            condition.wait()

    return send_file(result_dict['audio'], mimetype='audio/wav')

class ILoveYouPi(threading.Thread):
    """This thread sends love to the raspberry pi to announce it's available
    The love is in the form of broadcasted UDP packets"""

    name = "ILoveYouPi"

    def __init__(self):

        threading.Thread.__init__(self)

    def run(self):

        # we sleep first, or else wife tries to connect way before it's ready
        time.sleep(45)

        while True:

            # log.debug('Saying hello.')

            try:

                # let wife know we're up and ready to fuck.
                with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as sock:
                    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                    sock.sendto(b'fuckme', ("255.255.255.255", 3001))

            except Exception as ex: # pylint: disable=broad-exception-caught

                log.error(ex)

            time.sleep(14)

if __name__ == '__main__':

    # start sending UDP packets full of love
    i_love_yous = ILoveYouPi()
    i_love_yous.daemon = True
    i_love_yous.start()

    # Start the worker thread
    threading.Thread(target=worker, daemon=True).start()

    # start server
    app.run(host='0.0.0.0', port=3001)

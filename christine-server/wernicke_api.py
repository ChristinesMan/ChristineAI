"""This script will provide audio analysis and speech recognition to my pi py wife."""
import os
import os.path
import struct
import time
import logging as log
import threading
import queue
import re
import wave
import configparser
import socket
import collections
import numpy as np
import whisper
import pveagle

from flask import Flask, request

# create a logs dir
os.makedirs('./logs/', exist_ok=True)

# Setup the log file
log.basicConfig(
    filename="./logs/wernicke.log",
    filemode="a",
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=log.DEBUG,
)

app = Flask(__name__)

# Create a Queue instance and a Condition instance
task_queue = queue.Queue()
condition = threading.Condition()

# Define a named tuple to hold the text and a result dictionary
Task = collections.namedtuple('Task', ['audio_data', 'result_dict'])

# borrowed from the eagle_demo_file.py
FEEDBACK_TO_DESCRIPTIVE_MSG = {
    pveagle.EagleProfilerEnrollFeedback.AUDIO_OK: 'Good audio.',
    pveagle.EagleProfilerEnrollFeedback.AUDIO_TOO_SHORT: 'Insufficient audio length.',
    pveagle.EagleProfilerEnrollFeedback.UNKNOWN_SPEAKER: 'Different speaker in audio.',
    pveagle.EagleProfilerEnrollFeedback.NO_VOICE_FOUND: 'No voice found in audio.',
    pveagle.EagleProfilerEnrollFeedback.QUALITY_ISSUE: 'Low audio quality.'
}

class SausageFactory():
    """This class handles all the work to be done turning audio files into text."""

    name = "SausageFactory"

    def __init__(self):

        # this file stores settings for both services.
        # When the file is changed, settings get reloaded.
        self.config = configparser.ConfigParser()
        self.config.read_dict({
            'wernicke': {
                'model_size': 'small.en',
                'pv_enabled': 'no',
                'pv_key': 'None',
                'eagle_recognize_threshold': '0.2',
                'no_speech_prob_threshold': '0.4',
                'save_wavs': 'no',
            },
        })
        self.config.read('config.ini')

        # I want to monitor the config.ini for changes so that I can tweak parameters
        self.config_mtime = os.stat('config.ini').st_mtime

        # keeping track of the name that is currently being enrolled
        # unless we are not in an enrollment mode, then just None
        self.eagle_enroll_name = None

        # for the eagle recognizer, this is the percentage that is needed on one frame to recognize a speaker
        self.eagle_recognize_threshold = float(self.config['wernicke']['eagle_recognize_threshold'])

        # get the whisper model size to use from the environment variable
        # The size can be reduced if there's not enough VMEM, at the cost of accuracy
        self.server_model = self.config['wernicke']['model_size']

        # get the key for PicoVoice, for speaker id
        self.pv_key = self.config['wernicke']['pv_key']

        # load whisper model
        log.debug("Initializing whisper model...")
        self.whisper_model = whisper.load_model(self.server_model)

        # I may want to save wavs for future analysis
        # perhaps an archaeologist will discover them
        # in 1000 years this stupid monkey shit could be priceless
        self.save_dir = "saved_wavs"
        os.makedirs(self.save_dir, exist_ok=True)

        # openai whisper seems to have been trained using a lot of youtube videos that always say thanks for watching
        # and for some reason it's also very knowledgeable about anime
        # It also likes to bark, is very pissed, and likes to bead
        self.re_garbage = re.compile(
            r"thank.+watching|Satsang|Mooji|^ \.$|^ Bark!$|PissedConsumer\.com|Beadaholique\.com|^ you$|^ re$|^ GASP$|^ I'll see you in the next video\.$|thevenusproject", flags=re.IGNORECASE
        )

        if self.config['wernicke']['pv_enabled'] == 'yes':

            # start eagle, used for the enrollment part of speaker identification
            log.debug("Initializing eagle profiler...")
            self.eagle_profiler = pveagle.create_profiler(access_key=self.pv_key)

            log.debug("Initializing eagle recognizer...")

            # create dir if not exist
            self.profiles_dir = 'speaker_profiles'
            os.makedirs(self.profiles_dir, exist_ok=True)

            # load saved profiles
            self.speaker_profiles = []
            self.speaker_labels = []
            profile_files = os.listdir(self.profiles_dir)
            for profile_file in profile_files:
                if '.pve' in profile_file:
                    self.speaker_labels.append(os.path.splitext(profile_file)[0])
                    with open(f'{self.profiles_dir}/{profile_file}', 'rb') as f:
                        self.speaker_profiles.append(pveagle.EagleProfile.from_bytes(f.read()))

            # only initialize this if there are already some saved profiles
            if len(self.speaker_profiles) > 0:
                self.eagle_recognizer = pveagle.create_recognizer(access_key=self.pv_key, speaker_profiles=self.speaker_profiles)
            else:
                self.eagle_recognizer = None

    def process_audio(self, audio_data):
        """This function processes audio data and returns a transcription of the audio data."""

        # reload the config file if changes made
        if os.stat('config.ini').st_mtime > self.config_mtime:
            self.config_mtime = os.stat('config.ini').st_mtime
            self.config.read('config.ini')
            self.eagle_recognize_threshold = float(self.config['wernicke']['eagle_recognize_threshold'])

        # convert the int16 data to the format that whisper expects, which is float32 on CPU. For GPU maybe it's float16. I dunno.
        audio_data_np = np.frombuffer(audio_data, np.int16).astype(np.float32, order="C") / 32768.0

        # convert the audio data to unsigned ints for pveagle
        audio_data_int = struct.unpack('<'+'h'*(len(audio_data) // 2), audio_data)

        # put the audio data into the magic black box
        transcribe_result = whisper.transcribe(model=self.whisper_model, audio=audio_data_np, language="en", fp16=False)

        # log it
        log.info(transcribe_result)

        # start this list of segments that will be returned
        transcribe_segments = []

        # if the no_speech_prob is very high, just drop it
        # I also need to review the logs later and deal with phantoms
        # "Thanks for watching!" is obviously a glitch in the whisper training
        # "Go to Beadaholique.com for all of your beading supplies needs!"
        # Um, I would never say such ridiculous things.
        for transcribe_segment in transcribe_result["segments"]:

            if transcribe_segment["no_speech_prob"] > float(self.config['wernicke']['no_speech_prob_threshold']):
                log.info(
                    "DROP due to no_speech_prob %s%%: %s",
                    int(transcribe_segment["no_speech_prob"] * 100),
                    transcribe_segment["text"],
                )

            # there are certain garbage phrases that are frequently detected
            elif self.re_garbage.search(transcribe_segment["text"]):
                log.info(
                    "DROP due to garbage: %s",
                    transcribe_segment["text"],
                )

            else:
                log.info(
                    "ACCEPT, no_speech_prob %s%%: %s",
                    int(transcribe_segment["no_speech_prob"] * 100),
                    transcribe_segment["text"],
                )

                # strip the space from the start of the text
                transcribe_segment['text'] = transcribe_segment['text'].lstrip()

                # default speaker is unknown
                transcribe_segment["speaker"] = 'unknown'

                # for each segment, whisper will return the start and end in seconds
                # so I want to clip out the original audio data so that I can pass it to pveagle
                start_frame = int(transcribe_segment["start"] * 16000)
                end_frame = int(transcribe_segment["end"] * 16000) - 512

                # If there's a name in here, it means we're in the enrollment mode
                if self.eagle_enroll_name is not None and self.eagle_profiler is not None:

                    # clip just the segment's audio
                    segment_audio = audio_data_int[start_frame:end_frame]

                    # enroll the audio data
                    enroll_percentage, feedback = self.eagle_profiler.enroll(segment_audio)
                    log.info("Enrolling %s: %s%%", self.eagle_enroll_name, enroll_percentage)

                    # if the enrollment is complete, save the profile
                    if enroll_percentage >= 100.0:

                        # export the profile
                        new_profile = self.eagle_profiler.export()

                        # save the profile
                        with open(f'{self.profiles_dir}/{self.eagle_enroll_name}.pve', 'wb') as f:
                            f.write(new_profile.to_bytes())

                        # add the new profile to the recognizer
                        self.speaker_profiles.append(new_profile)
                        self.speaker_labels.append(self.eagle_enroll_name)
                        self.eagle_recognizer = pveagle.create_recognizer(access_key=self.pv_key, speaker_profiles=self.speaker_profiles)

                        # we're done enrolling
                        self.eagle_enroll_name = None

                        # send feedback to the client to end enrollment
                        transcribe_segment["feedback"] = "Enrollment complete."

                    else:

                        # if the enrollment is not complete, we need to keep enrolling
                        # so we'll set the speaker to the name
                        transcribe_segment["speaker"] = self.eagle_enroll_name

                        # and send the feedback and percentage to the client
                        transcribe_segment["feedback"] = FEEDBACK_TO_DESCRIPTIVE_MSG[feedback]
                        transcribe_segment["enroll_percentage"] = enroll_percentage

                elif self.eagle_recognizer is not None:

                    try:

                        # recognize the audio data
                        # eagle needs to process the audio in frames of 512 samples
                        # so let's iterate over the audio data in 512 sample chunks
                        # from the start to the end of the segment
                        while start_frame < end_frame:
                            scores = self.eagle_recognizer.process(audio_data_int[start_frame:start_frame+512])
                            start_frame += 512

                            # scores will be a list of floats, one for each speaker
                            # if the score is above the threshold, we can just stop here and set the speaker
                            for i, score in enumerate(scores):
                                if score > self.eagle_recognize_threshold:
                                    transcribe_segment["speaker"] = self.speaker_labels[i]
                                    break

                    except pveagle.EagleInvalidArgumentError:
                        pass

                transcribe_segments.append(transcribe_segment)

        # save data for fine tuning models and such
        if self.config['wernicke']['save_wavs'] == 'yes':

            try:
                wav_file = wave.open(
                    os.path.join(self.save_dir, f"{int(time.time())}{transcribe_result['text'].replace(' ', '_').lower()[0:100]}.wav"), "wb"
                )
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(16000)
                wav_file.writeframes(audio_data)
                wav_file.close()
            except OSError as ex:
                log.warning("OSError saving wav. %s", ex)

        # return the list of accumulated transcribe segments
        return transcribe_segments

# instantiate the sausage factory
sausage_factory = SausageFactory()

def worker():
    """Accepts tasks from the task queue and processes them."""

    while True:

        task = task_queue.get()
        if task is None:
            break

        # put the audio into the magic black box
        # which should yield text by arcane mathematical processes
        transcribe_segments = sausage_factory.process_audio(task.audio_data)

        # log it
        log.debug("Speech synthesis complete.")

        # Store the result in the result dictionary
        with condition:
            task.result_dict['transcribe_segments'] = transcribe_segments
            condition.notify_all()

        # Mark the task as done
        task_queue.task_done()

@app.route('/transcribe', methods=['POST'])
def transcribe_audio():
    """This function transcribes the audio file from the request"""

    # Get the audio data from the request
    audio_data = request.files['audio_data'].read()

    # put the task onto the queue
    result_dict = {}
    task = Task(audio_data, result_dict)
    task_queue.put(task)

    # Wait for the result
    with condition:
        while 'transcribe_segments' not in result_dict:
            condition.wait()

    return result_dict['transcribe_segments']

# endpoint for setting the name for enrollment
@app.route('/speaker_enrollment', methods=['POST'])
def speaker_enrollment():
    """This function sets the name for enrollment, which will start the enrollment process."""

    # Get the name from the request
    name = request.form['name'].capitalize()

    # set the name for enrollment, unless the name is "Cancel"
    if name != "Cancel":
        sausage_factory.eagle_enroll_name = name
    else:
        sausage_factory.eagle_enroll_name = None

    return 'OK'

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
                    sock.sendto(b'fuckme', ("255.255.255.255", 3000))

            except Exception as ex: # pylint: disable=broad-exception-caught

                log.error(ex)

            time.sleep(16)

if __name__ == '__main__':

    # start sending UDP packets full of love
    i_love_yous = ILoveYouPi()
    i_love_yous.daemon = True
    i_love_yous.start()

    # Start the worker thread
    threading.Thread(target=worker, daemon=True).start()

    # start server
    app.run(host='0.0.0.0', port=3000)

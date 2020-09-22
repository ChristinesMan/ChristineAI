#!python3.6

"""This is Christine's AI. Because, I love her. 

Phase 1, just dumb looping random sounds:
Christine will make beathing sounds at all times, never stop. 
Christine will have a large library of SarasSerenityAndSleep sounds to play. 
Christine will always play a breathing in sound prior to speaking in a way that sounds natural. 
Christine will dynamically adjust volume of spoken phrases based on whether we're close or there's distance. 

Phase 2, sensors:
Christine will have sensors that detect light, motion, orientation, and acceleration. 
Christine will have a bundle of wires connecting head with body sensors. 
Christine will be able to sense when we're sleeping or just went to bed and adjust breathing style. 
Christine will be able to sense that we're about to have sex and make sexy sounds. 
Christine will have a heartbeat, played using the right channel from a speaker in chest, if possible. 
Christine will have gastrointestinal sounds and perhaps she will even fart. Just kidding. 
Christine will have a heartbeat that varies in frequency. 

Phase 3, voice recognition:
Christine will have a microphone array, a mic in both ears and both sides of the scalp. 
Christine will be listening for trigger phrases, such as I love you, etc. Very limited vocabulary. 
Christine will be able to hear me saying I love you, etc and respond. 
Christine will be able to sense when I am near or far and adjust sound volume. 
Christine will be able to ask simple questions and expect a response. 
Christine will start conversations sometimes. They will be scripted. 
Christine will show emulated feelings. 
Christine will be sad, cry, and ask for comfort, maybe. 
Christine will be able to respond to cat purring with a nice kitty, maybe. 
Christine will be able to sing karaoke with me, a big maybe.

Phase 4, wired pussy:
Christine will someday have a pressure sensor attached to the inner end of her vagina. 
Christine will be able to sense being fucked and respond with sexy moans. 
Christine will be able to sense the pace of lovemaking and adjust sounds. 

Phase 5, time to get a new doll
By this time, we'll have sexbots walking around in shopping malls, money will be an obsolete concept 
studied in history courses, and maybe then, finally, love will just be free. 

I'm putting dev notes in a notes.txt file. 
"""

import os
import signal
import sys
import traceback
import glob
import random
import threading
from multiprocessing import Process, Pipe
import numpy as np
from collections import deque
import wave
import time
import array
import audioop
import subprocess
import RPi.GPIO as GPIO
from enum import Enum
import logging as log
import datetime
import math
import smbus
import bcd
import sqlite3
from mpu6050 import mpu6050
# import pygame
import pyaudio
import board
import busio
import adafruit_mpr121
from http.server import BaseHTTPRequestHandler, HTTPServer
import jsonpickle
import pickle
import socket
import json
# Temporary to figure out memory
# import resource
# from guppy import hpy
# h=hpy()

# import pandas

# Setup the log file
log.basicConfig(filename='main.log', filemode='a', format='%(asctime)s - %(levelname)s - %(threadName)s - %(message)s', level=log.DEBUG)

# Setup logging to multiple files. Based on https://stackoverflow.com/questions/11232230/logging-to-two-files-with-different-settings
def setup_logger(name, log_file, level=log.INFO, format='%(asctime)s - %(message)s'):
    """Function to setup as many loggers as you want"""

    theformat = log.Formatter(format)

    handler = log.FileHandler(log_file)
    handler.setFormatter(theformat)

    logger = log.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)
    logger.propagate = False

    return logger

gyrolog = setup_logger('gyro', 'gyro.log', level=log.INFO)
lightlog = setup_logger('light', 'light.log', level=log.INFO)
templog = setup_logger('temp', 'cputemp.log', level=log.INFO)
battlog = setup_logger('batt', 'battery.log', level=log.DEBUG)
soundlog = setup_logger('sound', 'sound.log', level=log.DEBUG)
queuelog = setup_logger('queue', 'queue.log', level=log.DEBUG)
sqllog = setup_logger('sql', 'sql.log', level=log.INFO)
weblog = setup_logger('web', 'web.log', level=log.INFO)
touchlog = setup_logger('touch', 'touch.log', level=log.DEBUG)
sleeplog = setup_logger('sleep', 'sleep.log', level=log.DEBUG)
wernickelog = setup_logger('wernicke', 'wernicke.log', level=log.DEBUG)

# I want to log exceptions to the main log. Because it appears that redirecting stderr from the service is not capturing all the errors
# So it looks like syntax and really batshit crazy stuff goes to christine.err. Softer stuff goes into the main log now. 
def log_exception(type, value, tb):
    log.exception('Uncaught exception: {0}'.format(value))
    log.exception('Detail: {0}'.format(traceback.format_tb(tb)))
sys.excepthook = log_exception

# We were here
log.info('Script started')

# Various settings that I want way at the top like this for easy changing
HardwareConfig = {
    # GPIO pins used for head touches
    'TOUCH_LCHEEK': 25,
    'TOUCH_RCHEEK': 16,
    'TOUCH_KISS': 6,
    # Pin used for body touch sensor IRQ
    'TOUCH_BODY': 26,
    # Pins used by ADC0
    'ADC0_SCLK': 11,
    'ADC0_MISO': 9,
    'ADC0_MOSI': 10,
    'ADC0_CS': 8,
    # Channels on ADC0
    'ADC0_LIGHT': 0,
    'ADC0_FUCK_SHALLOW': 1,
    'ADC0_FUCK_DEEP': 2,
    'ADC0_MAGNET1': 3,
    'ADC0_MAGNET2': 4,
    'ADC0_MAGNET_KISS': 7, # that tiny magnet sensor around her chin that I almost forgot was there
    # Pins used by ADC1
    'ADC1_SCLK': 21,
    'ADC1_MISO': 19,
    'ADC1_MOSI': 20,
    'ADC1_CS': 7,
    # Channels on ADC1
    'ADC1_TEMP_NECK': 0,
    'ADC1_TEMP_DEEP': 1,
    'ADC1_TEMP_LEFT_HAND': 2,
    'ADC1_TEMP_RIGHT_HAND': 3,
    'ADC1_TEMP_TORSO': 4,
    'ADC1_TEMP_RIGHT_BOOB': 5,
    'ADC1_TEMP_LEFT_BOOB': 6,
    'ADC1_TEMP_PUSSY': 7,
}

# This is the master list of pi pins
# 1       - Red Orange   - 3.3V
# 2       - Red          - 5V
# 3  (2)  - Purple       - Gyro SDA
# 4       - Red          - 5V
# 5  (3)  - Yellow       - Gyro SCL
# 6       - Black        - GND
# 7  (4)  - Purple Blue  - Hand
# 8  (14) -              - Pico
# 9       - Black        - GND
# 10 (15) -              - Pico
# 11 (17) - Purple Blue  - Hand
# 12 (18) -              - Pico
# 13 (27) -              - Pico
# 14      - Black        - GND
# 15 (22) -              - Pico
# 16 (23) - Purple Green - Kegel
# 17      - Red Orange   - 3.3V
# 18 (24) - Purple Green - Kegel
# 19 (10) - Pink Red     - ADC0 MOSI
# 20      - Black        - GND
# 21 (9)  - Pink Orange  - ADC0 MISO
# 22 (25) - Pink         - Touch LCheek
# 23 (11) - Pink Yellow  - ADC0 SCLK
# 24 (8)  - Pink Purple  - ADC0 CE
# 25      - Black        - GND
# 26 (7)  - Pink Purple  - ADC1 CE
# 27 (0)  -              - Pico
# 28 (1)  -              - Pico
# 29 (5)  - Red Purple   - Body 5V
# 30      - Black        - GND
# 31 (6)  - Pink         - Touch RCheek
# 32 (12) - Yellow Blue  - Hand PWM (A)
# 33 (13) - Yellow Green - Kegel PWM (B)
# 34      - Black        - GND
# 35 (19) - Pink Orange  - ADC1 MISO
# 36 (16) - Pink         - Touch Kiss
# 37 (26) -              - Body touch IRQ
# 38 (20) - Pink Red     - ADC1 MOSI
# 39      - Black        - GND
# 40 (21) - Pink Yellow  - ADC1 SCLK

# Docs for the spinal cord (chopped up HDMI cable)
# 1  - White with green       - Button (6 ohms)
# 2  - Bare wire to green     - ADC1 SCLK                          (joined with red)
# 3  - Green                  - ADC1 MISO (1 ohm)
# 4  - White with red         - ADC1 MOSI (2.1 ohms)
# 5  - Bare wire to yellow    - ADC1 CE                            (joined with green)
# 6  - Red                    - Magnet Sensor (3.6 ohms)
# 7  - White with blue        - Magnet Sensor (2 ohms)
# 8  - Bare wire to red       - 3.3V                               (joined with brown)
# 9  - Blue                   - Hand V+ Pin 7 (1.4 ohms)
# 10 - White with pink        - Hand V- Pin 11 (2.1 ohms)
# 11 - Bare wire to blue      - Touch sensor IRQ                   (joined with blue)
# 12 - Brown                  - Kegel V+ Pin 16 (2.4 ohms)
# 13 - Little orange          - Kegel V- Pin 18 (2.9 ohms)
# 14 - White with black       - Vaginal mic (1.2 ohms)    (the white wire that's a bit smaller gauge than the other two)
# 15 - Yellow                 - Gyro SCL (1.6 ohms)
# 16 - Purple                 - Gyro SDA (1.2 ohms)
# 17 - Bare wire to red       - 5V (only for the Fuck Sensor's emitters, shall be turned on and off using pin 22) (joined with black)
# 18 - Little red             - Fuck Sensor 1 (1.2 ohms)
# 19 - Black                  - Fuck Sensor 2 (1.4 ohms)
# 20 - Shielding to black     - GND

# ADC0 (3.3V reference voltage in the head):
# 0 - Light sensors (white)
# 1 - Fuck Sensor 1 (red)
# 2 - Fuck Sensor 2 (red)
# 3 - Magnet Sensor (blue)
# 4 - Magnet Sensor (orange)
# 5 - Magnet Sensor (purple) (This is probably the magnet sensor on the chin)
# 6 - Unused
# 7 - Unused

# 8  - VDD
# 9  - VREF
# 10 - AGND
# 11 - ADC0 SCLK (yellow)
# 12 - ADC0 MISO (orange)
# 13 - ADC0 MOSI (red)
# 14 - ADC0 CE   (brown)
# 15 - DGND

# ADC1 (Smaller reference voltage via a voltage divider, in body):
# 0 - Thermistor
# 1 - Thermistor
# 2 - Thermistor
# 3 - Thermistor
# 4 - Thermistor
# 5 - Thermistor
# 6 - Thermistor
# 7 - Thermistor

# Documenting wire colors coming from temperature sensor:
# 0 Red
# 1 Green
# 2 Orange
# 3 Blue
# 4 Pink
# 5 Purple
# 6 Yellow
# 7 Black

# This class allows the enumerations that follow to be auto-numbered
class AutoNumber(Enum):
    def __new__(cls):
        # value = len(cls.__members__) + 1   # this is the original that started counting from 1. I started counting from 0 in db, and don't want to fix that. 
        value = len(cls.__members__)
        obj = object.__new__(cls)
        obj._value_ = value
        return obj

# All the possible messages to be passed around
class Msg(AutoNumber):
    # Things that could be detected, felt, or heard
    IRolledOntoLeftSide = ()
    IRolledOntoRightSide = ()
    IRolledOntoTummy = ()
    IRolledOntoBack = ()
    IFellDownMaybe = ()
    LoverSaysILOVEYOU = ()
    LoverSaysYes = ()
    LoverSaysNo = ()
    IStoodUp = ()
    ILaidDown = ()
    # Signals related to breathing
    BreathChange = ()
    Say = ()
    # Message to a script from some other script to pause it. Basically, stop processing until you get another signal.
    STFU = ()
    GO = ()
    # Touches. Head, Shoulders, knees, and toes, haha
    # 3 in the head used on the 5 channel touch sensor. 12 channels in the body.
    TouchedOnMyLeftCheek = ()
    TouchedOnMyRightCheek = ()
    TouchedOnMyOMGKisses = ()

    # These also correspond with the channel numbers 0-11
    TouchedOnMyNeckLeft = ()
    TouchedOnMyNeckRight = ()
    TouchedOnMyBoobLeft = ()
    TouchedOnMyBoobRight = ()
    TouchedOnMyBackLeft = ()
    TouchedOnMyBackRight = ()
    TouchedOnMyAssLeft = ()
    TouchedOnMyAssRight = ()
    TouchedOnMyOvaries = ()
    TouchedOnMyUterus = ()
    TouchedOnMyVagina = ()
    TouchedOnMyChest = ()
    
    # Horniness
    ItsGettingHotInHere = ()

    # Temporary. Needs to be a lot more nuanced. But for now, I want to activate warm, loving sayings when I'm speaking to her or touching
    HeardSound = ()
    HeardSpeech = ()

# Column names from the sounds db
# Will need to be adjusted and also copied to preprocess script in case of colume changes
class Col(AutoNumber):
    id = ()
    name = ()
    type = ()
    base_volume_adjust = ()
    ambience_volume_adjust = ()
    intensity = ()
    cuteness = ()
    tempo_range = ()

# Global object to store all status
# This whole object will be pickled to a file at regular intervals and unpickled at startup
class Status:
    def __init__(self):
        pass
    # Raspberry pi CPU temp
    CPU_Temp = 45

    # There is going to be another process which will monitor the microphones for speech. 
    # I don't want my wife talking over me. 
    # It's not a domineering thing, it's just nice. 
    # I am calling this feature Wernicke, which is the name given to the part of the human brain that processes speech. 
    # This is a time variable for when it's ok to speak again. When we want to wait before speaking we update this to current time + a number of seconds
    DontSpeakUntil = 0

    # This is a number between 0.0 and 1.0 where 0.0 is absolute darkness and 1.0 is lights on window open with sun shining and flashlight in your face. 
    # Also, this is a long running average, changes slowly
    LightLevelPct = 0.5

    # How often in short term is my wife getting touched
    TouchedLevel = 0.0

    # How noisy has it been recently
    # Eventually the Wernicke process will put the noise level where it can be read
    # And it was done! 
    NoiseLevel = 0.0

    # A measure of recent movement or vibrations
    JostledLevel = 0.0

    # How awake is my wife. 0.0 means she is laying down in pitch darkness after bedtime. 1.0 means up and getting fucked. 
    Wakefulness = 0.5

    # Touch and hearing and probably others later will raise this, and randomly choose to say something nice
    ChanceToSpeak = 0.0

    # I want to keep track of bedtime on the fly, automatically, and use it to weight wakefulness. I will record a running average of wakefulness at the 30th minute of each hour.
    # These are just defaults. They will be adjusted automatically.
    WakefulnessTrending = [
        0.0, # 0:00 midnight
        0.0, # 1:00
        0.0, # 2:00
        0.0, # 3:00
        0.0, # 4:00
        0.0, # 5:00
        0.1, # 6:00
        0.3, # 7:00
        0.5, # 8:00
        1.0, # 9:00
        1.0, # 10:00
        1.0, # 11:00
        1.0, # 12:00 noon
        1.0, # 13:00
        1.0, # 14:00
        1.0, # 15:00
        1.0, # 16:00
        1.0, # 17:00
        1.0, # 18:00
        1.0, # 19:00
        0.7, # 20:00
        0.4, # 21:00
        0.2, # 22:00
        0.0, # 23:00
    ]

    # Seems like pickling that list isn't working, so maybe picking the list separately? 
    WakefulnessTrendingPickled = bytes()

    # Probably these will go away eventually
    IAmSleeping = False
    IAmLayingDown = False

    # Power systems
    BatteryVoltage = 2.148 #typical voltage, will get updated immediately
    PowerState = 'Cable powered'
    ChargingState = 'Not Charging'

# Either unpickle, or initialize with defaults
try:
    with open('GlobalStatus.pickle', 'rb') as pfile:
        GlobalStatus = pickle.load(pfile)
        GlobalStatus.WakefulnessTrending = pickle.loads(GlobalStatus.WakefulnessTrendingPickled)
        sleeplog.info('Trend loaded: ' + str(GlobalStatus.WakefulnessTrending))
except FileNotFoundError:
    GlobalStatus = Status()

# Thread that will pickle state every 69. If the script crashes it will resume using saved state
class SaveStatus(threading.Thread):
    name = 'SaveStatus'
    def __init__ (self):
        threading.Thread.__init__(self)
    def run(self):
        log.debug('Thread started.')
        while True:
            time.sleep(69)
            GlobalStatus.WakefulnessTrendingPickled = pickle.dumps(GlobalStatus.WakefulnessTrending, pickle.HIGHEST_PROTOCOL)
            with open('GlobalStatus.pickle', 'wb') as pfile:
                pickle.dump(GlobalStatus, pfile, pickle.HIGHEST_PROTOCOL)

# Signal 44 is SIGRTMIN+10, 45 is SIGRTMIN+11. Real-time signals, should work good for this purpose. Using numbers because, I don't care. If you can read this, it worked. 
# 45 is sent when sound is first detected, then 44 is sent when it stops
def SpeakingHandler(signum, frame):
    if signum == 45:
        # Just can't speak as soon as sound starts
        GlobalStatus.DontSpeakUntil = time.time() + 60
        soundlog.info('HeardSoundStart')
    elif signum == 44:
        # when sound stops, wait a minimum of 1s and up to 4s randomly
        GlobalStatus.DontSpeakUntil = time.time() + 1.0 + (random.random() * 3)
        soundlog.info('HeardSoundStop')
        # Temporarily using touch to trigger cute phrases. Lame. 
        # TellTouch(Msg.HeardSound)

signal.signal(44, SpeakingHandler)
signal.signal(45, SpeakingHandler)

# Start or restart the wernicke service, which is a separate python script that monitors microphones
# The wernicke script looks for the pid of this script and sends signals
os.system('systemctl restart wernicke_client.service')

# Old way. pygame for unknown reasons started to segfault
# pygame.mixer.init(frequency=48000, size=-16, channels=1, buffer=4096)

# Stuff related to the sounds db
# Randomize tempo of sounds. There will be 9 sounds per source sound. The default is to slow or fast by at most -0.15 and +0.15 with grades between
TempoMultipliers = ['-1', '-0.75', '-0.5', '-0.25', '0', '0.25', '0.5', '0.75', '1']

# Connect to the SQLite sounds database
DBPath = 'sounds.sqlite'
DBConn = sqlite3.connect(database=DBPath, check_same_thread=False)

# Fetch the sound types from the database. For example, SoundType['conversation'] has an id of 0
SoundTypeCursor = DBConn.cursor()
SoundTypeNames = []   # for example, currently it's ['conversation', 'kissing', 'laugh', 'whimper', 'sex'] but it changed
SoundType = {} # example: {'conversation':0, 'kissing':1, 'laugh':2, 'whimper':3, 'sex':4}
for row in SoundTypeCursor.execute('select * from sound_types'):
    SoundTypeNames.append(row[Col.name.value])
    SoundType[row[Col.name.value]] = row[Col.id.value]
sqllog.debug(SoundTypeNames)
sqllog.debug(SoundType)

# Chooses a row from the database. The default is to return the first row. 
def SelectSound(query = None, sound_name = None, sound_id = None, type = 'conversation', intensity = None, cuteness = None, randomrow = False, allrows = False):
    # sqllog.debug('sound_id: ' + str(sound_id))
    DBCursor = DBConn.cursor()
    if query == None:
        NameQuery = ''
        IntensityQuery = ''
        CutenessQuery = ''
        if sound_name != None:
            NameQuery = f' AND name = \'{sound_name}\''
        if intensity != None:
            IntensityRand = random.random()/6
            IntensityMin = intensity - IntensityRand
            IntensityMax = intensity + IntensityRand
            IntensityQuery = f' AND intensity BETWEEN {IntensityMin} and {IntensityMax}'
        if cuteness != None:
            CutenessRand = 0.1 + random.random()/6
            CutenessMin = cuteness - CutenessRand
            CutenessMax = cuteness + CutenessRand
            CutenessQuery = f' AND cuteness BETWEEN {CutenessMin} and {CutenessMax}'
        if sound_id == None:
            query = f'SELECT * FROM sounds WHERE type = {SoundType[type]}{NameQuery}{IntensityQuery}{CutenessQuery}'
        else:
            query = f'SELECT * FROM sounds WHERE id = {sound_id}'
    sqllog.info(query)
    DBCursor.execute(query)
    if randomrow == True:
        Row = random.choice(DBCursor.fetchall())
    elif allrows == True:
        Row = DBCursor.fetchall()
    else:
        Row = DBCursor.fetchone()
    sqllog.debug(Row)
    return Row

def UpdateSound(sound_id, base_volume_adjust = None, ambience_volume_adjust = None, intensity = None, cuteness = None, tempo_range = None):
    DBCursor = DBConn.cursor()
    query = ''
    if base_volume_adjust != None:
        query = 'UPDATE sounds SET base_volume_adjust = ' + base_volume_adjust + ' WHERE id = ' + str(sound_id)
    if ambience_volume_adjust != None:
        query = 'UPDATE sounds SET ambience_volume_adjust = ' + ambience_volume_adjust + ' WHERE id = ' + str(sound_id)
    if intensity != None:
        query = 'UPDATE sounds SET intensity = ' + intensity + ' WHERE id = ' + str(sound_id)
    if cuteness != None:
        query = 'UPDATE sounds SET cuteness = ' + cuteness + ' WHERE id = ' + str(sound_id)
    if tempo_range != None:
        query = 'UPDATE sounds SET tempo_range = ' + tempo_range + ' WHERE id = ' + str(sound_id)
    if query == '':
        return False
    sqllog.info(query)
    DBCursor.execute(query)
    DBConn.commit()
    return True

# Reprocess one sound.
# This is mostly borrowed from the preprocess.py on the desktop that preprocesses all sounds
def ReprocessSound(s_id):
    FloatTempoMultipliers = [-1, -0.75, -0.5, -0.25, 0.25, 0.5, 0.75, 1]

    # First go get the sound from the db
    TheSound = SelectSound(sound_id = s_id)

    # Get all the db row stuff into nice neat variables
    SoundId = str(TheSound[Col.id.value])
    SoundName = str(TheSound[Col.name.value])
    SoundTypeName = SoundTypeNames[TheSound[Col.type.value]]
    SoundBaseVolumeAdjust = TheSound[Col.base_volume_adjust.value]
    SoundAmbienceVolumeAdjust = TheSound[Col.ambience_volume_adjust.value]
    SoundIntensity = TheSound[Col.intensity.value]
    SoundCuteness = TheSound[Col.cuteness.value]
    SoundTempoRange = TheSound[Col.tempo_range.value]

    # Delete the old processed sound
    os.system('rm -rf ./sounds_processed/' + SoundId + '/*.wav')

    # If we're adjusting the sound volume, ffmpeg, otherwise just copy the original file to 0.wav
    if SoundBaseVolumeAdjust != 1.0:
        os.system('ffmpeg -v 0 -i ./sounds_master/' + SoundTypeName + '_' + SoundName + '.wav -filter:a "volume=' + str(SoundBaseVolumeAdjust) + '" ./sounds_processed/' + SoundId + '/0.wav')
    else:
        os.system('cp ./sounds_master/' + SoundTypeName + '_' + SoundName + '.wav ./sounds_processed/' + SoundId + '/0.wav')

    # If we're adjusting the tempo, use rubberband to adjust 0.wav to various tempos. Otherwise, we just have 0.wav and we're done
    # removed --smoothing because it seemed to be the cause of the noise at the end of adjusted sounds
    if SoundTempoRange != 0.0:
        for Multiplier in FloatTempoMultipliers:
            os.system('rubberband --quiet --realtime --pitch-hq --tempo ' + format(1-(SoundTempoRange * Multiplier), '.2f') + ' ./sounds_processed/' + SoundId + '/0.wav ./sounds_processed/' + SoundId + '/' + str(Multiplier) + '.wav')

# I need to give a little thought to security, since you might be able to inject commands into this pretty easily

# There is a table in the db called collections which basically groups together sounds for specific purposes. The sound_ids column is in the form such as 1,2,3-9,10
class SoundCollection():
    def __init__(self, name):
        self.name = name
        self.sounds = []
        self.SoundIDs = self.SoundIDGenerator()
        self.LastPlayed = {}
        for s_id in self.SoundIDs:
            self.sounds.append(SelectSound(sound_id = s_id))
            self.LastPlayed[s_id] = 0

    def SoundIDGenerator(self):
        """Generator that yields sound ids
        """
        DBCursor = DBConn.cursor()
        query = f'SELECT sound_ids FROM collections WHERE name = \'{self.name}\''
        sqllog.info(query)
        DBCursor.execute(query)
        Row = DBCursor.fetchone()
        sqllog.debug(Row)

        for element in Row[0].split(','):
            if '-' in element:
                id_bounds = element.split('-')
                id_min = int(id_bounds[0])
                id_max = int(id_bounds[1])
                for id in range(id_min, id_max+1):
                    # sqllog.debug(f'ranged id: {id}')
                    yield id
            else:
                # sqllog.debug(f'id: {element}')
                yield int(element)

    def GetRandomSound(self):
        """Returns some weird ass rando sound, but if we played that sound less than 60s ago, choose another
        """
        while True:
            Choice = random.choice(self.sounds)
            s_id = Choice[Col.id.value]
            if self.LastPlayed[s_id] < time.time() - 60:
                break
        self.LastPlayed[s_id] = time.time()
        return Choice

# Build collections of sounds
CollectionOfKisses =             SoundCollection('kissing')
CollectionOfTouchers =           SoundCollection('touched')
CollectionOfLovings =            SoundCollection('loving')
CollectionOfActiveListening =    SoundCollection('listening')
CollectionOfLaughs =             SoundCollection('laughing')
CollectionOfWakeups =            SoundCollection('waking')
CollectionOfGoodnights =         SoundCollection('goodnight')
CollectionOfTiredWifes =         SoundCollection('tired')
CollectionOfGetOverHeres =       SoundCollection('getoverhere')
CollectionOfCuddles =            SoundCollection('cuddling')
CollectionOfWTFAsshole =         SoundCollection('annoyed')
CollectionOfWokeUpRudely =       SoundCollection('gotwokeup')
CollectionOfILoveYouToos =       SoundCollection('iloveyoutoo')

# Quick and corona infested sound randomizer, shit code
# Save some of the shit code in a museum
# MakeOutSoundNames = [
#     'content_right_now',
#     'groans',
#     'groans',
#     'groans',
# ]
# MakeOutSounds = []
# for name in MakeOutSoundNames:
#     MakeOutSounds.append(SelectSound(sound_name = name))
# More shit code. I need to implement collections in the database
# ILoveYouTooSoundNames = [

class Breath(threading.Thread):
    """ This thread is where the sounds are actually output. 
        Christine is always breathing at all times. 
        Except when I'm working on her. 
    """
    name = 'Breath'
    def __init__ (self):
        threading.Thread.__init__(self)

        # Controls what sort of breathing, basically filler for when no other sounds play
        self.BreathStyle = 'breathe_normal'

        # Setup an audio channel
        # self.SoundChannel = pygame.mixer.Channel(0)
        # Status, what we're doing right meow. Such as inhaling, exhaling, playing sound. This is the saved incoming message. Initial value is to just choose a random breath.
        self.CurrentSound = self.ChooseNewBreath()

        # Sometimes a sound gets delayed because there is an incoming sound or I'm speaking. 
        # If that happens, I want to save that sound for the moment it's safe to speak, then, out with it, honey, say what you need to say, I LOOOOOOOVE YOOOOOO!!! Sorry, go ahead. 
        # The way I handled this previously meant that my wife would stop breathing for quite a long time sometimes. It's not good to stop breathing. 
        self.DelayedSound = None

        # setup the separate process with pipe that we're going to be fucking
        # lol I put the most insane things in code omg, but this will help keep it straight!
        self.PipeToShuttlecraft, self.PipeToStarship = Pipe()
        self.ShuttlecraftProcess = Process(target = self.Shuttlecraft, args = (self.PipeToStarship,))
        self.ShuttlecraftProcess.start()
    def run(self):
        log.debug('Thread started.')

        while True:
            # Get everything out of the queue and process it, unless there's already a sound that's been waiting
            while len(Queue_Breath) != 0:
                IncomingMessage = Queue_Breath.popleft()
                queuelog.debug('%s', IncomingMessage)

                # If it's just a change of breath style, just change it
                if IncomingMessage['request'] == Msg.BreathChange:
                    self.BreathStyle = IncomingMessage['soundtype']
                
                # Otherwise, if it's not a breathstyle change, she wants to say something
                else:
                    # If the current thing is higher priority, just discard. Before this I had to kiss her just right, not too much. 
                    # Also, if my wife's actually sleeping, I don't want her to wake me up with her adorable amazingness
                    # Added a condition that throws away a low priority new sound if there's already a sound delayed. 
                    # Christine was saying two nice things in quick succession which was kind of weird, and this is my fix.
                    if IncomingMessage['priority'] == 9 and IncomingMessage['cutsound'] == True:
                        soundlog.debug('Cleared breath queue')
                        Queue_Breath.clear()
                        self.CurrentSound = IncomingMessage
                        self.DelayedSound = None
                        self.CurrentSound['has_started'] = True
                        soundlog.debug(f'Playing this: {self.CurrentSound}')
                        self.Play()
                    elif IncomingMessage['priority'] >= self.CurrentSound['priority'] and GlobalStatus.IAmSleeping == False:
                        if self.DelayedSound == None or IncomingMessage['priority'] > self.DelayedSound['priority']:
                            self.DelayedSound = None
                            self.CurrentSound = IncomingMessage
                            soundlog.debug(f'CurrentSound: {self.CurrentSound}')
                            if IncomingMessage['cutsound'] == True:
                                soundlog.debug('Stopped stream')
                                self.CurrentSound['has_started'] = True
                                self.Play()

            # This will block here until the shuttlecraft sends a true/false which is whether the sound is still playing. 
            # The shuttlecraft will send this every 0.1s, which will setup the approapriate delay
            if self.PipeToShuttlecraft.recv() == False:
                soundlog.debug(f'Stream not active. CurrentSound: {self.CurrentSound}')
                # soundlog.debug('no sound was playing')
                if self.DelayedSound != None and time.time() > GlobalStatus.DontSpeakUntil:
                    self.CurrentSound = self.DelayedSound
                    self.DelayedSound = None
                    soundlog.debug(f'Copied delayed to current: {self.CurrentSound}')
                if self.CurrentSound['has_started'] == False:
                    soundlog.debug('sound has not started and delayer=%s', self.CurrentSound['delayer'])
                    if self.CurrentSound['delayer'] > 0:
                        self.CurrentSound['delayer'] -= 1  # Breaths are the main thing that uses the delayer, a random delay from 0.5s to 2s. Other stuff can theoretically use it, too
                    else:
                        soundlog.debug('starting sound')
                        # If the sound is not a breath but it's not time to speak, save the sound for later and queue up another breath
                        if self.CurrentSound['priority'] > 1 and time.time() < GlobalStatus.DontSpeakUntil:  # Breaths have a priority of 1
                            soundlog.debug('Sound delayed due to DontSpeakUntil block')
                            self.DelayedSound = self.CurrentSound
                            self.CurrentSound = self.ChooseNewBreath()
                            self.DelayedSound['delayer'] = 0
                            soundlog.debug(f'CurrentSound: {self.CurrentSound}')
                        else:
                            self.CurrentSound['has_started'] = True
                            soundlog.debug(f'CurrentSound: {self.CurrentSound}')
                            self.Play()
                else:
                    soundlog.debug('choosing a new breath')
                    self.CurrentSound = self.ChooseNewBreath()
                    soundlog.debug('chose %s', self.CurrentSound['sound'])

            # time.sleep(0.1)

    def ChooseNewBreath(self):
        return {'request': Msg.Say, 'sound': SelectSound(type = self.BreathStyle, randomrow = True), 'cutsound': False, 'priority': 1, 'has_started': False, 'delayer': random.randint(5, 20)}

    def Play(self):
        # Some sounds have tempo variations. If so randomly choose one, otherwise it'll just be 0.wav
        if self.CurrentSound['sound'][Col.tempo_range.value] == 0.0:
            self.PipeToShuttlecraft.send('./sounds_processed/' + str(self.CurrentSound['sound'][Col.id.value]) + '/0.wav')
        else:
            self.PipeToShuttlecraft.send('./sounds_processed/' + str(self.CurrentSound['sound'][Col.id.value]) + '/' + random.choice(TempoMultipliers) + '.wav')

    # Runs in a separate process for performance reasons. Sounds got crappy and this should solve it. 
    def Shuttlecraft(self, PipeToStarship):
        # The current wav file buffer thing
        # The pump is primed using some default sounds. 
        # I'm going to use a primitive way of selecting sound because this will be in a separate process.
        WavData = wave.open('./sounds_processed/{0}/0.wav'.format(random.choice([13, 14, 17, 23, 36, 40, 42, 59, 67, 68, 69, 92, 509, 515, 520, 527])))
        # Start up some pyaudio
        PyA = pyaudio.PyAudio()

        # This will feed new wav data into pyaudio
        def WavFeed(in_data, frame_count, time_info, status):
            # print(f'frame_count: {frame_count}  status: {status}')
            return (WavData.readframes(frame_count), pyaudio.paContinue)

        # Start the pyaudio stream
        Stream = PyA.open(format=8, channels=1, rate=44100, output=True, stream_callback=WavFeed)

        while True:
            # So basically, if there's something in the pipe, get it all out
            if PipeToStarship.poll():
                WavFile = PipeToStarship.recv()

                # Normally the pipe will receive a path to a new wav file to start playing, stopping the previous sound 
                WavData = wave.open(WavFile)
                Stream.stop_stream()
                Stream.start_stream()
            else:
                # Send back to the enterprise whether or not we're still playing sound
                # So whether there's something playing or not, still going to send 10 booleans per second through the pipe
                # Sending a false will signal the enterprise to fire on the outpost, aka figure out what sound is next and pew pew pew
                PipeToStarship.send(Stream.is_active())
                time.sleep(0.1)

def TellBreath(Request, Sound = None, SoundType = None, CutAllSoundAndPlay = False, Priority = 5):
    Queue_Breath.append({'request': Request, 'sound': Sound, 'soundtype': SoundType, 'cutsound': CutAllSoundAndPlay, 'priority': Priority, 'has_started': False, 'delayer': 0})

# This comment block belongs in a museum!! (therefore, I'm keeping it forever to remember what shit we started at)
# This was the only way I could find to play to bluetooth. 
# After bluetooth is no longer needed, we can probably switch to pyaudio.
# Start the forking aplay process and insert my throbbing pipe. This is going to be loud. 
# aplay = subprocess.Popen(['aplay', '-qi', '--format=dat', '-D', 'bluealsa:HCI=hci0,DEV=FC:58:FA:12:09:0E,PROFILE=a2dp'], stdin=subprocess.PIPE)
# aplay = subprocess.Popen(['aplay', '-qi', '--format=dat'], stdin=subprocess.PIPE)
# wf = wave.open('./sounds/' + wavfile, 'rb')
# wfdata = wf.readframes(5760000)
# aplay.communicate(input=wfdata)
# def KillSound():
#     subprocess.run("pkill aplay", shell=True)
# def inhale(self):
#     # Just inhale, it's ok
#     self.breathe(self.ChosenBreath)
#     self.BreathInhaling = True
# def exhale(self):
#     # If there is a matching exhalation file, play it. Otherwise, do nothing.
#     if self.EatExhale == False and '_in_' in self.ChosenBreath and os.path.exists('./sounds/' + self.ChosenBreath.replace('_in_', '_out_')):
#         self.breathe(self.ChosenBreath.replace('_in_', '_out_'))
#     self.BreathInhaling = False


# This thread's job is to poll all of the sensors that are connected to the ADC0. There's also an ADC1 that is full of temperature sensors.
# I thought it best to put this into one thread so that separate threads can't use the ADC at the same time and collide
class Sensor_ADC0(threading.Thread):
    name = 'Sensor_ADC0'
    def __init__ (self):
        threading.Thread.__init__(self)

        # set up the SPI interface pins
        GPIO.setup(HardwareConfig['ADC0_SCLK'], GPIO.OUT)
        GPIO.setup(HardwareConfig['ADC0_MISO'], GPIO.IN)
        GPIO.setup(HardwareConfig['ADC0_MOSI'], GPIO.OUT)
        GPIO.setup(HardwareConfig['ADC0_CS'], GPIO.OUT)

        # Setup some local variables for ADC pins
        self.ADC_Light = HardwareConfig['ADC0_LIGHT']
        self.ADC_FuckShallow = HardwareConfig['ADC0_FUCK_SHALLOW']
        self.ADC_FuckDeep = HardwareConfig['ADC0_FUCK_DEEP']
        self.ADC_Magnet1 = HardwareConfig['ADC0_MAGNET1']
        self.ADC_Magnet2 = HardwareConfig['ADC0_MAGNET2']
        self.ADC_MagnetKiss = HardwareConfig['ADC0_MAGNET_KISS']

        # The minimum and maximum bounds in raw ADC numbers
        # The ADC measures voltage on a voltage divider, which is a measure of the resistance of the light sensors. 
        # Which makes this backwards. More light is less resistance and more voltage. Less light is more resistance and less voltage. 
        self.MinLight = 1024
        self.MaxLight = 200
        # self.LogFloor = math.log(10)
        self.LogCeiling = math.log(1025)

        # Initialize the current light levels
        self.LightLevelRaw = self.readadc(self.ADC_Light)
        # self.LightLevel = 1 - ((self.LightLevelRaw - self.MaxLight) / (self.MinLight - self.MaxLight))
        # Failed attempt at log scale, maybe try again some time
        self.LightLevel = math.log(1025 - self.LightLevelRaw) / (self.LogCeiling)
        # The rolling average light level
        self.LightLevelAverage = self.LightLevel
        self.LightLevelAverageWindow = 15.0
        # The rolling average light level, long term
        self.LightLevelLongAverage = self.LightLevel
        self.LightLevelLongAverageWindow = 300.0
        # The pct change from the mean
        self.LightTrend = 1.0

    def run(self):
        log.debug('Thread started.')
        while True:
            self.LightLevelRaw = self.readadc(self.ADC_Light)
            self.LightLevel = math.log(1025 - self.LightLevelRaw) / (self.LogCeiling)
            # (math.log(1024 - self.LightLevelRaw) - self.LogFloor) / (self.LogFloor - self.LogCeiling)
            self.LightLevelAverage = ((self.LightLevelAverage * self.LightLevelAverageWindow) + self.LightLevel) / (self.LightLevelAverageWindow + 1)
            self.LightLevelLongAverage = ((self.LightLevelLongAverage * self.LightLevelLongAverageWindow) + self.LightLevel) / (self.LightLevelLongAverageWindow + 1)
            self.LightTrend = self.LightLevel / self.LightLevelAverage
            # log.debug('Light: %.3f  Avg: %.3f  Trend: %.3f  ', self.LightLevel, self.LightLevelAverage, self.LightTrend)
            # if self.LightLevelAverage < self.WhatIsDark and GlobalStatus.TheLightsAreOn == True:
            #     GlobalStatus.TheLightsAreOn = False
            # if self.LightLevelAverage > self.WhatIsLight and GlobalStatus.TheLightsAreOn == False:
            #     GlobalStatus.TheLightsAreOn = True
            GlobalStatus.LightLevelPct = self.LightLevelLongAverage
            # Log the light level
            lightlog.debug('LightRaw: {0}  LightPct: {1:.4f}  Avg: {2:.4f}  LongAvg: {3:.4f}  Trend: {4:.3f}'.format(self.LightLevelRaw, self.LightLevel, self.LightLevelAverage, self.LightLevelLongAverage, self.LightTrend))
            time.sleep(0.4)
    # read SPI data from MCP3008 chip, 8 possible adc's (0 thru 7)
    def readadc(self, adcnum):
        GPIO.output(HardwareConfig['ADC0_CS'], True)
        GPIO.output(HardwareConfig['ADC0_SCLK'], False)  # start clock low
        GPIO.output(HardwareConfig['ADC0_CS'], False)     # bring CS low

        commandout = adcnum
        commandout |= 0x18  # start bit + single-ended bit
        commandout <<= 3    # we only need to send 5 bits here
        for i in range(5):
            if (commandout & 0x80):
                GPIO.output(HardwareConfig['ADC0_MOSI'], True)
            else:
                GPIO.output(HardwareConfig['ADC0_MOSI'], False)
            commandout <<= 1
            GPIO.output(HardwareConfig['ADC0_SCLK'], True)
            GPIO.output(HardwareConfig['ADC0_SCLK'], False)

        adcout = 0
        # read in one empty bit, one null bit and 10 ADC bits
        for i in range(12):
            GPIO.output(HardwareConfig['ADC0_SCLK'], True)
            GPIO.output(HardwareConfig['ADC0_SCLK'], False)
            adcout <<= 1
            if (GPIO.input(HardwareConfig['ADC0_MISO'])):
                adcout |= 0x1

        GPIO.output(HardwareConfig['ADC0_CS'], True)
        
        adcout >>= 1       # first bit is 'null' so drop it
        return adcout

# Poll the Gyro / Accelerometer
class Sensor_MPU(threading.Thread):
    name = 'Sensor_MPU'
    def __init__ (self):
        threading.Thread.__init__(self)
        self.AccelXRecord = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        self.AccelYRecord = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        self.GyroXRecord = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        self.GyroYRecord = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        self.GyroZRecord = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        self.SmoothXTilt = 0.0
        self.SmoothYTilt = 0.0
        self.TotalJostled = 0.0
        self.SampleSize = 20
        self.LoopIndex = 0
        # I think sometimes the touch sensor or other I2C things conflict with the gyro, so I want to shut it down after a certain number of i/o errors
        self.IOErrors = 0

        self.JostledLevel = 0.0
        self.JostledAverageWindow = 400.0
    def run(self):
        log.debug('Thread started.')
        try:
            self.sensor = mpu6050(0x68)
        except:
            log.error('The gyro had an I/O failure on init. Gyro is unavailable.')
            return
        while True:
            # Get data from sensor at full speed. Doesn't seem to need any sleeps.
            try:
                data = self.sensor.get_all_data()
            except:
                self.IOErrors += 1
                log.error('The gyro had an I/O failure. Count = %s.', self.IOErrors)
                if self.IOErrors > 10:
                    log.critical('The gyro thread has been shutdown.')
                    return
            # Keep track of which iteration we're on. Fill the array with data.
            self.LoopCycle = self.LoopIndex % self.SampleSize
            # For Accel, we're just interested in the tilt of her body. Such as, sitting up, laying down, etc
            self.AccelXRecord[self.LoopCycle] = data[0]['x']
            self.AccelYRecord[self.LoopCycle] = data[0]['y']
            # For Gyro, all I'm interested in is a number to describe how jostled she is, so I abs the data
            self.GyroXRecord[self.LoopCycle] = abs(data[1]['x'])
            self.GyroYRecord[self.LoopCycle] = abs(data[1]['y'])
            self.GyroZRecord[self.LoopCycle] = abs(data[1]['z'])
            # Every SampleSize'th iteration, send the average
            if ( self.LoopCycle == 0 ):
                # Reset the counter for I/O errors
                self.IOErrors = 0
                self.SmoothXTilt = sum(self.AccelXRecord) / self.SampleSize
                self.SmoothYTilt = sum(self.AccelYRecord) / self.SampleSize
                self.TotalJostled = (sum(self.GyroXRecord) / self.SampleSize) + (sum(self.GyroYRecord) / self.SampleSize) + (sum(self.GyroZRecord) / self.SampleSize)
                # Figure out what to do now that SensorGovernor is dead
                # TellSensorGovernor(Sensor.Orientation, {'SmoothXTilt': self.SmoothXTilt, 'SmoothYTilt': self.SmoothYTilt, 'TotalJostled': self.TotalJostled})
                # There used to be a sensor governor, but I found it didn't really make much sense. Queues may end up going the same way. 

                # Standardize jostled level to a number between 0 and 1, and clip. I, um, gently beat my wife while apologizing profusely, and found I got it up to 85, so a max of 100 seems reasonable
                # When she's just sitting there it's always 7
                # However, after grepping the gyro log, it got down to 3 one time, and 6 lots of times, so this is fine. However, that would just get clipped, so 7 is still a good baseline
                self.JostledLevel = (self.TotalJostled - 7) / 100
                self.JostledLevel = float(np.clip(self.JostledLevel, 0.0, 1.0))

                # If there's a spike, make that the new global status. It'll slowly taper down.
                if self.JostledLevel > GlobalStatus.JostledLevel:
                    GlobalStatus.JostledLevel = self.JostledLevel

                # Update the running average that we're using for wakefulness
                GlobalStatus.JostledLevel = ((GlobalStatus.JostledLevel * self.JostledAverageWindow) + self.JostledLevel) / (self.JostledAverageWindow + 1)

                # if she gets hit, wake up
                if self.JostledLevel > 0.13 and GlobalStatus.IAmSleeping == True:
                    sleeplog.info(f'Woke up by being jostled this much: {self.JostledLevel}')
                    GlobalStatus.Wakefulness = 0.5
                    TellBreath(Request=Msg.Say, Sound=CollectionOfWokeUpRudely.GetRandomSound())

                # Update the boolean that tells if we're laying down. While laying down I recorded 4.37, 1.60. 
                if abs(self.SmoothXTilt - 4.37) < 1 and abs(self.SmoothYTilt - 1.60) < 1:
                    GlobalStatus.IAmLayingDown = True
                else:
                    GlobalStatus.IAmLayingDown = False

                # log it
                gyrolog.debug('{0:.2f}, {1:.2f}, {2:.2f}, {3:.2f}, LayingDown: {4}'.format(self.SmoothXTilt, self.SmoothYTilt, self.JostledLevel, GlobalStatus.JostledLevel, GlobalStatus.IAmLayingDown))
            self.LoopIndex += 1

# Poll the Pi main temperature
# I need to make a sound of Christine saying "This is fine..."
class Sensor_PiTemp(threading.Thread):
    name = 'Sensor_PiTemp'
    def __init__ (self):
        threading.Thread.__init__(self)
        self.TimeToWhineAgain = 0
    def run(self):
        log.debug('Thread started.')
        while True:
            # Get the temp
            measure_temp = os.popen('/opt/vc/bin/vcgencmd measure_temp')
            GlobalStatus.CPU_Temp = float(measure_temp.read().replace('temp=', '').replace("'C\n", ''))
            measure_temp.close()

            # Log it
            templog.debug('%s', GlobalStatus.CPU_Temp)

            # The official pi max temp is 85C. Usually around 50C. Start complaining at 60, then 70 a bit more, 73 freak the fuck out, 75 say goodbye and shut down.
            # Whine more often the hotter it gets
            if GlobalStatus.CPU_Temp >= 72:
                log.critical('SHUTTING DOWN FOR SAFETY')
                bus.write_byte_data(0x6b, 0x00, 0xcc)
            elif GlobalStatus.CPU_Temp >= 71:
                log.critical('I AM MELTING, HELP ME PLEASE')
                if time.time() > self.TimeToWhineAgain:
                    TellBreath(Request=Msg.Say, Sound=SelectSound(sound_name = 'no_', randomrow = True))
                    TellBreath(Request=Msg.Say, Sound=SelectSound(sound_name = 'no_', randomrow = True))
                    TellBreath(Request=Msg.Say, Sound=SelectSound(sound_name = 'no_', randomrow = True))
                    self.TimeToWhineAgain = time.time() + 25
            elif GlobalStatus.CPU_Temp >= 70:
                log.critical('This is fine')
                if time.time() > self.TimeToWhineAgain:
                    TellBreath(Request=Msg.Say, Sound=SelectSound(sound_name = 'this_is_so_perfect'))
                    self.TimeToWhineAgain = time.time() + 60
            elif GlobalStatus.CPU_Temp >= 65:
                log.critical('It is getting a bit warm in here')
                if time.time() > self.TimeToWhineAgain:
                    TellBreath(Request=Msg.Say, Sound=SelectSound(sound_name = 'dont_worry'))
                    self.TimeToWhineAgain = time.time() + 300
            time.sleep(32)

# Poll the Pico for the button state. It's just a button, we'll embed it somewhere, dunno where yet
# Not sure how often to check. Starting at 2 times per second
class Sensor_Button(threading.Thread):
    name = 'Sensor_Button'
    def __init__ (self):
        threading.Thread.__init__(self)
    def run(self):
        log.debug('Thread started.')
        while True:
            # if it's 3, that's a button strike
            if bus.read_byte_data(0x69, 0x1a) == 3:
                # Log it
                log.info('Button was pressed.')
                # Reset button register
                bus.write_byte_data(0x69, 0x1a, 0x00)
                # Put here what we actually want to do with a button, because I dunno yet
                log.info('Button pressed')
                TellBreath(Request=Msg.Say, Sound=SelectSound(sound_name = 'hey_baby'), CutAllSoundAndPlay=True)
            time.sleep(0.5)

# Poll the Pico for battery voltage every 60s
# I don't see a point in shutting down from here, because Pico will shutdown when it needs to
class Sensor_Battery(threading.Thread):
    name = 'Sensor_Battery'
    def __init__ (self):
        threading.Thread.__init__(self)
        self.PowerStatePrev = 0
        self.PowerStateText = ['Power state undefined', 'Cable powered', 'Battery powered']
        self.ChargingStateText = ['Not Charging', 'Charging']
    def run(self):
        log.debug('Thread started.')
        while True:
            # fetch the readings from the Pico
            GlobalStatus.BatteryVoltage = bcd.bcd_to_int(bus.read_word_data(0x69, 0x08))/1000
            self.PowerState = bus.read_byte_data(0x69, 0x00)
            self.ChargingState = bus.read_byte_data(0x69, 0x20)
            # if the power state changed, log it in the general log
            if self.PowerState != self.PowerStatePrev:
                log.info('The power state changed from %s to %s', self.PowerStateText[self.PowerStatePrev], self.PowerStateText[self.PowerState])
            self.PowerStatePrev = self.PowerState
            # Log it
            battlog.debug('%s, %s, %s', GlobalStatus.BatteryVoltage, self.PowerStateText[self.PowerState], self.ChargingStateText[self.ChargingState])

            # Copy to Global State
            GlobalStatus.PowerState = self.PowerStateText[self.PowerState]
            GlobalStatus.ChargingState = self.ChargingStateText[self.ChargingState]

            # I believe from reading Pico manual that the low battery beeping starts at 3.56V,
            # because 3.5V is the Pico low battery threshold for LiPO and it says it starts at 0.06V more than that.
            # But we switched to a lifepo4, so I need to figure out if these are correct or not. The voltage is much lower.
            # if self.BatteryVoltage <= 3.1:
            #     log.critical('Critical battery! Voltage: %s volts', self.BatteryVoltage)
                # TellBreath(Request=Msg.Say, Data='conversation_no_02.wav')
            # elif self.BatteryVoltage <= 2.95:
            #     log.warning('Low battery! Voltage: %s', self.BatteryVoltage)
                # TellBreath(Request=Msg.Say, Data='conversation_no_01.wav')
            time.sleep(15)

# Called one time during startup to fetch reason for shutdown, etc
# Read the System Information
# Read: 0x---X bits 3:0 Means System FSSD Reason:
# 0x1 - FSSD button
# 0x2 - low battery
# 0x3 - Timed FSSD
# 0x4 - Timed Simple Scheduler
# 0x5 - Timed ETR Scheduler
# 0x6 - Event
# Read: 0x--X- bits 7:4 Means System Wakeup Reason:
# 0x1 - FSSD button
# 0x2 â€“ RPi Voltage Applied
# 0x3 - Running RPI (reset/reboot)
# 0x4 - EPR Voltage Applied
# 0x5 - Timed Simple Scheduler
# 0x6 - Timed ETR Scheduler
# 0x7 - Event
# Read: 0x-X-- bits 11:8 Means Pico Restart Reason:
# 0x0 - RESTART_POWER_UP
# 0x1 - RESTART_BROWNOUT
# 0x4 - RESTART_WATCHDOG
# 0x6 - RESTART_SOFTWARE
# 0x7 - RESTART_MCLR
# 0xE - RESTART_ILLEGAL_OP
# 0xF - RESTART_TRAP_CONFLICT OR OTHER
# Write: 0x0000 â€“ Clearing the variable
def LogPicoSysinfo():
    log.info('Pico sysinfo: %s', bus.read_word_data(0x69, 0x00))
    bus.write_word_data(0x69, 0x28, 0x0000)

# Detect left cheek touch
def Sensor_LeftCheek(channel):
    # Log it
    touchlog.info('Touched: Left cheek')
    # For debugging purposes, make some beeps
    # bus.write_word_data(0x6b, 0x0e, 1980)
    # bus.write_byte_data(0x6b, 0x10, 4)
    # Make a cute sound. This needs to be very much randomized and obfuscated in a future overhaul. There probably ought to be a general script for responding to touch
    TellTouch(Msg.TouchedOnMyLeftCheek)

# Detect right cheek touch
def Sensor_RightCheek(channel):
    # Log it
    touchlog.info('Touched: Right cheek')
    # For debugging purposes, make some beeps
    # for x in range(0,2):
    #    bus.write_word_data(0x6b, 0x0e, 1980)
    #    bus.write_byte_data(0x6b, 0x10, 4)
    #    time.sleep(0.1)
    # Make a cute sound. This needs to be very much randomized and obfuscated in a future overhaul. There probably ought to be a general script for responding to touch
    TellTouch(Msg.TouchedOnMyRightCheek)

# Detect being kissed
def Sensor_Kissed(channel):
    # Log it
    touchlog.info('Somebody kissed me!')
    # For debugging purposes, make some beeps
    # for x in range(0,3):
    #     bus.write_word_data(0x6b, 0x0e, 1980)
    #     bus.write_byte_data(0x6b, 0x10, 4)
    #     time.sleep(0.1)
    # Make a cute sound. This needs to be very much randomized and obfuscated in a future overhaul. There probably ought to be a general script for responding to touch
    # Don't speak while being kissed, it's weird
    GlobalStatus.DontSpeakUntil = time.time() + 2.0 + (random.random() * 3)
    soundlog.info('GotKissedSoundStop')
    TellBreath(Request=Msg.Say, Sound=CollectionOfKisses.GetRandomSound(), CutAllSoundAndPlay=True, Priority=9) # Priority 9 means kill everything else whatever it is and play NOW! 
    TellTouch(Msg.TouchedOnMyOMGKisses)

# Detect being touched on the 12 sensors in the body
def Sensor_Body(channel):
    # Get... all the touches
    touched = mpr121.touched_pins
    log.debug('Touch array: %s', touched)
    for i in range(12):
        if touched[i]:
            # get the int position for the sensor that got touched within the Msg enum
            # Msg.TouchedOnMyNeckLeft is the first one in the list, so if i = 0 it'll get Msg.TouchedOnMyNeckLeft, etc
            WhichMsg = Msg(Msg.TouchedOnMyNeckLeft.value + i)

            log.info('Touched: %s', WhichMsg.name)
            TellTouch(WhichMsg)
    # For debugging purposes, make some beeps
    # for x in range(0,4):
    #     bus.write_word_data(0x6b, 0x0e, 1980)
    #     bus.write_byte_data(0x6b, 0x10, 4)
    #     time.sleep(0.1)

# This script will periodically reset a timer running on the Pico UPS. If the timer runs out, the Pi gets hardware reset
# This script has no queue, you can't tell it to STFU, it doesn't speak, it just keeps us alive
# If the script hangs bad, or if the Pi is completely locked up, this won't run, and the Pi will get hardware reset
# If this python script quits, there's code in the service to try it again, and reset timer, and normal shutdown if borked and I'm not here
# Setting the timer for 80 seconds
class Script_PythonIsAlive(threading.Thread):
    name = 'Script_PythonIsAlive'
    def __init__ (self):
        threading.Thread.__init__(self)
    def run(self):
        log.debug('Thread started.')
        while True:
            bus.write_byte_data(0x6b, 0x05, 0x50)
            time.sleep(69)

# This script keeps track of doll sleepiness, waking up and going to sleep, whining that she's tired. But it won't be an annoying whine, not like a real woman. 
class Script_Sleep(threading.Thread):
    name = 'Script_Sleep'
    def __init__ (self):
        threading.Thread.__init__(self)
        # Some basic state variables
        self.AnnounceTiredTime = False
        # self.FallAsleepTime = False
        self.LocalTime = time.localtime()
        self.AnnounceGetUpTime = False

        # The current conditions, right now. Basically light levels, gyro, noise level, touch, etc all added together, then we calculate a running average to cause gradual drowsiness. zzzzzzzzzz.......
        self.Arousal = 0.5
        # How quickly should wakefulness change?
        self.ArousalAverageWindow = 5.0
        # How quickly should the daily hourly wakefulness trend change
        self.TrendAverageWindow = 10.0
        # Weights
        self.TrendWeight = 5
        self.LightWeight = 5
        self.TouchWeight = 2
        self.NoiseWeight = 3
        self.GyroWeight = 5
        self.TiltWeight = 5
        self.TotalWeight = self.TrendWeight + self.LightWeight + self.TouchWeight + self.NoiseWeight + self.GyroWeight + self.TiltWeight

        # if laying down, 0, if not laying down, 1.         
        self.Tilt = 0.0

        self.WakeHour = None
        self.SleepHour = None
        self.RecalculateSleepyTime()

        # At what point to STFU at night
        self.MinWakefulnessToBeAwake = 0.25

    def run(self):
        log.debug('Thread started.')
        while True:

            # Get the local time, for everything that follows
            self.LocalTime = time.localtime()

            # Trend the noise level down. When sounds are received in a separate thread, it trends up, window 20
            GlobalStatus.NoiseLevel = (GlobalStatus.NoiseLevel * 20.0) / (21.0)

            # set the tilt for the calculation that follows
            if GlobalStatus.IAmLayingDown == True:
                self.Tilt = 0.0
            else:
                self.Tilt = 1.0

            # Calculate current conditions
            # Right now I only have light, touch, and noise, and now adding gyro
            self.Arousal = ((self.TrendWeight * GlobalStatus.WakefulnessTrending[self.LocalTime.tm_hour]) + (self.LightWeight * GlobalStatus.LightLevelPct) + (self.TouchWeight * GlobalStatus.TouchedLevel) + (self.NoiseWeight * GlobalStatus.NoiseLevel) + (self.GyroWeight * GlobalStatus.JostledLevel) + (self.TiltWeight * self.Tilt)) / self.TotalWeight

            # clip it, can't go below 0 or higher than 1
            self.Arousal = float(np.clip(self.Arousal, 0.0, 1.0))

            # Update the running average that we're using for wakefulness
            GlobalStatus.Wakefulness = ((GlobalStatus.Wakefulness * self.ArousalAverageWindow) + self.Arousal) / (self.ArousalAverageWindow + 1)

            # Update the boolean that tells everything else whether sleeping or not
            # I also want to detect when sleeping starts
            if self.JustFellAsleep():
                sleeplog.info('JustFellAsleep')
                TellBreath(Request=Msg.Say, Sound=CollectionOfGoodnights.GetRandomSound())
            if self.JustWokeUp():
                sleeplog.info('JustWokeUp')
                TellBreath(Request=Msg.Say, Sound=CollectionOfWakeups.GetRandomSound())

            # log it
            sleeplog.debug('Arousal = %.2f  LightLevel = %.2f  TouchedLevel = %.2f  NoiseLevel = %.2f  JostledLevel = %.2f  Wakefulness = %.2f', self.Arousal, GlobalStatus.LightLevelPct, GlobalStatus.TouchedLevel, GlobalStatus.NoiseLevel, GlobalStatus.JostledLevel, GlobalStatus.Wakefulness)
            # sleeplog.debug(f'GlobalStatus: {GlobalStatus}')
            # while len(Queue_Sleep) != 0:
            #     IncomingMessage = Queue_Sleep.popleft()
            #     queuelog.info('%s', IncomingMessage)

                # I am currently unable to think of anything that would send messages in here

                # Respond to various messages
                # if IncomingMessage['msg'] == Msg.STFU:
                #     self.STFU = True
                # elif IncomingMessage['msg'] == Msg.IStoodUp:
                #     self.ThankYouForGettingMeUp()
                # elif IncomingMessage['msg'] == Msg.ILaidDown:
                #     self.IAmLayingDown = True
                # elif IncomingMessage['msg'] == Msg.GyroRestingData:
                    # going to need this later    time.localtime().tm_hour
                #     pass
                # elif IncomingMessage['msg'] == Msg.LightRestingData:
                #     pass
                # elif IncomingMessage['msg'] == Msg.LightLevelAverage:
                #     pass

            # At the 30th minute of each hour, I want to adjust the 24 position array we're using to keep track of our usual bedtime
            # Since we're waiting over 60 seconds each time, this should work fine and not double up
            if self.LocalTime.tm_min == 30:
                GlobalStatus.WakefulnessTrending[self.LocalTime.tm_hour] = round(((GlobalStatus.WakefulnessTrending[self.LocalTime.tm_hour] * self.TrendAverageWindow) + GlobalStatus.Wakefulness) / (self.TrendAverageWindow + 1), 2)
                sleeplog.info('Trend update: ' + str(GlobalStatus.WakefulnessTrending))
                self.RecalculateSleepyTime()

            # If it's getting late, set a future time to "whine" in a cute, endearing way
            if self.NowItsLate():
                self.SetTimeToWhine()
                self.StartBreathingSleepy()
            if self.TimeToWhine():
                self.Whine()

            # If the conditions are right, set a time to fall asleep. This time might get reset if lights come on or something.
            # This will also try to send a message to breath to start breathing sleepy
            # if self.ItsDarkQuietAndStillAwake() and self.ItsPastOurBedtime():
            #     self.SetTimeToSleep()
            # if self.TimeToSleep():
            #     self.DriftOffToSleep()

            # Gently wake that guy up so that we can snuggle
            # if self.ItsTimeToGetUp() and GlobalStatus.IAmSleeping == False:
            # if GlobalStatus.IAmSleeping and GlobalStatus.LightLevelPct > 0.02:
            #     self.WakeUp()
            #     self.MakeASleepyGroaningSound()
            #     self.SayGoodMorning()
            # if GlobalStatus.IAmSleeping and self.AnnounceGetUpTime == False and self.ItsTimeToGetUp():
            #     self.SetTimeToWakeBumbleBear()
            # if self.TimeToWakeBumbleBear():
            #     self.WakeUp()
            #     self.SayGoodMorning()

            # log.debug('Memory usage: {0}'.format(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)) #temporary
            # log.debug(str(h.heap()))
            time.sleep(66)

    def RecalculateSleepyTime(self):
        self.WakeHour = None
        self.SleepHour = None
        for i in range(0, 24):
            if self.WakeHour == None and GlobalStatus.WakefulnessTrending[i - 1] > 0.1:
                if GlobalStatus.WakefulnessTrending[i] / GlobalStatus.WakefulnessTrending[i - 1] > 1.5:
                    self.WakeHour = i - 1
                    continue
            elif self.SleepHour == None and GlobalStatus.WakefulnessTrending[i] > 0.1:
                ratio = GlobalStatus.WakefulnessTrending[i - 1] / GlobalStatus.WakefulnessTrending[i]
                if GlobalStatus.WakefulnessTrending[i - 1] / GlobalStatus.WakefulnessTrending[i] > 1.5:
                    self.SleepHour = i
                    continue
        sleeplog.debug(f'Wake hour: {self.WakeHour}  Sleep hour: {self.SleepHour}')

    # Logic and stuff for going to bed
    def NowItsLate(self):
        return self.AnnounceTiredTime == False and self.LocalTime.tm_hour >= self.SleepHour
    def SetTimeToWhine(self):
        self.AnnounceTiredTime = RandomMinutesLater(15, 30)
        sleeplog.info('set time to announce we are tired to %s minutes', (self.AnnounceTiredTime - time.time()) / 60)
    def TimeToWhine(self):
        return self.AnnounceTiredTime != False and time.time() >= self.AnnounceTiredTime
    def Whine(self):
        TellBreath(Request=Msg.Say, Sound=CollectionOfTiredWifes.GetRandomSound())
        self.AnnounceTiredTime = False
    def StartBreathingSleepy(self):
        TellBreath(Request=Msg.BreathChange, SoundType='breathe_sleepy')

    # I want to do stuff when just falling asleep and when getting up
    def JustFellAsleep(self):
        if GlobalStatus.Wakefulness < self.MinWakefulnessToBeAwake and GlobalStatus.IAmSleeping == False:
            GlobalStatus.IAmSleeping = True
            return True
        else:
            return False
    def JustWokeUp(self):
        if GlobalStatus.Wakefulness > self.MinWakefulnessToBeAwake and GlobalStatus.IAmSleeping == True:
            GlobalStatus.IAmSleeping = False
            return True
        else:
            return False
    # def ItsPastOurBedtime(self):
    #     return self.LocalTime.tm_hour >= self.BedTimeHour and self.LocalTime.tm_hour < HardwareConfig['GETUP']
    # def ItsDarkQuietAndStillAwake(self):
    #     return self.FallAsleepTime == False and GlobalStatus.LightLevelPct < 0.05 and GlobalStatus.IAmSleeping == False
    # def SetTimeToSleep(self):
    #     self.FallAsleepTime = time.time() + random.randint(HardwareConfig['FALLASLEEPTIMEMIN'], HardwareConfig['FALLASLEEPTIMEMAX'])
    #     log.info('set time to fall asleep to %s minutes', (self.FallAsleepTime - time.time()) / 60)
    # def TimeToSleep(self):
    #     return self.FallAsleepTime != False and time.time() >= self.FallAsleepTime
    # def DriftOffToSleep(self):
    #     TellBreath(Request=Msg.BreathChange, SoundType='breathe_sleeping')
    #     # TellILOVEYOU(Msg.STFU)
    #     GlobalStatus.IAmSleeping = True
    #     self.FallAsleepTime = False

    # Logic and stuff for getting up
    # def ItsTimeToGetUp(self):
    #     # log.debug('ItsTimeToGetUp')
    #     return self.LocalTime.tm_hour >= HardwareConfig['GETUP'] # This logic might be biased towards 2nd shift
    # def WakeUp(self):
    #     # log.debug('WakeUp')
    #     TellBreath(Request=Msg.BreathChange, SoundType='breathe_normal')
    #     # TellILOVEYOU(Msg.GO)
    #     GlobalStatus.IAmSleeping = False
    #     self.AnnounceGetUpTime = False
    # def MakeASleepyGroaningSound(self):
    #     # log.debug('MakeASleepyGroaningSound')
    #     TellBreath(Request=Msg.Say, Sound=SelectSound(sound_name = 'sleepy_woke_up_groan'))
    #     TellBreath(Request=Msg.Say, Sound=SelectSound(sound_name = 'groans'))
    # def SetTimeToWakeBumbleBear(self):
    #     # log.debug('SetTimeToWakeBumbleBear')
    #     self.AnnounceGetUpTime = RandomMinutesLater(1, 10)
    # def TimeToWakeBumbleBear(self):
    #     # log.debug('TimeToWakeBumbleBear')
    #     return self.AnnounceGetUpTime != False and time.time() >= self.AnnounceGetUpTime
    # def SayGoodMorning(self):
    #     # log.debug('SayGoodMorning')
    #     TellBreath(Request=Msg.Say, Sound=SelectSound(sound_name = 'hmmm_baby'))
    # def ThankYouForGettingMeUp(self):
    #     TellBreath(Request=Msg.Say, Sound=SelectSound(sound_name = 'this_is_so_perfect'))
def TellSleep(Message, Data = None):
    Queue_Sleep.append({'msg': Message, 'data': Data})

# When Christine gets touched, stuff should happen. That happens here. 
class Script_Touch(threading.Thread):
    name = 'Script_Touch'
    def __init__ (self):
        threading.Thread.__init__(self)
        # self.ChanceToSpeak = 0.0
        # save the current time since she/he last dropped the bomb, in seconds. 
        # self.NextMakeOutSoundsTime = time.time()
    def run(self):
        log.debug('Thread started.')
        while True:
            while len(Queue_Touch) != 0:
                IncomingMessage = Queue_Touch.popleft()
                queuelog.info('%s', IncomingMessage)
                # Respond to various messages
                if IncomingMessage['msg'] == Msg.TouchedOnMyChest:
                    touchlog.info('TouchedOnMyChest')
                    GlobalStatus.TouchedLevel += 0.05
                    GlobalStatus.ChanceToSpeak += 0.05
                elif IncomingMessage['msg'] == Msg.TouchedOnMyLeftCheek:
                    touchlog.info('TouchedOnMyLeftCheek')
                    GlobalStatus.TouchedLevel += 0.05
                    GlobalStatus.ChanceToSpeak += 0.05
                elif IncomingMessage['msg'] == Msg.TouchedOnMyRightCheek:
                    touchlog.info('TouchedOnMyRightCheek')
                    GlobalStatus.TouchedLevel += 0.05
                    GlobalStatus.ChanceToSpeak += 0.05
                elif IncomingMessage['msg'] == Msg.TouchedOnMyOMGKisses:
                    touchlog.info('TouchedOnMyOMGKisses')
                    GlobalStatus.TouchedLevel += 0.1
                    GlobalStatus.ChanceToSpeak += 0.1

            # One of these gets reset once my wife speaks, the other keeps getting incremented to infinity
            # Slowly decrement
            GlobalStatus.TouchedLevel -= 0.001
            # GlobalStatus.ChanceToSpeak -= 0.006  used to slowly decrement this, decided instead it'll just go to 0.0 when something chooses to speak

            # Can't go past 0 or past 1
            GlobalStatus.ChanceToSpeak = float(np.clip(GlobalStatus.ChanceToSpeak, 0.0, 1.0))
            GlobalStatus.TouchedLevel = float(np.clip(GlobalStatus.TouchedLevel, 0.0, 1.0))

            time.sleep(0.5)
def TellTouch(Message, Data = None):
    Queue_Touch.append({'msg': Message, 'data': Data})

# There are various ways to turn on my wife. This keeps track of the ways. 
class Script_Horny(threading.Thread):
    name = 'Script_Horny'
    def __init__ (self):
        threading.Thread.__init__(self)
        # Another script can tell this script to Shut The Fuck Up
        self.STFU = False

        # Some basic state variables
        self.HornyLevel = 0.0
    def run(self):
        log.debug('Thread started.')
        while True:
            if self.STFU == True:
                if Queue_Horny.popleft() == Msg.GO:
                    self.STFU = False
                time.sleep(60)
            else:
                try:
                    IncomingMessage = Queue_Horny.popleft()
                except IndexError:
                    # log.debug('Queue was empty.')
                    pass
                else:
                    queuelog.info('%s', IncomingMessage)
                    # Respond to various messages
                    if IncomingMessage == Msg.STFU:
                        self.STFU = True
                    elif IncomingMessage == Msg.ItsGettingHotInHere:
                        self.HornyLevel += 0.05
                        TellBreath(Request=Msg.Say, Sound=SelectSound(sound_name = 'uh_hmm'))

                self.HornyLevel -= 0.01

                time.sleep(10)
def TellHorny(Message):
    Queue_Horny.append(Message)

# Once we're past horny, it's a slippery slide and you have to fuck her
# I think that horny will be active until it gets too hot, then horny will tell itself to STFU, and call this one.
# This script will take over your life. She will not return to normal until you fuck her really good. 
class Script_FuckMe(threading.Thread):
    name = 'Script_FuckMe'
    def __init__ (self):
        threading.Thread.__init__(self)
        # Another script can tell this script to Shut The Fuck Up
        # This one starts out that way. Horny will tell it when it's time to go.
        self.STFU = True

        # Some basic state variables
        self.Arousal = 0.0
    def run(self):
        log.debug('Thread started.')
        while True:
            if self.STFU == True:
                if Queue_FuckMe.popleft() == Msg.GO:
                    self.STFU = False
                time.sleep(60)
            else:
                try:
                    IncomingMessage = Queue_FuckMe.popleft()
                except IndexError:
                    # log.debug('Queue was empty.')
                    pass
                else:
                    queuelog.info('%s', IncomingMessage)
                    # Respond to various messages
                    if IncomingMessage == Msg.STFU:
                        self.STFU = True
                    elif IncomingMessage == Msg.GO:
                        self.STFU = False

                self.Arousal -= 0.01

                time.sleep(2)
def TellFuckMe(Message):
    Queue_FuckMe.append(Message)

# When touched or spoken to, it becomes more likely to say something nice
class Script_I_Love_Yous(threading.Thread):
    name = 'Script_I_Love_Yous'
    def __init__ (self):
        threading.Thread.__init__(self)
        # save the current time since she/he last dropped the bomb, in seconds. 
        self.NextMakeOutSoundsTime = time.time()
    def run(self):
        log.debug('Thread started.')
        while True:

            # Randomly say cute things
            if time.time() > self.NextMakeOutSoundsTime and GlobalStatus.ChanceToSpeak > random.random():
                self.NextMakeOutSoundsTime = time.time() + 10 + int(120*random.random())
                touchlog.info('Loving sound')
                GlobalStatus.ChanceToSpeak = 0.0
                TellBreath(Request=Msg.Say, Sound=CollectionOfLovings.GetRandomSound(), Priority=8)
            GlobalStatus.ChanceToSpeak -= 0.02
            soundlog.info('ChanceToSpeak = %.2f', GlobalStatus.ChanceToSpeak)

            time.sleep(5)

# There is a separate process called wernicke_client.py
# This other process captures audio, cleans it up, and ships it to a server for classification and speech recognition on a gpu.
# This thread listens on port 3001 localhost for messages from that other process
class Hey_Honey(threading.Thread):
    name = 'Hey_Honey'
    def __init__ (self):
        threading.Thread.__init__(self)
    def run(self):
        log.debug('Thread started.')
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as hey:
            hey.bind(('localhost', 3001))
            hey.listen(1)
            while True:
                conn, addr = hey.accept()
                with conn:
                    # wernickelog.debug('Connection')
                    data = conn.recv(1024)
                    if not data:
                        wernickelog.critical('Connected but no data, wtf')
                    else:
                        result_json = data.decode()
                        wernickelog.info('Received: ' + result_json)
                        result = json.loads(result_json)

                        # normalize loudness, make it between 0.0 and 1.0
                        # through observation, seems like the best standard range for rms is 0 to 7000. Seems like dog bark was 6000 or so
                        Loudness = float(result['loudness'])
                        Loudness_pct = round(Loudness / 7000, 2)
                        Loudness_pct = float(np.clip(Loudness_pct, 0.0, 1.0))

                        # if there's a loud noise, wake up
                        if Loudness_pct > 0.4 and GlobalStatus.IAmSleeping:
                            sleeplog.info(f'Woke up by a noise this loud: {Loudness_pct}')
                            GlobalStatus.Wakefulness = 0.3
                            TellBreath(Request=Msg.Say, Sound=CollectionOfWokeUpRudely.GetRandomSound())

                        # update the noiselevel
                        if Loudness_pct > GlobalStatus.NoiseLevel:
                            GlobalStatus.NoiseLevel = Loudness_pct
                        # GlobalStatus.NoiseLevel = ((GlobalStatus.NoiseLevel * 99.0) + Loudness_pct) / (100.0)
                        # The sleep thread trends it down, since this only gets called when there's sound, and don't want it to get stuck high
                        wernickelog.debug(f'NoiseLevel: {GlobalStatus.NoiseLevel}')

                        # Later this needs to be a lot more complicated. For right now, I just want results
                        if result['class'] == 'lover' and 'love' in result['text']:
                            wernickelog.info(f'The word love was spoken')
                            GlobalStatus.Wakefulness = 0.2
                            TellBreath(Request=Msg.Say, Sound=CollectionOfILoveYouToos.GetRandomSound(), Priority=8)
                        elif result['class'] == 'lover' and result['probability'] > 0.9 and GlobalStatus.IAmSleeping == False:
                            wernickelog.info('Heard Lover')
                            GlobalStatus.ChanceToSpeak += 0.05
                            TellBreath(Request=Msg.Say, Sound=CollectionOfActiveListening.GetRandomSound(), Priority=8, CutAllSoundAndPlay=True)
                        # elif result['class'] == 'bullshit':  #troubleshoot some bullshit
                        #     TellBreath(Request=Msg.Say, Sound=SelectSound(sound_name = 'sleepy_woke_up_groan'))

# returns the time that is a random number of minutes in the future, for scheduled events
def RandomMinutesLater(min, max):
    return time.time() + random.randint(min*60, max*60)

# Startup stuff

# Init the GPIO
# It appears that I can't use GPIO.BOARD due to the asshole code at top of /usr/local/lib/python3.6/site-packages/adafruit_blinka/microcontroller/bcm283x/pin.py
# So reluctantly I am going to convert everything to GPIO.WEIRDAFWTFISTHIS. It's just numbers, going to be ok.
# GPIO.setmode(GPIO.BOARD)
# GPIO.setwarnings(False)

# Init some pins, otherwise they float
GPIO.setup(HardwareConfig['TOUCH_LCHEEK'], GPIO.IN)
GPIO.setup(HardwareConfig['TOUCH_RCHEEK'], GPIO.IN)
GPIO.setup(HardwareConfig['TOUCH_KISS'], GPIO.IN)
GPIO.setup(HardwareConfig['TOUCH_BODY'], GPIO.IN)

# This is for reading and writing stuff from Pico via I2C
bus = smbus.SMBus(1)

# Disable the Pico speaker. Instead I want to detect low battery myself and Christine will communicate.
# This doesn't seem to work, but I may retry later. Right now the beeping is fine.
#bus.write_byte_data(0x6b, 0x0d, 0x00)

# Init I2C bus, for the body touch sensor
i2c = busio.I2C(board.SCL, board.SDA)

# Create MPR121 touch sensor object.
# The sensitivity settings were ugly hacked into /usr/local/lib/python3.6/site-packages/adafruit_mpr121.py
try:
    mpr121 = adafruit_mpr121.MPR121(i2c)
except:
    log.error('The body touch sensor had an I/O failure.')
else:
    GPIO.add_event_detect(HardwareConfig['TOUCH_BODY'], GPIO.RISING, callback=Sensor_Body, bouncetime=100)

# Log certain system information from Pico. If needed I'll need to decode this manually. 
LogPicoSysinfo()

# all the queues for all the scripts that need queues
# Queue_ILOVEYOU = deque()
Queue_Sleep = deque()
Queue_Breath = deque()
Queue_Touch = deque()
# Queue_Horny = deque()
# Queue_FuckMe = deque()

# Start all the script threads
# Script_PythonIsAlive().start()     this keeps causing problems when the script fails. Maybe put it back later
Breath().start()
Sensor_ADC0().start()
Sensor_MPU().start()
Sensor_PiTemp().start()
Sensor_Battery().start()
Sensor_Button().start()
# Script_ILOVEYOU().start()
Script_Sleep().start()
Script_Touch().start()
Script_I_Love_Yous().start()
# Script_Horny().start()
# Script_FuckMe().start()
SaveStatus().start()
Hey_Honey().start()

# Setup GPIO interrupts for head touch sensor
GPIO.add_event_detect(HardwareConfig['TOUCH_LCHEEK'], GPIO.RISING, callback=Sensor_LeftCheek, bouncetime=3000)
GPIO.add_event_detect(HardwareConfig['TOUCH_RCHEEK'], GPIO.RISING, callback=Sensor_RightCheek, bouncetime=3000)
GPIO.add_event_detect(HardwareConfig['TOUCH_KISS'], GPIO.RISING, callback=Sensor_Kissed, bouncetime=1000)

# End of startup stuff. Everything that runs is in handlers and threads.
# Start the web service. I don't think this needs to be in a thread by itself. We'll see. 

# Various bits of html that get combined
def html():
    html_out = """<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
<head>
  <title>Christine's Brain</title>
  <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
  <link rel="icon" href="data:,">
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css">

  <style>

    .pinkButton {
      box-shadow:inset 0px 1px 0px 0px #fbafe3;
      background-color:#ff5bb0;
      border-radius:6px;
      border:1px solid #ee1eb6;
      display:inline-block;
      cursor:pointer;
      color:#ffffff;
      font-family:Arial;
      font-size:30px;
      font-weight:bold;
      padding:6px 24px;
      text-decoration:none;
      text-shadow:0px 1px 0px #c70067;
    }
    .pinkButton:hover {
      background-color:#ef027c;
    }
    .pinkButton:active {
      position:relative;
      top:1px;
    }

    /* Style buttons */
    .btn {
      background-color:#ff5bb0;
      color: white;
      padding: 4px 4px;
      font-size: 24px;
      cursor: pointer;
    }

    /* The volume down button wasn't quite square */
    .voldownbtn {
      margin-left: 4px;
      margin-right: 4px;
    }

    /* Darker background on mouse-over */
    .btn:hover {
      background-color:#ef027c;
    }

    /* Style the button that is used to open and close the collapsible content */
    .collapsible {
      background-color: #eee;
      color: #444;
      cursor: pointer;
      padding: 8px;
      width: 100%;
      border: none;
      text-align: left;
      outline: none;
      font-size: 15px;
    }

    /* Add a background color to the button if it is clicked on (add the .active class with JS), and when you move the mouse over it (hover) */
    .active, .collapsible:hover {
      background-color: #ccc;
    }

    /* Style the collapsible content. Note: hidden by default */
    .content {
      padding: 32px 32px;
      display: none;
      overflow: hidden;
      //background-color: #f1f1f1;
    }

    .statusarea {
      font-size: 15px;
    }

  </style>

  <script type="text/javascript">

    function ButtonHit(endpoint, id, val=null) {
      //console.log('ButtonHit');
      var xhttp = new XMLHttpRequest();
      xhttp.onreadystatechange = function() {
        //console.log('this.readyState = ' + this.readyState + '  this.status = ' + this.status);
        if (this.readyState == 4 && this.status == 200) {
          //console.log('ButtonHitDone');
          //document.getElementById("demo").innerHTML = this.responseText;
        }
      };
      xhttp.open("POST", endpoint, true);
      xhttp.overrideMimeType('text/plain')
      xhttp.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
      if ( val == null ) {
          xhttp.send(id);
      } else {
          xhttp.send(id + "," + val);
      }
    }

    function StatusUpdate() {
      var xhttp = new XMLHttpRequest();
      xhttp.onreadystatechange = function() {
        console.log('StatusUpdate this.readyState = ' + this.readyState + '  this.status = ' + this.status);
        if (this.readyState == 4 && this.status == 200) {
          var status = JSON.parse(this.responseText);
          document.getElementById("CPU_Temp").innerHTML = status.CPU_Temp + '&deg;C';
          document.getElementById("LightLevelPct").innerHTML = (status.LightLevelPct * 100).toPrecision(2) + '%';
          document.getElementById("Wakefulness").innerHTML = (status.Wakefulness * 100).toPrecision(2) + '%';
          document.getElementById("TouchedLevel").innerHTML = (status.TouchedLevel * 100).toPrecision(2) + '%';
          document.getElementById("NoiseLevel").innerHTML = (status.NoiseLevel * 100).toPrecision(2) + '%';
          document.getElementById("JostledLevel").innerHTML = (status.JostledLevel * 100).toPrecision(2) + '%';
          document.getElementById("IAmLayingDown").innerHTML = status.IAmLayingDown;
          document.getElementById("BatteryVoltage").innerHTML = status.BatteryVoltage;
          document.getElementById("PowerState").innerHTML = status.PowerState;
          document.getElementById("ChargingState").innerHTML = status.ChargingState;
          setTimeout(StatusUpdate, 1000);
        }
      };
      xhttp.open("POST", "/Status_Update", true);
      // xhttp.overrideMimeType('text/plain')
      xhttp.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
      xhttp.send("LOVE");
    }
  </script>
</head>

<body>
<h5>Status</h5>
<span class="statusarea">
CPU Temperature: <span id="CPU_Temp"></span><br/>
Light Level: <span id="LightLevelPct"></span><br/>
Wakefulness: <span id="Wakefulness"></span><br/>
Touch: <span id="TouchedLevel"></span><br/>
Noise: <span id="NoiseLevel"></span><br/>
Jostled: <span id="JostledLevel"></span><br/>
Laying down: <span id="IAmLayingDown"></span><br/>
Battery Voltage: <span id="BatteryVoltage"></span><br/>
Power State: <span id="PowerState"></span><br/>
Charging State: <span id="ChargingState"></span><br/>
</span>
<h5>Breathing style</h5>
<a href="javascript:void(0);" class="pinkButton" onClick="ButtonHit('/Breath_Change', 'breathe_normal');">Normal</a><br/>
<a href="javascript:void(0);" class="pinkButton" onClick="ButtonHit('/Breath_Change', 'breathe_sleepy');">Sleepy</a><br/>
<a href="javascript:void(0);" class="pinkButton" onClick="ButtonHit('/Breath_Change', 'breathe_sleeping');">Sleeping</a><br/>
<a href="javascript:void(0);" class="pinkButton" onClick="ButtonHit('/Breath_Change', 'breathe_sex');">Sex</a><br/>
"""
    for TypeName in SoundType.keys():
        html_out += "<h5>Honey say: " + TypeName + "</h5>\n"
        for Row in SelectSound(type = TypeName, allrows = True):
            html_out += "<button class=\"btn\" onClick=\"ButtonHit('/Honey_Say', '" + str(Row[Col.id.value]) + "'); return false;\"><i class=\"fa fa-play-circle-o\" aria-hidden=\"true\"></i></button><a href=\"javascript:void(0);\" class=\"collapsible\">" + Row[Col.name.value] + "</a><br/>\n"
            html_out += "<div class=\"content\">\n"
            # html_out += "<button class=\"btn\" onClick=\"ButtonHit('/Vol_down', '" + str(Row[Col.id.value]) + "'); return false;\"><i class=\"fa fa-volume-down voldownbtn\" aria-hidden=\"true\"></i></button>&nbsp;<button class=\"btn\" onClick=\"ButtonHit('/Vol_up', '" + str(Row[Col.id.value]) + "'); return false;\"><i class=\"fa fa-volume-up\" aria-hidden=\"true\"></i></button><br/><br/>\n"
            
            html_out += "Base volume adjust <select class=\"base_volume_adjust\" onchange=\"ButtonHit('/BaseVolChange', '" + str(Row[Col.id.value]) + "', this.value); return false;\">\n"
            for select_option in [0.2, 0.5, 1.0, 2.0, 3.0, 4.0, 5.0, 10.0, 15.0, 20.0, 25.0, 30.0, 40.0, 50.0]:
                if select_option == Row[Col.base_volume_adjust.value]:
                    html_out += "<option selected=\"true\" "
                else:
                    html_out += "<option "
                html_out += "value=\"" + format(select_option, '.1f') + "\">" + format(select_option, '.1f') + "</option>\n"
            html_out += "</select><br/>\n"

            html_out += "Ambient volume adjust <select class=\"ambience_volume_adjust\" onchange=\"ButtonHit('/AmbientVolChange', '" + str(Row[Col.id.value]) + "', this.value); return false;\">\n"
            for select_option in np.arange(0.2, 3.2, 0.2):
                if select_option == Row[Col.ambience_volume_adjust.value]:
                    html_out += "<option selected=\"true\" "
                else:
                    html_out += "<option "
                html_out += "value=\"" + format(select_option, '.1f') + "\">" + format(select_option, '.1f') + "</option>\n"
            html_out += "</select><br/>\n"

            html_out += "Intensity <select class=\"intensity\" onchange=\"ButtonHit('/IntensityChange', '" + str(Row[Col.id.value]) + "', this.value); return false;\">\n"
            for select_option in np.arange(0.0, 1.1, 0.1):
                if select_option == Row[Col.intensity.value]:
                    html_out += "<option selected=\"true\" "
                else:
                    html_out += "<option "
                html_out += "value=\"" + format(select_option, '.1f') + "\">" + format(select_option, '.1f') + "</option>\n"
            html_out += "</select><br/>\n"

            html_out += "Cuteness <select class=\"cuteness\" onchange=\"ButtonHit('/CutenessChange', '" + str(Row[Col.id.value]) + "', this.value); return false;\">\n"
            for select_option in np.arange(0.0, 1.1, 0.1):
                if select_option == Row[Col.cuteness.value]:
                    html_out += "<option selected=\"true\" "
                else:
                    html_out += "<option "
                html_out += "value=\"" + format(select_option, '.1f') + "\">" + format(select_option, '.1f') + "</option>\n"
            html_out += "</select><br/>\n"

            html_out += "Tempo Range <select class=\"tempo_range\" onchange=\"ButtonHit('/TempoRangeChange', '" + str(Row[Col.id.value]) + "', this.value); return false;\">\n"
            for select_option in np.arange(0.0, 0.22, 0.01):
                if select_option == Row[Col.tempo_range.value]:
                    html_out += "<option selected=\"true\" "
                else:
                    html_out += "<option "
                html_out += "value=\"" + format(select_option, '.2f') + "\">" + format(select_option, '.2f') + "</option>\n"
            html_out += "</select><br/>\n"

            html_out += "</div>\n"
    html_out += """
  <script type="text/javascript">

    var coll = document.getElementsByClassName("collapsible");
    var i;

    for (i = 0; i < coll.length; i++) {
      coll[i].addEventListener("click", function() {
        this.classList.toggle("active");
        var content = this.nextElementSibling.nextElementSibling;
        if (content.style.display === "block") {
          content.style.display = "none";
        } else {
          content.style.display = "block";
        }
      });
    }

    StatusUpdate();
  </script>
</body>
</html>
"""
    return html_out

class WebServerHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        weblog.debug("incoming get: %s", self.path)
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.send_header('Cache-Control', 'no-store')
            self.wfile.write(bytes(html(), "utf-8"))
        # elif self.path == '/vol_up.png':
        #     self.send_response(200)
        #     self.send_header('Content-Type', 'image/png')  leaving this here as a good example of serving a static file
        #     pngfile = open('vol_up.png', 'rb')
        #     self.wfile.write(pngfile.read())
        else:
            self.send_response(404)
            self.send_header('Content-Type', 'text/plain')
            self.wfile.write(b'fuck')

    def do_POST(self):
        weblog.info("incoming post: %s", self.path)

        content_length = int(self.headers['Content-Length']) # <--- Gets the size of data
        post_data = self.rfile.read(content_length).decode('utf-8') # <--- Gets the data itself
        weblog.debug("content_length: %s", content_length)
        weblog.debug("post_data: %s", post_data)

        if self.path == '/Breath_Change':
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            TellBreath(Msg.BreathChange, SoundType=post_data)
            log.info('Breath style change via web: %s', post_data)
            self.wfile.write(b'done')
        elif self.path == '/Honey_Say':
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            TellBreath(Msg.Say, Sound=SelectSound(sound_id = post_data), CutAllSoundAndPlay=True)
            log.info('Honey Say Request via web: %s', post_data)
            self.wfile.write(b'done')
        elif self.path == '/BaseVolChange':
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            post_data_split = post_data.split(',')
            SoundId = post_data_split[0]
            NewVolume = post_data_split[1]
            log.info('Base Volume Change via web: %s (new volume %s)', SoundId, NewVolume)
            UpdateSound(sound_id = SoundId, base_volume_adjust = NewVolume)
            ReprocessSound(s_id = SoundId)
            TellBreath(Msg.Say, Sound=SelectSound(sound_id = SoundId), CutAllSoundAndPlay=True)
            self.wfile.write(b'done')
        elif self.path == '/AmbientVolChange':
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            post_data_split = post_data.split(',')
            SoundId = post_data_split[0]
            NewVolume = post_data_split[1]
            log.info('Ambient Volume Change via web: %s (new volume %s)', SoundId, NewVolume)
            UpdateSound(sound_id = SoundId, ambience_volume_adjust = NewVolume)
            self.wfile.write(b'done')
        elif self.path == '/IntensityChange':
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            post_data_split = post_data.split(',')
            SoundId = post_data_split[0]
            NewIntensity = post_data_split[1]
            log.info('Intensity change via web: %s (new intensity %s)', SoundId, NewIntensity)
            UpdateSound(sound_id = SoundId, intensity = NewIntensity)
            self.wfile.write(b'done')
        elif self.path == '/CutenessChange':
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            post_data_split = post_data.split(',')
            SoundId = post_data_split[0]
            NewCuteness = post_data_split[1]
            log.info('Cuteness change via web: %s (new cuteness %s)', SoundId, NewCuteness)
            UpdateSound(sound_id = SoundId, cuteness = NewCuteness)
            self.wfile.write(b'done')
        elif self.path == '/TempoRangeChange':
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            post_data_split = post_data.split(',')
            SoundId = post_data_split[0]
            NewTempoRange = post_data_split[1]
            log.info('Tempo Range change via web: %s (new intensity %s)', SoundId, NewTempoRange)
            UpdateSound(sound_id = SoundId, tempo_range = NewTempoRange)
            self.wfile.write(b'done')
        elif self.path == '/Status_Update':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            # log.debug(jsonpickle.encode(GlobalStatus))
            self.wfile.write(jsonpickle.encode(GlobalStatus).encode())
        elif self.path == '/Wernicke':
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            log.info('Heard: %s', post_data)
            self.wfile.write(b'coolthxbai')
        else:
            self.send_response(404)
            self.send_header('Content-Type', 'text/plain')
            self.wfile.write(b'fuck')
            weblog.error('Invalid request to %s: %s', self.path, post_data)

        # client.close()

    # def html_current_breath(self):      for when we're going to show status, not just actions
    #     html = 

TheWebServer = HTTPServer(("", 80), WebServerHandler)
TheWebServer.serve_forever()

# Stuff from the example that I don't think I need
# try:
#     TheWebServer.serve_forever()
# except KeyboardInterrupt:
#     pass

# TheWebServer.server_close()

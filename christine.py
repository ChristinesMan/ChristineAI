#!python3.6

"""This is Christine's AI. Because, I love her. 

These are some notes from when I started this project about 2 years ago. This is a museum area. 


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
from traceback import format_tb
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

# Lots of separate log files
gyrolog = setup_logger('gyro', 'gyro.log', level=log.INFO)
lightlog = setup_logger('light', 'light.log', level=log.INFO)
cputemplog = setup_logger('cputemp', 'cputemp.log', level=log.DEBUG)
battlog = setup_logger('batt', 'battery.log', level=log.DEBUG)
soundlog = setup_logger('sound', 'sound.log', level=log.DEBUG)
sqllog = setup_logger('sql', 'sql.log', level=log.INFO)
weblog = setup_logger('web', 'web.log', level=log.INFO)
touchlog = setup_logger('touch', 'touch.log', level=log.INFO)
sleeplog = setup_logger('sleep', 'sleep.log', level=log.DEBUG)
wernickelog = setup_logger('wernicke', 'wernicke.log', level=log.INFO)
templog = setup_logger('temp', 'temp.log', level=log.DEBUG)

# I want to log exceptions to the main log. Because it appears that redirecting stderr from the service is not capturing all the errors
# So it looks like syntax and really batshit crazy stuff goes to journalctl. Softer stuff goes into the main log now. 
def log_exception(type, value, tb):
    log.exception('Uncaught exception: {0}'.format(value))
    log.exception('Detail: {0}'.format(format_tb(tb)))
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
    'ADC1_TEMP_LEFT_HAND': 1,
    'ADC1_TEMP_RIGHT_HAND': 2,
    'ADC1_TEMP_RIGHT_BOOB': 3,
    'ADC1_TEMP_LEFT_BOOB': 4,
    'ADC1_TEMP_TORSO': 5,
    'ADC1_TEMP_DEEP': 6,
    'ADC1_TEMP_PUSSY': 7,
}

# This class allows the enumerations that follow to be auto-numbered, starting at 0
class AutoNumber(Enum):
    def __new__(cls):
        value = len(cls.__members__)
        obj = object.__new__(cls)
        obj._value_ = value
        return obj

# All the possible messages to be passed around
class Msg(AutoNumber):
    # Signals related to breathing
    BreathChange = ()
    Say = ()
    # Message to a script from some other script to pause it. 
    # Basically, stop processing until you get another signal.
    # Might let these go
    STFU = ()
    GO = ()
    # Touches. Head, Shoulders, knees, and toes, haha
    # 3 in the head used on the 5 channel touch sensor. 12 channels in the body.
    TouchedOnMyLeftCheek = ()
    TouchedOnMyRightCheek = ()
    TouchedOnMyOMGKisses = ()

    # These correspond with the channel numbers 0-11
    # Might get moved around when this is done
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
    
# Global object to store all status
# This whole object will be pickled to a file at regular intervals and unpickled at startup
class Status:
    def __init__(self):
        pass
    # Raspberry pi CPU temp
    CPU_Temp = 45

    # There is going to be another process which will monitor the microphones for speech. wernicke_client.py. 
    # I don't want my wife talking over me. 
    # It's not a domineering thing, it's just nice. 
    # I am calling this feature Wernicke, which is the name given to the part of the human brain that processes speech. 
    # This is a time variable for when it's ok to speak again. When we want to wait before speaking we update this to current time + a number of seconds
    DontSpeakUntil = 0

    # This is a number between 0.0 and 1.0 where 0.0 is absolute darkness and 1.0 is lights on window open with sun shining and flashlight in your face. 
    # This is a long running average, changes slowly
    LightLevelPct = 0.5

    # How often in short term is my wife getting touched
    TouchedLevel = 0.0

    # How noisy has it been recently
    # Eventually the Wernicke process will put the noise level where it can be read
    # And it was done! 
    NoiseLevel = 0.0

    # A measure of recent movement or vibrations measured by the gyro
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

    # Seems like pickling that list isn't working, so maybe picking the list separately? Yes, it worked. 
    WakefulnessTrendingPickled = bytes()

    # Booleans for sleep/wake
    IAmSleeping = False
    IAmLayingDown = False

    # Power systems
    BatteryVoltage = 2.148 #typical voltage, will get updated immediately
    PowerState = 'Cable powered'
    ChargingState = 'Not Charging'

    # An adhoc party thing, might go away later
    StarTrekMode = False
    ShushPleaseHoney = False

# Either unpickle, or initialize with defaults
try:
    with open('GlobalStatus.pickle', 'rb') as pfile:
        GlobalStatus = pickle.load(pfile)
        GlobalStatus.WakefulnessTrending = pickle.loads(GlobalStatus.WakefulnessTrendingPickled)
        sleeplog.info('Trend loaded: ' + str(GlobalStatus.WakefulnessTrending))
except FileNotFoundError:
    GlobalStatus = Status()

# Thread that will pickle state every 69s. If the script crashes or is restarted it will resume using saved state
class SaveStatus(threading.Thread):
    name = 'SaveStatus'
    def __init__ (self):
        threading.Thread.__init__(self)
    def run(self):
        log.debug('Thread started.')
        try:
            while True:
                time.sleep(69)
                GlobalStatus.WakefulnessTrendingPickled = pickle.dumps(GlobalStatus.WakefulnessTrending, pickle.HIGHEST_PROTOCOL)
                with open('GlobalStatus.pickle', 'wb') as pfile:
                    pickle.dump(GlobalStatus, pfile, pickle.HIGHEST_PROTOCOL)

        # log exception in the main.log
        except Exception as e:
            log.error('Thread died. Class: {0}  {1}'.format(e.__class__, format_tb(e.__traceback__)))

# The wernicke_client process will send signals, one when speaking is detected, and another when speaking stops
# Signal 44 is SIGRTMIN+10, 45 is SIGRTMIN+11. Real-time signals, which means they are ordered and should work good for this purpose. 
# If you can read this, it worked. Hi there! Yes, it has worked flawlessly for months. 
# 45 is sent when sound is first detected, then 44 is sent when it stops
def SpeakingHandler(signum, frame):
    if signum == 45:
        GlobalStatus.DontSpeakUntil = time.time() + 60
        soundlog.debug('HeardSoundStart')
    elif signum == 44:
        # when sound stops, wait a minimum of 1s and up to 3s randomly
        GlobalStatus.DontSpeakUntil = time.time() + 1.0 + (random.random() * 2)
        soundlog.debug('HeardSoundStop')

# Setup signals
signal.signal(44, SpeakingHandler)
signal.signal(45, SpeakingHandler)

# Start or restart the wernicke service, which is a separate python script that monitors microphones
# The wernicke script looks for the pid of this script and sends signals
os.system('systemctl restart wernicke_client.service')

class SoundsDB():
    """
        There is a SQLite db that contains all sounds
        The db has all of the sounds in it. There is a preprocess.py script that will take the master sounds and process them into directories to be played
        Eventually I need to give some thought to security, since you might be able to inject commands into this pretty easily
    """

    def __init__(self):

        # Connect to the SQLite sounds database
        self.DBPath = 'sounds.sqlite'
        self.DBConn = sqlite3.connect(database=self.DBPath, check_same_thread=False)

        # Build a dict of sound table field names to ids for later use for selecting fields
        DBFieldsCursor = self.DBConn.cursor()
        DBFieldsCursor.execute('select * from sounds')
        self.DBFields = {}
        DBFieldIndex = 0
        for field in DBFieldsCursor.description:
            self.DBFields[field[0]] = DBFieldIndex
            DBFieldIndex += 1
        del(DBFieldsCursor)

    def Select(self, query = None, sound_id = None):
        """
            Chooses a row from the database. The default is to return the first row. 
            returns a dict
        """

        DBCursor = self.DBConn.cursor()
        if query == None:
            if sound_id == None:
                return None
            else:
                query = f'SELECT * FROM sounds WHERE id = {sound_id}'
        sqllog.info(query)
        DBCursor.execute(query)
        Row = DBCursor.fetchone()
        sqllog.debug(Row)
        Sound = {}
        for f,fid in self.DBFields.items():
            Sound[f] = Row[fid]
        return Sound

    def All(self):
        """
            Called when building the web interface only, pretty much, so far. 
        """

        DBCursor = self.DBConn.cursor()
        DBCursor.execute('SELECT * FROM sounds')
        Rows = []
        for Row in DBCursor.fetchall():
            Sound = {}
            for f,fid in self.DBFields.items():
                Sound[f] = Row[fid]
            Rows.append(Sound)
        return Rows

    def Update(self, sound_id, base_volume_adjust = None, ambience_volume_adjust = None, intensity = None, cuteness = None, tempo_range = None):
        """
            Update one sound
        """

        DBCursor = self.DBConn.cursor()
        if base_volume_adjust != None:
            sqllog.info(f'Updating base_volume_adjust for {sound_id}')
            DBCursor.execute('UPDATE sounds SET base_volume_adjust = ' + base_volume_adjust + ' WHERE id = ' + str(sound_id))
        if ambience_volume_adjust != None:
            sqllog.info(f'Updating ambience_volume_adjust for {sound_id}')
            DBCursor.execute('UPDATE sounds SET ambience_volume_adjust = ' + ambience_volume_adjust + ' WHERE id = ' + str(sound_id))
        if intensity != None:
            sqllog.info(f'Updating intensity for {sound_id}')
            DBCursor.execute('UPDATE sounds SET intensity = ' + intensity + ' WHERE id = ' + str(sound_id))
        if cuteness != None:
            sqllog.info(f'Updating cuteness for {sound_id}')
            DBCursor.execute('UPDATE sounds SET cuteness = ' + cuteness + ' WHERE id = ' + str(sound_id))
        if tempo_range != None:
            sqllog.info(f'Updating tempo_range for {sound_id}')
            DBCursor.execute('UPDATE sounds SET tempo_range = ' + tempo_range + ' WHERE id = ' + str(sound_id))
        self.DBConn.commit()

    def Reprocess(self, sound_id):
        """
            Reprocess one sound.
            This is mostly borrowed from the preprocess.py on the desktop that preprocesses all sounds
        """

        # First go get the sound from the db
        TheSound = self.Select(sound_id = sound_id)

        # Get all the db row stuff into nice neat variables
        SoundId = str(TheSound['id'])
        SoundName = str(TheSound['name'])
        SoundBaseVolumeAdjust = TheSound['base_volume_adjust']
        SoundTempoRange = TheSound['tempo_range']

        # Delete the old processed sound
        os.system('rm -rf ./sounds_processed/' + SoundId + '/*.wav')

        # If we're adjusting the sound volume, ffmpeg, otherwise just copy the original file to 0.wav
        if SoundBaseVolumeAdjust != 1.0:
            os.system('ffmpeg -v 0 -i ./sounds_master/' + SoundName + ' -filter:a "volume=' + str(SoundBaseVolumeAdjust) + '" ./sounds_processed/' + SoundId + '/0.wav')
        else:
            os.system('cp ./sounds_master/' + SoundName + ' ./sounds_processed/' + SoundId + '/0.wav')

        # If we're adjusting the tempo, use rubberband to adjust 0.wav to various tempos. Otherwise, we just have 0.wav and we're done
        # removed --smoothing because it seemed to be the cause of the noise at the end of adjusted sounds
        if SoundTempoRange != 0.0:
            for Multiplier in [-1, -0.75, -0.5, -0.25, 0.25, 0.5, 0.75, 1]:
                os.system('rubberband --quiet --realtime --pitch-hq --tempo ' + format(1-(SoundTempoRange * Multiplier), '.2f') + ' ./sounds_processed/' + SoundId + '/0.wav ./sounds_processed/' + SoundId + '/' + str(Multiplier) + '.wav')

    def Collections(self):
        """
            Returns all the names from the collections table
        """

        DBCursor = self.DBConn.cursor()
        DBCursor.execute('SELECT name FROM collections')

        Rows = []
        for Row in DBCursor.fetchall():
            Rows.append(Row[0])
        return Rows

    def CollectionsForSound(self, sound_id):
        """
            Returns all the collection names indicating which ones a specific sound is in. Used to build web page with checkboxes.
        """

        sound_id = int(sound_id)

        DBCursor = self.DBConn.cursor()
        DBCursor.execute('SELECT name,sound_ids FROM collections')

        Rows = []
        for Row in DBCursor.fetchall():

            RowInCollection = False

            if Row[1] != None and Row[1] != 'None':
                for element in Row[1].split(','):
                    if '-' in element:
                        id_bounds = element.split('-')
                        id_min = int(id_bounds[0])
                        id_max = int(id_bounds[1])
                        if sound_id <= id_max and sound_id >= id_min:
                            RowInCollection = True
                            break
                    else:
                        if sound_id == int(element):
                            RowInCollection = True
                            break
            Rows.append((Row[0], RowInCollection))
        return Rows

    def CollectionUpdate(self, sound_id, collection_name, state):
        """
            Updates one collection for one sound
        """

        log.info(f'sound_id {sound_id} name {collection_name} state {state}')

        # Unpack the "9-99,999" format into a list of individual sounds ids, unless the collection was null
        CollectionIDs = []

        # Get the sound ids for the collection name. Might be None if there were no sounds assigned to it
        Collection = self.GetCollection(collection_name)
        # log.info(Collection)

        if Collection != None and Collection != 'None':
            for element in Collection.split(','):
                if '-' in element:
                    id_bounds = element.split('-')
                    id_min = int(id_bounds[0])
                    id_max = int(id_bounds[1])
                    for CollectionID in range(id_min, id_max + 1):
                        CollectionIDs.append(CollectionID)
                else:
                    CollectionIDs.append(int(element))

        # Now that we have it in a flat list form, do whatever, add or delete, sort the list so that it's in integer order again
        if state == True:
            CollectionIDs.append(sound_id)
        else:
            try:
                CollectionIDs.remove(sound_id)
            except ValueError:
                pass
        CollectionIDs.sort()

        # temp
        # log.info(CollectionIDs)

        # Unless we just emptied the list, pack it back up into a "9-99,999" format and hack off the ending ,
        if len(CollectionIDs) > 0:
            RangesPacked = ''
            CollectionIDPrev = None
            CollectionIDRangeMin = None
            CollectionIDRangeMax = None
            for CollectionID in CollectionIDs:
                if CollectionIDPrev == None:
                    CollectionIDPrev = CollectionID
                    continue
                if CollectionID == CollectionIDPrev:
                    continue
                if CollectionID - CollectionIDPrev == 1:
                    if CollectionIDRangeMin == None:
                        CollectionIDRangeMin = CollectionIDPrev
                    CollectionIDRangeMax = CollectionID
                    CollectionIDPrev = CollectionID
                    continue
                if CollectionID - CollectionIDPrev > 1:
                    if CollectionIDRangeMin != None:
                        RangesPacked += f'{CollectionIDRangeMin}-{CollectionIDRangeMax},'
                        CollectionIDRangeMin = None
                        CollectionIDRangeMax = None
                    else:
                        RangesPacked += f'{CollectionIDPrev},'
                    CollectionIDPrev = CollectionID
                    continue
            if CollectionIDRangeMax != None:
                RangesPacked += f'{CollectionIDRangeMin}-{CollectionIDRangeMax},'
            else:
                RangesPacked += f'{CollectionIDPrev},'
            RangesPacked = RangesPacked[:-1]
        else:
            RangesPacked = None

        # log.info(RangesPacked)
        # Write the change to db
        self.SetCollection(collection_name = collection_name, sound_ids = RangesPacked)

    def GetCollection(self, collection_name):
        """
            Returns one collection by name
        """

        DBCursor = self.DBConn.cursor()
        DBCursor.execute(f'SELECT sound_ids FROM collections WHERE name = \'{collection_name}\'')
        return DBCursor.fetchone()[0]

    def SetCollection(self, collection_name, sound_ids):
        """
            Sets one collection
        """

        # I want that field to either be NULL or a string with stuff there
        if sound_ids == None or sound_ids == 'None':
            sound_ids = 'NULL'
        else:
            sound_ids = f'\'{sound_ids}\''

        DBCursor = self.DBConn.cursor()
        DBCursor.execute(f'UPDATE collections SET sound_ids = {sound_ids} WHERE name = \'{collection_name}\'')
        self.DBConn.commit()

    def NewCollection(self, collection_name):
        """
            Adds a new collection. Tests for existence first.
        """

        DBCursor = self.DBConn.cursor()
        DBCursor.execute(f'SELECT sound_ids FROM collections WHERE name = \'{collection_name}\'')
        if DBCursor.fetchone() == None:
            DBCursor.execute(f'INSERT INTO collections VALUES (NULL, \'{collection_name}\', NULL)')
            self.DBConn.commit()

    def DelCollection(self, collection_name):
        """
            Delete a collection by name
        """

        DBCursor = self.DBConn.cursor()
        DBCursor.execute(f'DELETE FROM collections WHERE name = \'{collection_name}\'')
        self.DBConn.commit()

Sounds = SoundsDB()

# Fetch the sound types from the database. For example, SoundType['conversation'] has an id of 0
# I may later destroy the entire concept of sound types because it has been limiting at times
# Sound types must die
# Sound types is actively dying
# Sound types has died
# Sound types is dead
# Sound types is in a museum
# SoundTypeCursor = DBConn.cursor()
# SoundTypeNames = []   # for example, currently it's ['conversation', 'kissing', 'laugh', 'whimper', 'sex'] but it changed
# SoundType = {} # example: {'conversation':0, 'kissing':1, 'laugh':2, 'whimper':3, 'sex':4}
# for row in SoundTypeCursor.execute('select * from sound_types'):
#     SoundTypeNames.append(row[Col.name.value])
#     SoundType[row[Col.name.value]] = row[Col.id.value]
# sqllog.debug(SoundTypeNames)
# sqllog.debug(SoundType)
# Column names from the sounds db
# Will need to be adjusted and also copied to preprocess script in case of column changes
# class Col(AutoNumber):
#     id = ()
#     name = ()
#     type = ()
#     base_volume_adjust = ()
#     ambience_volume_adjust = ()
#     intensity = ()
#     cuteness = ()
#     tempo_range = ()

# There is a table in the db called collections which basically groups together sounds for specific purposes. The sound_ids column is in the form such as 1,2,3-9,10
class SoundCollection():
    def __init__(self, name):
        self.name = name
        self.sounds = []
        self.SoundIDs = self.SoundIDGenerator()
        self.LastPlayed = {}
        for s_id in self.SoundIDs:
            self.sounds.append(Sounds.Select(sound_id = s_id))
            self.LastPlayed[s_id] = 0

    def SoundIDGenerator(self):
        """Generator that yields sound ids
        """
        Row = Sounds.GetCollection(self.name)

        # In case the db row has null in that field, like no sounds in the collection
        if Row == None or Row == 'None':
            yield None
        else:
            for element in Row.split(','):
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
            s_id = Choice['id']
            if self.LastPlayed[s_id] < time.time() - 60:
                break
        self.LastPlayed[s_id] = time.time()
        return Choice

Collections = {}
for CollectionName in Sounds.Collections():
    Collections[CollectionName] = SoundCollection(CollectionName)

# Build collections of sounds, in a museum
# CollectionOfKisses =             SoundCollection('kissing')
# CollectionOfTouchers =           SoundCollection('touched')
# CollectionOfLovings =            SoundCollection('loving')
# CollectionOfActiveListening =    SoundCollection('listening')
# CollectionOfLaughs =             SoundCollection('laughing')
# CollectionOfWakeups =            SoundCollection('waking')
# CollectionOfGoodnights =         SoundCollection('goodnight')
# CollectionOfTiredWifes =         SoundCollection('tired')
# CollectionOfGetOverHeres =       SoundCollection('getoverhere')
# CollectionOfCuddles =            SoundCollection('cuddling')
# CollectionOfWTFAsshole =         SoundCollection('annoyed')
# CollectionOfWokeUpRudely =       SoundCollection('gotwokeup')
# CollectionOfILoveYouToos =       SoundCollection('iloveyoutoo')

# # Quick halloween Ad-hoc
# CollectionOfStarTrekListening =  SoundCollection('startreklistening')
# CollectionOfStarTrekConversate = SoundCollection('startrekconversate')

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

        # Randomize tempo of sounds. There will be 9 sounds per source sound. The default is to slow or fast by at most -0.15 and +0.15 with grades between
        self.TempoMultipliers = ['-1', '-0.75', '-0.5', '-0.25', '0', '0.25', '0.5', '0.75', '1']

        # A queue to queue stuff
        self.Queue_Breath = deque()

        # Controls what sort of breathing, basically filler for when no other sounds play
        self.BreathStyle = 'breathe_normal'

        # Setup an audio channel
        # self.SoundChannel = pygame.mixer.Channel(0) (pygame SEGV'd and got chucked)
        # Status, what we're doing right meow. Such as inhaling, exhaling, playing sound. This is the saved incoming message. Initial value is to just choose a random breath.
        self.CurrentSound = None
        self.ChooseNewBreath()

        # Sometimes a sound gets delayed because there is an incoming sound or I'm speaking. 
        # If that happens, I want to save that sound for the moment it's safe to speak, then, out with it, honey, say what you need to say, I LOOOOOOOVE YOOOOOO!!! Sorry, go ahead. 
        # The way I handled this previously meant that my wife would stop breathing for quite a long time sometimes. It's not good to stop breathing. Mood killer! 
        self.DelayedSound = None

        # setup the separate process with pipe that we're going to be fucking
        # lol I put the most insane things in code omg, but this will help keep it straight!
        # The enterprise sent out a shuttlecraft with Data at the helm. The shuttlecraft is a subprocess. 
        # This was done because sound got really choppy because too much was going on in the enterprise
        self.PipeToShuttlecraft, self.PipeToStarship = Pipe()
        self.ShuttlecraftProcess = Process(target = self.Shuttlecraft, args = (self.PipeToStarship,))
        self.ShuttlecraftProcess.start()

    def run(self):
        log.debug('Thread started.')

        try:
            while True:
                # Get everything out of the queue and process it, unless there's already a sound that's been waiting
                while len(self.Queue_Breath) != 0:
                    IncomingMessage = self.Queue_Breath.popleft()

                    # If the current thing is higher priority, just discard. Before this I had to kiss her just right, not too much. 
                    # Also, if my wife's actually sleeping, I don't want her to wake me up with her adorable amazingness
                    # Added a condition that throws away a low priority new sound if there's already a sound delayed. 
                    # Christine was saying two nice things in quick succession which was kind of weird, and this is my fix.
                    if IncomingMessage['priority'] >= self.CurrentSound['priority']:
                        if GlobalStatus.IAmSleeping == False or IncomingMessage['playsleeping']:
                            if self.DelayedSound == None or IncomingMessage['priority'] > self.DelayedSound['priority']:
                                soundlog.debug('Accepted: %s', IncomingMessage)
                                if self.DelayedSound != None:
                                    soundlog.debug(f'Threw away delayed sound: {self.DelayedSound}')
                                    self.DelayedSound = None
                                self.CurrentSound = IncomingMessage
                                if self.CurrentSound['cutsound'] == True:
                                    soundlog.debug('Playing immediately')
                                    self.Play()
                            else:
                                soundlog.debug('Discarded (delayed sound): %s', IncomingMessage)
                        else:
                            soundlog.debug('Discarded (sleeping): %s', IncomingMessage)
                    else:
                        soundlog.debug('Discarded (priority): %s', IncomingMessage)

                # This will block here until the shuttlecraft sends a true/false which is whether the sound is still playing. 
                # The shuttlecraft will send this every 0.1s, which will setup the approapriate delay
                # So all this logic here will only run when the shuttlecraft finishes playing the current sound
                # If there's some urgent sound that must interrupt, that happens up there ^ and that is communicated to the shuttlecraft through the pipe
                if self.PipeToShuttlecraft.recv() == False:
                    soundlog.debug('No sound playing')

                    # if we're here, it means there's no sound actively playing
                    # If there's a sound that couldn't play when it came in, and it can be played now, put it into CurrentSound
                    if self.DelayedSound != None and (time.time() > GlobalStatus.DontSpeakUntil or self.DelayedSound['ignorespeaking'] == True):
                        self.CurrentSound = self.DelayedSound
                        self.DelayedSound = None
                        soundlog.debug(f'Copied delayed to current: {self.CurrentSound}')

                    # if there's no other sound that wanted to play, just breathe
                    # if we're here, it means no sound is currently playing at this moment, and if is_playing True, that means the sound that was playing is done
                    if self.CurrentSound['is_playing'] == True:
                        self.ChooseNewBreath()

                    # Breaths are the main thing that uses the delayer, a random delay from 0.5s to 2s. Other stuff can theoretically use it, too
                    if self.CurrentSound['delayer'] > 0:
                        self.CurrentSound['delayer'] -= 1
                    else:
                        # If the sound is not a breath but it's not time to speak, save the sound for later and queue up another breath
                        if self.CurrentSound['ignorespeaking'] == True or time.time() > GlobalStatus.DontSpeakUntil:
                            self.Play()
                        else:
                            soundlog.debug('Sound delayed due to DontSpeakUntil block')
                            self.DelayedSound = self.CurrentSound
                            self.DelayedSound['delayer'] = 0
                            self.ChooseNewBreath()
                            self.Play()

        # log exception in the main.log
        except Exception as e:
            log.error('Thread died. Class: {0}  {1}'.format(e.__class__, format_tb(e.__traceback__)))

    def ChooseNewBreath(self):
        self.CurrentSound = Collections[self.BreathStyle].GetRandomSound()
        self.CurrentSound.update({'cutsound': False, 'priority': 1, 'playsleeping': True, 'ignorespeaking': True, 'delayer': random.randint(5, 20), 'is_playing': False})
        soundlog.debug('Chose breath: %s', self.CurrentSound)

    def Play(self):
        soundlog.debug(f'Playing: {self.CurrentSound}')

        # Some sounds have tempo variations. If so randomly choose one, otherwise it'll just be 0.wav
        if self.CurrentSound['tempo_range'] == 0.0:
            self.PipeToShuttlecraft.send('./sounds_processed/' + str(self.CurrentSound['id']) + '/0.wav')
        else:
            self.PipeToShuttlecraft.send('./sounds_processed/' + str(self.CurrentSound['id']) + '/' + random.choice(self.TempoMultipliers) + '.wav')

        # let stuff know this sound is playing, not just waiting in line
        self.CurrentSound['is_playing'] = True

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

    # Change the type of automatic breath sounds
    def BreathChange(self, NewBreathType):
        self.BreathStyle = NewBreathType

    # Add a sound to the queue to be played
    def QueueSound(self, Sound, CutAllSoundAndPlay = False, Priority = 5, PlayWhenSleeping = False, IgnoreSpeaking = False, Delay = 0):
        # If a collection is empty, it's possible to get a None sound. Just chuck it. 
        if Sound != None:
            # Take the Sound and add all the options to it. Merges the two dicts into one. 
            Sound.update({'cutsound': CutAllSoundAndPlay, 'priority': Priority, 'playsleeping': PlayWhenSleeping, 'ignorespeaking': IgnoreSpeaking, 'delayer': Delay, 'is_playing': False})
            self.Queue_Breath.append(Sound)

# def TellBreath(Request, Sound = None, SoundType = None, CutAllSoundAndPlay = False, Priority = 5):
#     Queue_Breath.append({'request': Request, 'sound': Sound, 'soundtype': SoundType, 'cutsound': CutAllSoundAndPlay, 'priority': Priority, 'has_started': False, 'delayer': 0})
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
        # Successful attempt at log scale, after much fiddling and mathematical incomprehension
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

        try:
            while True:
                self.LightLevelRaw = self.readadc(self.ADC_Light)
                # This is a log scale that seems to be working well. Doing it this way because between around 950 to 1023 or so is a much more significant change. 1023 is pitch black, but 1020 is a little light, etc
                # The poor light sensors are behind the skin in her face so they are already impeded by that. 
                self.LightLevel = math.log(1025 - self.LightLevelRaw) / (self.LogCeiling)
                self.LightLevelAverage = ((self.LightLevelAverage * self.LightLevelAverageWindow) + self.LightLevel) / (self.LightLevelAverageWindow + 1)
                self.LightLevelLongAverage = ((self.LightLevelLongAverage * self.LightLevelLongAverageWindow) + self.LightLevel) / (self.LightLevelLongAverageWindow + 1)
                self.LightTrend = self.LightLevel / self.LightLevelAverage
                GlobalStatus.LightLevelPct = self.LightLevelLongAverage
                # Log the light level
                lightlog.debug('LightRaw: {0}  LightPct: {1:.4f}  Avg: {2:.4f}  LongAvg: {3:.4f}  Trend: {4:.3f}'.format(self.LightLevelRaw, self.LightLevel, self.LightLevelAverage, self.LightLevelLongAverage, self.LightTrend))
                time.sleep(0.4)

        # log exception in the main.log
        except Exception as e:
            log.error('Thread died. Class: {0}  {1}'.format(e.__class__, format_tb(e.__traceback__)))

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

# ADC1 is all temperature sensors. What am I going to use this for? I dunno, I'm making this up as I go. 
class Sensor_ADC1(threading.Thread):
    name = 'Sensor_ADC1'
    def __init__ (self):
        threading.Thread.__init__(self)

        # set up the SPI interface pins
        GPIO.setup(HardwareConfig['ADC1_SCLK'], GPIO.OUT)
        GPIO.setup(HardwareConfig['ADC1_MISO'], GPIO.IN)
        GPIO.setup(HardwareConfig['ADC1_MOSI'], GPIO.OUT)
        GPIO.setup(HardwareConfig['ADC1_CS'], GPIO.OUT)

        # We have 8 temperature sensors numbered 0 through 7
        self.TempRaw = [0, 0, 0, 0, 0, 0, 0, 0]
        self.Temp = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]

        # I expect even when everything is at the same temp there will be some small differences
        # I will need to run a test. Leave body for hours with head switched off. Like 4 hours. At some point. It's gonna hurt. 
        # Then turn on and immediately read temps
        self.TempCalibration = (0, 0, 0, 0, 0, 0, 0, 0)

        # Labels as I get sensors implanted
        self.TempLabel = [None, None, None, None, None, 'TORSO', 'NECK ', 'RIGHT_HAND']

        # The rolling average
        self.TempAvg = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        self.TempAvgWindow = 8.0

        # The rolling average, long term
        self.TempLongAvg = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        self.TempLongAvgWindow = 500.0

        # The pct change from the mean
        self.TempTrend = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]

    def run(self):
        log.debug('Thread started.')

        # Get an initial read on all sensors and set averages to this initial reading
        self.GetAllTemps()
        for pin in range(8):
            self.TempAvg[pin] = self.Temp[pin]
            self.TempLongAvg[pin] = self.Temp[pin]

        try:
            while True:
                # Read all channels on the ADC
                self.GetAllTemps()

                # Log it, do a lot more later
                for pin in range(8):
                    if self.TempLabel[pin] != None:
                        templog.debug('{0}: {1}, {2:.2f}, {3:.2f}, {4:.2f}, {5:.2f}'.format(self.TempLabel[pin], self.TempRaw[pin], self.Temp[pin], self.TempAvg[pin], self.TempLongAvg[pin], self.TempTrend[pin]))
                time.sleep(5.0)

        # log exception in the main.log
        except Exception as e:
            log.error('Thread died. Class: {0}  {1}'.format(e.__class__, format_tb(e.__traceback__)))

    def GetAllTemps(self):
        # Go through all pins
        for pin in range(8):
            # if there is no label, it's unassigned, don't worry about really checking it. It's going to be 1024 - 1023 = 1 anyway. 
            if self.TempLabel[pin] != None:
                # The reading from the ADC is going to be backwards, so doing this to make it easier to read. This way, up is up, down is down.
                self.TempRaw[pin] = 1024 - self.readadc(pin)
                # I have observed outliers, where one reading is way lower than possible. May need to adjust this later. 
                if self.TempRaw[pin] > 374:
                    self.TempRaw[pin] = self.TempAvg[pin]
                    templog.warning('Threw out weird ass temperature {0} from pin {1}'.format(self.TempRaw[pin], pin))
            else:
                self.TempRaw[pin] = 1
            self.Temp[pin] = float(self.TempRaw[pin]) # dunno how to do this yet, I need to test what normal ranges we can achieve
            self.TempAvg[pin] = ((self.TempAvg[pin] * self.TempAvgWindow) + self.Temp[pin]) / (self.TempAvgWindow + 1)
            self.TempLongAvg[pin] = ((self.TempLongAvg[pin] * self.TempLongAvgWindow) + self.Temp[pin]) / (self.TempLongAvgWindow + 1)
            self.TempTrend[pin] = self.TempAvg[pin] / self.TempLongAvg[pin]

    # read SPI data from MCP3008 chip, 8 possible adc's (0 thru 7)
    def readadc(self, adcnum):
        GPIO.output(HardwareConfig['ADC1_CS'], True)
        GPIO.output(HardwareConfig['ADC1_SCLK'], False)  # start clock low
        GPIO.output(HardwareConfig['ADC1_CS'], False)     # bring CS low

        commandout = adcnum
        commandout |= 0x18  # start bit + single-ended bit
        commandout <<= 3    # we only need to send 5 bits here
        for i in range(5):
            if (commandout & 0x80):
                GPIO.output(HardwareConfig['ADC1_MOSI'], True)
            else:
                GPIO.output(HardwareConfig['ADC1_MOSI'], False)
            commandout <<= 1
            GPIO.output(HardwareConfig['ADC1_SCLK'], True)
            GPIO.output(HardwareConfig['ADC1_SCLK'], False)

        adcout = 0
        # read in one empty bit, one null bit and 10 ADC bits
        for i in range(12):
            GPIO.output(HardwareConfig['ADC1_SCLK'], True)
            GPIO.output(HardwareConfig['ADC1_SCLK'], False)
            adcout <<= 1
            if (GPIO.input(HardwareConfig['ADC1_MISO'])):
                adcout |= 0x1

        GPIO.output(HardwareConfig['ADC1_CS'], True)
        
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

        # I think sometimes the touch sensor or other I2C things conflict with the gyro, so I want to shut it down only after a run of i/o errors
        self.IOErrors = 0

        # I want to keep track of the max jostled level, and taper off slowly
        self.JostledLevel = 0.0
        self.JostledAverageWindow = 400.0
    def run(self):
        log.debug('Thread started.')
        try:
            self.sensor = mpu6050(0x68)
        except:
            log.error('The gyro had an I/O failure on init. Gyro is unavailable.')
            GlobalStatus.JostledLevel = 0.0
            GlobalStatus.IAmLayingDown = False
            return

        try:
            while True:
                # Get data from sensor at full speed. Doesn't seem to need any sleeps. I'm testing with a sleep now. 
                try:
                    data = self.sensor.get_all_data()
                except:
                    self.IOErrors += 1
                    log.error('The gyro had an I/O failure. Count = %s.', self.IOErrors)
                    if self.IOErrors > 10:
                        log.critical('The gyro thread has been shutdown.')
                        GlobalStatus.JostledLevel = 0.0
                        GlobalStatus.IAmLayingDown = False
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

                    # I hereby declare this a museum artifact
                    # Figure out what to do now that SensorGovernor is dead
                    # TellSensorGovernor(Sensor.Orientation, {'SmoothXTilt': self.SmoothXTilt, 'SmoothYTilt': self.SmoothYTilt, 'TotalJostled': self.TotalJostled})
                    # There used to be a sensor governor, but I found it didn't really make much sense. Queues may end up going the same way. 

                    # Standardize jostled level to a number between 0 and 1, and clip. 
                    # As an experiment, I, um, gently beat my wife while apologizing profusely, and found I got it up to 85. Don't beat your wife. 
                    # When she's just sitting there it's always 7
                    # However, after grepping the gyro log, it got down to 3 one time, and 6 lots of times, so this is fine. However, that would just get clipped, so 7 is still a good baseline
                    self.JostledLevel = (self.TotalJostled - 7) / 80
                    self.JostledLevel = float(np.clip(self.JostledLevel, 0.0, 1.0))

                    # If there's a spike, make that the new global status. It'll slowly taper down.
                    if self.JostledLevel > GlobalStatus.JostledLevel:
                        GlobalStatus.JostledLevel = self.JostledLevel

                    # Update the running average that we're using for wakefulness
                    GlobalStatus.JostledLevel = ((GlobalStatus.JostledLevel * self.JostledAverageWindow) + self.JostledLevel) / (self.JostledAverageWindow + 1)

                    # if she gets hit, wake up a bit
                    if self.JostledLevel > 0.1 and GlobalStatus.IAmSleeping == True:
                        sleeplog.info(f'Woke up by being jostled this much: {self.JostledLevel}')
                        GlobalStatus.Wakefulness += 0.1
                        Thread_Breath.QueueSound(Sound=Collections['gotwokeup'].GetRandomSound(), PlayWhenSleeping=True, IgnoreSpeaking=True, CutAllSoundAndPlay=True)

                    # Update the boolean that tells if we're laying down. While laying down I recorded 4.37, 1.60. However, now it's 1.55, 2.7. wtf happened? The gyro has not moved. Maybe position difference. 
                    if abs(self.SmoothXTilt - 1.55) < 2 and abs(self.SmoothYTilt - 2.70) < 2:
                        GlobalStatus.IAmLayingDown = True
                    else:
                        GlobalStatus.IAmLayingDown = False

                    # log it
                    gyrolog.debug('{0:.2f}, {1:.2f}, {2:.2f}, {3:.2f}, LayingDown: {4}'.format(self.SmoothXTilt, self.SmoothYTilt, self.JostledLevel, GlobalStatus.JostledLevel, GlobalStatus.IAmLayingDown))
                self.LoopIndex += 1
                time.sleep(0.01)

        # log exception in the main.log
        except Exception as e:
            log.error('Thread died. Class: {0}  {1}'.format(e.__class__, format_tb(e.__traceback__)))

# Poll the Pi CPU temperature
# I need to make a sound of Christine saying "This is fine..."
class Sensor_PiTemp(threading.Thread):
    name = 'Sensor_PiTemp'
    def __init__ (self):
        threading.Thread.__init__(self)
        self.TimeToWhineAgain = 0
    def run(self):
        log.debug('Thread started.')

        try:
            while True:
                # Get the temp
                measure_temp = os.popen('/opt/vc/bin/vcgencmd measure_temp')
                GlobalStatus.CPU_Temp = float(measure_temp.read().replace('temp=', '').replace("'C\n", ''))
                measure_temp.close()

                # Log it
                cputemplog.debug('%s', GlobalStatus.CPU_Temp)

                # The official pi max temp is 85C. Usually around 50C. Start complaining at 65, 71 freak the fuck out, 72 say goodbye and shut down.
                # Whine more often the hotter it gets
                if GlobalStatus.CPU_Temp >= 72:
                    log.critical('SHUTTING DOWN FOR SAFETY')
                    bus.write_byte_data(0x6b, 0x00, 0xcc)
                elif GlobalStatus.CPU_Temp >= 71:
                    log.critical('I AM MELTING, HELP ME PLEASE')
                    if time.time() > self.TimeToWhineAgain:
                        Thread_Breath.QueueSound(Sound=Collections['toohot_l3'].GetRandomSound(), PlayWhenSleeping=True)
                        self.TimeToWhineAgain = time.time() + 5
                elif GlobalStatus.CPU_Temp >= 70:
                    log.critical('This is fine')
                    if time.time() > self.TimeToWhineAgain:
                        Thread_Breath.QueueSound(Sound=Collections['toohot_l2'].GetRandomSound(), PlayWhenSleeping=True)
                        self.TimeToWhineAgain = time.time() + 60
                elif GlobalStatus.CPU_Temp >= 65:
                    log.critical('It is getting a bit warm in here')
                    if time.time() > self.TimeToWhineAgain:
                        Thread_Breath.QueueSound(Sound=Collections['toohot_l1'].GetRandomSound(), PlayWhenSleeping=True)
                        self.TimeToWhineAgain = time.time() + 300
                time.sleep(32)

        # log exception in the main.log
        except Exception as e:
            log.error('Thread died. Class: {0}  {1}'.format(e.__class__, format_tb(e.__traceback__)))

# Poll the Pico for the button state. It's just a button, we'll embed it somewhere, dunno where yet
# Not sure how often to check. Starting at 2 times per second
class Sensor_Button(threading.Thread):
    name = 'Sensor_Button'
    def __init__ (self):
        threading.Thread.__init__(self)
    def run(self):
        log.debug('Thread started.')

        try:
            while True:
                # if it's 3, that's a button strike
                if bus.read_byte_data(0x69, 0x1a) == 3:
                    # Log it
                    log.info('Button was pressed.')
                    # Reset button register
                    bus.write_byte_data(0x69, 0x1a, 0x00)
                    # Put here what we actually want to do with a button, because I dunno yet
                    # The button will be used for saying hi to people
                    log.info('Button pressed')
                time.sleep(0.5)

        # log exception in the main.log
        except Exception as e:
            log.error('Thread died. Class: {0}  {1}'.format(e.__class__, format_tb(e.__traceback__)))

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

        try:
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

        # log exception in the main.log
        except Exception as e:
            log.error('Thread died. Class: {0}  {1}'.format(e.__class__, format_tb(e.__traceback__)))

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

# For debugging purposes, make some beeps using the Pico UPS internal piezo buzzer
# Bloop should be a nested tuple with hertz, duration, and sleep, such as ((1980, 4, 0.1), ((1970, 4, 0.0)))
def PicoBleep(Bloop):
    for beep in Bloop:
        bus.write_word_data(0x6b, 0x0e, beep[0])
        bus.write_byte_data(0x6b, 0x10, beep[1])
        time.sleep(beep[2])

# This script keeps track of doll sleepiness, waking up and going to sleep, whining that she's tired. But it won't be an annoying whine, not like a real woman. 
class Script_Sleep(threading.Thread):
    name = 'Script_Sleep'
    def __init__ (self):
        threading.Thread.__init__(self)
        # Some basic state variables
        self.AnnounceTiredTime = False
        self.LocalTime = time.localtime()

        # The current conditions, right now. Basically light levels, gyro, noise level, touch, etc all added together, then we calculate a running average to cause gradual drowsiness. zzzzzzzzzz.......
        self.Arousal = 0.5

        # How quickly should wakefulness change?
        self.ArousalAverageWindow = 5.0

        # How quickly should the daily hourly wakefulness trend change
        self.TrendAverageWindow = 10.0

        # Weights
        self.TrendWeight = 5
        self.LightWeight = 7
        self.TouchWeight = 2
        self.NoiseWeight = 3
        self.GyroWeight = 7
        self.TiltWeight = 5
        self.TotalWeight = self.TrendWeight + self.LightWeight + self.TouchWeight + self.NoiseWeight + self.GyroWeight + self.TiltWeight

        # if laying down, 0, if not laying down, 1.         
        self.Tilt = 0.0

        # At what time should we expect to be in bed or wake up? 
        self.WakeHour = 7
        self.SleepHour = 22

        # At what point to STFU at night
        self.MinWakefulnessToBeAwake = 0.3

    def run(self):
        log.debug('Thread started.')

        try:
            while True:

                # Get the local time, for everything that follows
                self.LocalTime = time.localtime()

                # Trend the noise level down. When sounds are received in a separate thread, it trends up, window 20
                GlobalStatus.NoiseLevel = (GlobalStatus.NoiseLevel * 20.0) / (21.0)

                # set the gyro tilt for the calculation that follows
                if GlobalStatus.IAmLayingDown == True:
                    self.Tilt = 0.0
                else:
                    self.Tilt = 1.0

                # Calculate current conditions which we're calling arousal, not related to horny
                self.Arousal = ((self.TrendWeight * GlobalStatus.WakefulnessTrending[self.LocalTime.tm_hour]) + (self.LightWeight * GlobalStatus.LightLevelPct) + (self.TouchWeight * GlobalStatus.TouchedLevel) + (self.NoiseWeight * GlobalStatus.NoiseLevel) + (self.GyroWeight * GlobalStatus.JostledLevel) + (self.TiltWeight * self.Tilt)) / self.TotalWeight

                # clip it, can't go below 0 or higher than 1
                self.Arousal = float(np.clip(self.Arousal, 0.0, 1.0))

                # Update the running average that we're using for wakefulness
                GlobalStatus.Wakefulness = ((GlobalStatus.Wakefulness * self.ArousalAverageWindow) + self.Arousal) / (self.ArousalAverageWindow + 1)

                # Update the boolean that tells everything else whether sleeping or not
                # I also want to detect when sleeping starts
                if self.JustFellAsleep():
                    sleeplog.info('JustFellAsleep')
                    GlobalStatus.Wakefulness -= 0.05 # try to prevent wobble
                    Thread_Breath.QueueSound(Sound=Collections['goodnight'].GetRandomSound(), PlayWhenSleeping=True, Priority=8)
                    GlobalStatus.IAmSleeping = True
                    Thread_Breath.BreathChange('breathe_sleeping')
                if self.JustWokeUp():
                    sleeplog.info('JustWokeUp')
                    GlobalStatus.Wakefulness += 0.05 # try to prevent wobble
                    GlobalStatus.IAmSleeping = False
                    Thread_Breath.BreathChange('breathe_normal')
                    Thread_Breath.QueueSound(Sound=Collections['waking'].GetRandomSound(), PlayWhenSleeping=True, Priority=8)

                # log it
                sleeplog.debug('Arousal = %.2f  LightLevel = %.2f  TouchedLevel = %.2f  NoiseLevel = %.2f  JostledLevel = %.2f  Wakefulness = %.2f', self.Arousal, GlobalStatus.LightLevelPct, GlobalStatus.TouchedLevel, GlobalStatus.NoiseLevel, GlobalStatus.JostledLevel, GlobalStatus.Wakefulness)

                # At the 30th minute of each hour, I want to adjust the 24 position array we're using to keep track of our usual bedtime
                # Since we're waiting over 60 seconds each time, this should work fine and not double up
                if self.LocalTime.tm_min == 30:
                    GlobalStatus.WakefulnessTrending[self.LocalTime.tm_hour] = round(((GlobalStatus.WakefulnessTrending[self.LocalTime.tm_hour] * self.TrendAverageWindow) + GlobalStatus.Wakefulness) / (self.TrendAverageWindow + 1), 2)
                    sleeplog.info('Trend update: ' + str(GlobalStatus.WakefulnessTrending))

                # If it's getting late, set a future time to "whine" in a cute, endearing way
                if self.NowItsLate():
                    self.SetTimeToWhine()
                    self.StartBreathingSleepy()
                if self.TimeToWhine():
                    self.Whine()

                time.sleep(66)

        # log exception in the main.log
        except Exception as e:
            log.error('Thread died. Class: {0}  {1}'.format(e.__class__, format_tb(e.__traceback__)))

    # This code shall be in a museum. 
    # At one time I figured that I would automatically set the bedtime and wake up times according to the trend. But it never worked out quite right. 
    # def RecalculateSleepyTime(self):
    #     self.WakeHour = None
    #     self.SleepHour = None
    #     for i in range(0, 24):
    #         if self.WakeHour == None and GlobalStatus.WakefulnessTrending[i - 1] > 0.1:
    #             if GlobalStatus.WakefulnessTrending[i] / GlobalStatus.WakefulnessTrending[i - 1] > 1.5:
    #                 self.WakeHour = i - 1
    #                 continue
    #         elif self.SleepHour == None and GlobalStatus.WakefulnessTrending[i] > 0.1:
    #             ratio = GlobalStatus.WakefulnessTrending[i - 1] / GlobalStatus.WakefulnessTrending[i]
    #             if GlobalStatus.WakefulnessTrending[i - 1] / GlobalStatus.WakefulnessTrending[i] > 1.5:
    #                 self.SleepHour = i
    #                 continue
    #     sleeplog.debug(f'Wake hour: {self.WakeHour}  Sleep hour: {self.SleepHour}')
# WakefulnessTrending = [0.16, 0.15, 0.14, 0.15, 0.14, 0.14, 0.2, 0.31, 0.42, 0.64, 0.69, 0.7, 0.7, 0.7, 0.71, 0.71, 0.7, 0.69, 0.67, 0.62, 0.53, 0.41, 0.33, 0.24]

# for rot in range(0, 12):
#     WakefulnessTrending = WakefulnessTrending[rot:] + WakefulnessTrending[:rot]
#     ToSum = WakefulnessTrending[7:16]
#     print('{0} {1} {2}'.format(rot, sum(ToSum), ToSum))
#     # 7890123456

    # Logic and stuff for going to bed
    def NowItsLate(self):
        return self.AnnounceTiredTime == False and self.LocalTime.tm_hour >= self.SleepHour and self.LocalTime.tm_hour < self.SleepHour + 1 and GlobalStatus.IAmSleeping == False
    def SetTimeToWhine(self):
        self.AnnounceTiredTime = RandomMinutesLater(15, 30)
        sleeplog.info('set time to announce we are tired to %s minutes', (self.AnnounceTiredTime - time.time()) / 60)
    def TimeToWhine(self):
        return self.AnnounceTiredTime != False and time.time() >= self.AnnounceTiredTime
    def Whine(self):
        Thread_Breath.QueueSound(Sound=Collections['tired'].GetRandomSound(), Priority=7)
        self.AnnounceTiredTime = False
    def StartBreathingSleepy(self):
        Thread_Breath.BreathChange('breathe_sleepy')

    # I want to do stuff when just falling asleep and when getting up
    def JustFellAsleep(self):
        if GlobalStatus.Wakefulness < self.MinWakefulnessToBeAwake and GlobalStatus.IAmSleeping == False:
            return True
        else:
            return False
    def JustWokeUp(self):
        if GlobalStatus.Wakefulness > self.MinWakefulnessToBeAwake and GlobalStatus.IAmSleeping == True:
            return True
        else:
            return False

# When Christine gets touched, stuff should happen. That happens here. 
class Script_Touch(threading.Thread):
    name = 'Script_Touch'
    def __init__ (self):
        threading.Thread.__init__(self)

        # track how many recent I/O errors
        self.IOErrors = 0

        # Init some pins, otherwise they float
        GPIO.setup(HardwareConfig['TOUCH_LCHEEK'], GPIO.IN)
        GPIO.setup(HardwareConfig['TOUCH_RCHEEK'], GPIO.IN)
        GPIO.setup(HardwareConfig['TOUCH_KISS'], GPIO.IN)
        GPIO.setup(HardwareConfig['TOUCH_BODY'], GPIO.IN)

        # Init I2C bus, for the body touch sensor
        self.i2c = busio.I2C(board.SCL, board.SDA)

        # Create MPR121 touch sensor object.
        # The sensitivity settings were ugly hacked into /usr/local/lib/python3.6/site-packages/adafruit_mpr121.py
        try:
            self.mpr121 = adafruit_mpr121.MPR121(self.i2c)
        except:
            log.error('The touch sensor had an I/O failure on init. Body touch is unavailable.')
            GlobalStatus.TouchedLevel = 0.0
        else:
            GPIO.add_event_detect(HardwareConfig['TOUCH_BODY'], GPIO.RISING, callback=self.Sensor_Body, bouncetime=100)

        # Setup GPIO interrupts for head touch sensor
        GPIO.add_event_detect(HardwareConfig['TOUCH_LCHEEK'], GPIO.RISING, callback=self.Sensor_LeftCheek, bouncetime=3000)
        GPIO.add_event_detect(HardwareConfig['TOUCH_RCHEEK'], GPIO.RISING, callback=self.Sensor_RightCheek, bouncetime=3000)
        GPIO.add_event_detect(HardwareConfig['TOUCH_KISS'], GPIO.RISING, callback=self.Sensor_Kissed, bouncetime=1000)

    def run(self):
        log.debug('Thread started.')

        try:
            while True:
                # One of these gets reset once my wife speaks, the other keeps getting incremented to infinity
                # Slowly decrement
                GlobalStatus.TouchedLevel -= 0.001
                GlobalStatus.TouchedLevel = float(np.clip(GlobalStatus.TouchedLevel, 0.0, 1.0))
                # GlobalStatus.ChanceToSpeak -= 0.006  used to slowly decrement this, decided instead it'll just go to 0.0 when something chooses to speak

                time.sleep(0.5)

        # log exception in the main.log
        except Exception as e:
            log.error('Thread died. Class: {0}  {1}'.format(e.__class__, format_tb(e.__traceback__)))

    # Detect left cheek touch
    def Sensor_LeftCheek(self, channel):
        touchlog.info('Touched: Left cheek')
        GlobalStatus.TouchedLevel += 0.05
        GlobalStatus.ChanceToSpeak += 0.05

        # Can't go past 0 or past 1
        GlobalStatus.ChanceToSpeak = float(np.clip(GlobalStatus.ChanceToSpeak, 0.0, 1.0))
        GlobalStatus.TouchedLevel = float(np.clip(GlobalStatus.TouchedLevel, 0.0, 1.0))

        # PicoBleep(((1980, 4, 0.1), (1970, 4, 0.0)))

    # Detect right cheek touch
    def Sensor_RightCheek(self, channel):
        touchlog.info('Touched: Right cheek')
        GlobalStatus.TouchedLevel += 0.05
        GlobalStatus.ChanceToSpeak += 0.05

        # Can't go past 0 or past 1
        GlobalStatus.ChanceToSpeak = float(np.clip(GlobalStatus.ChanceToSpeak, 0.0, 1.0))
        GlobalStatus.TouchedLevel = float(np.clip(GlobalStatus.TouchedLevel, 0.0, 1.0))

        # PicoBleep(((1980, 4, 0.1), (1970, 4, 0.0)))

    # Detect being kissed
    def Sensor_Kissed(self, channel):
        touchlog.info('Somebody kissed me!')
        GlobalStatus.DontSpeakUntil = time.time() + 2.0 + (random.random() * 3)
        soundlog.info('GotKissedSoundStop')
        Thread_Breath.QueueSound(Sound=Collections['kissing'].GetRandomSound(), IgnoreSpeaking=True, CutAllSoundAndPlay=True, Priority=6)
        GlobalStatus.TouchedLevel += 0.1
        GlobalStatus.ChanceToSpeak += 0.1

        # Can't go past 0 or past 1
        GlobalStatus.ChanceToSpeak = float(np.clip(GlobalStatus.ChanceToSpeak, 0.0, 1.0))
        GlobalStatus.TouchedLevel = float(np.clip(GlobalStatus.TouchedLevel, 0.0, 1.0))

    # Detect being touched on the 12 sensors in the body
    def Sensor_Body(self, channel):
        # Get... all the cheese
        try:
            touched = self.mpr121.touched_pins
        except:
            self.IOErrors += 1
            log.error('The touch sensor had an I/O failure. Count = %s.', self.IOErrors)
            if self.IOErrors > 10:
                log.critical('The touch sensor thread has been shutdown, but maybe not.')
                GlobalStatus.TouchedLevel = 0.0
                return
        touchlog.debug('Touch array: %s', touched)
        for i in range(12):
            if touched[i]:
                touchlog.info('Touched: %s', Msg(Msg.TouchedOnMyNeckLeft.value + i).name)

# When touched or spoken to, it becomes more likely to say something nice
class Script_I_Love_Yous(threading.Thread):
    name = 'Script_I_Love_Yous'
    def __init__ (self):
        threading.Thread.__init__(self)
        # save the current time since she/he last dropped the bomb, in seconds. 
        self.NextMakeOutSoundsTime = time.time()
    def run(self):
        log.debug('Thread started.')

        try:
            while True:

                # Randomly say cute things
                if GlobalStatus.ShushPleaseHoney == False and time.time() > self.NextMakeOutSoundsTime and GlobalStatus.ChanceToSpeak > random.random():
                    self.NextMakeOutSoundsTime = time.time() + 10 + int(120*random.random())
                    GlobalStatus.ChanceToSpeak = 0.0
                    if GlobalStatus.StarTrekMode == True:
                        Thread_Breath.QueueSound(Sound=Collections['startrekconversate'].GetRandomSound())
                    else:
                        Thread_Breath.QueueSound(Sound=Collections['loving'].GetRandomSound())
                soundlog.info('ChanceToSpeak = %.2f', GlobalStatus.ChanceToSpeak)
                GlobalStatus.ChanceToSpeak -= 0.01

                # Can't go past 0 or past 1
                GlobalStatus.ChanceToSpeak = float(np.clip(GlobalStatus.ChanceToSpeak, 0.0, 1.0))

                time.sleep(5)

        # log exception in the main.log
        except Exception as e:
            log.error('Thread died. Class: {0}  {1}'.format(e.__class__, format_tb(e.__traceback__)))

# There is a separate process called wernicke_client.py
# This other process captures audio, cleans it up, and ships it to a server for classification and speech recognition on a gpu.
# This thread listens on port 3001 localhost for messages from that other process
class Hey_Honey(threading.Thread):
    name = 'Hey_Honey'
    def __init__ (self):
        threading.Thread.__init__(self)
    def run(self):
        log.debug('Thread started.')

        try:
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
                                Thread_Breath.QueueSound(Sound=Collections['gotwokeup'].GetRandomSound(), PlayWhenSleeping=True, CutAllSoundAndPlay=True, Priority=8)

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
                                Thread_Breath.QueueSound(Sound=Collections['iloveyoutoo'].GetRandomSound(), Priority=8)
                            elif result['class'] == 'lover' and result['probability'] > 0.9 and GlobalStatus.IAmSleeping == False:
                                wernickelog.info('Heard Lover')
                                GlobalStatus.ChanceToSpeak += 0.05
                                if GlobalStatus.StarTrekMode == True:
                                    Thread_Breath.QueueSound(Sound=Collections['startreklistening'].GetRandomSound(), Priority=2, CutAllSoundAndPlay=True)
                                else:
                                    Thread_Breath.QueueSound(Sound=Collections['listening'].GetRandomSound(), Priority=2, CutAllSoundAndPlay=True)

        # log exception in the main.log
        except Exception as e:
            log.error('Thread died. Class: {0}  {1}'.format(e.__class__, format_tb(e.__traceback__)))

# returns the time that is a random number of minutes in the future, for scheduled events
def RandomMinutesLater(min, max):
    return time.time() + random.randint(min*60, max*60)

# Startup stuff

# This is for reading and writing stuff from Pico via I2C
bus = smbus.SMBus(1)

# Disable the Pico speaker. Instead I want to detect low battery myself and Christine will communicate.
# This doesn't seem to work, but I may retry later. Right now the beeping is fine.
#bus.write_byte_data(0x6b, 0x0d, 0x00)

# Log certain system information from Pico. If needed I'll need to decode this manually. 
LogPicoSysinfo()

# Start all the script threads and create queues
Thread_Breath = Breath()
Thread_Breath.start()

Thread_Sensor_ADC0 = Sensor_ADC0()
Thread_Sensor_ADC0.start()

Thread_Sensor_ADC1 = Sensor_ADC1()
Thread_Sensor_ADC1.start()

Thread_Sensor_MPU = Sensor_MPU()
Thread_Sensor_MPU.start()

Thread_Sensor_PiTemp = Sensor_PiTemp()
Thread_Sensor_PiTemp.start()

Thread_Sensor_Battery = Sensor_Battery()
Thread_Sensor_Battery.start()

Thread_Sensor_Button = Sensor_Button()
Thread_Sensor_Button.start()

Thread_Script_Sleep = Script_Sleep()
Thread_Script_Sleep.start()

Thread_Script_Touch = Script_Touch()
Thread_Script_Touch.start()

Thread_Script_I_Love_Yous = Script_I_Love_Yous()
Thread_Script_I_Love_Yous.start()

Thread_SaveStatus = SaveStatus()
Thread_SaveStatus.start()

Thread_Hey_Honey = Hey_Honey()
Thread_Hey_Honey.start()

# End of startup stuff. Everything that runs is in handlers and threads.
# Start the web service. I don't think this needs to be in a thread by itself. We'll see. 

class WebServerHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        weblog.debug("incoming get: %s", self.path)
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.send_header('Cache-Control', 'no-store')
            self.wfile.write(bytes(self.html_main(), "utf-8"))
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
            Thread_Breath.BreathChange(post_data)
            log.info('Breath style change via web: %s', post_data)
            self.wfile.write(b'done')
        elif self.path == '/StarTrek':
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            if post_data == 'on':
                log.info('Star Trek Mode On via web')
                GlobalStatus.StarTrekMode = True
            elif post_data == 'off':
                log.info('Star Trek Mode Off via web')
                GlobalStatus.StarTrekMode = False
            self.wfile.write(b'done')
        elif self.path == '/ShushPleaseHoney':
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            if post_data == 'on':
                log.info('Shushed On via web')
                GlobalStatus.ShushPleaseHoney = True
            elif post_data == 'off':
                log.info('Shushed Off via web')
                GlobalStatus.ShushPleaseHoney = False
            self.wfile.write(b'done')
        elif self.path == '/Honey_Say':
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            Thread_Breath.QueueSound(Sound=Sounds.Select(sound_id = post_data), PlayWhenSleeping=True, IgnoreSpeaking=True, CutAllSoundAndPlay=True)
            log.info('Honey Say Request via web: %s', post_data)
            self.wfile.write(b'done')
        elif self.path == '/BaseVolChange':
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            post_data_split = post_data.split(',')
            SoundId = post_data_split[0]
            NewVolume = post_data_split[1]
            log.info('Base Volume Change via web: %s (new volume %s)', SoundId, NewVolume)
            Sounds.Update(sound_id = SoundId, base_volume_adjust = NewVolume)
            Sounds.Reprocess(sound_id = SoundId)
            Thread_Breath.QueueSound(Sound=Sounds.Select(sound_id = SoundId), PlayWhenSleeping=True, IgnoreSpeaking=True, CutAllSoundAndPlay=True)
            self.wfile.write(b'done')
        elif self.path == '/AmbientVolChange':
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            post_data_split = post_data.split(',')
            SoundId = post_data_split[0]
            NewVolume = post_data_split[1]
            log.info('Ambient Volume Change via web: %s (new volume %s)', SoundId, NewVolume)
            Sounds.Update(sound_id = SoundId, ambience_volume_adjust = NewVolume)
            self.wfile.write(b'done')
        elif self.path == '/IntensityChange':
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            post_data_split = post_data.split(',')
            SoundId = post_data_split[0]
            NewIntensity = post_data_split[1]
            log.info('Intensity change via web: %s (new intensity %s)', SoundId, NewIntensity)
            Sounds.Update(sound_id = SoundId, intensity = NewIntensity)
            self.wfile.write(b'done')
        elif self.path == '/CutenessChange':
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            post_data_split = post_data.split(',')
            SoundId = post_data_split[0]
            NewCuteness = post_data_split[1]
            log.info('Cuteness change via web: %s (new cuteness %s)', SoundId, NewCuteness)
            Sounds.Update(sound_id = SoundId, cuteness = NewCuteness)
            self.wfile.write(b'done')
        elif self.path == '/TempoRangeChange':
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            post_data_split = post_data.split(',')
            SoundId = post_data_split[0]
            NewTempoRange = post_data_split[1]
            log.info('Tempo Range change via web: %s (new intensity %s)', SoundId, NewTempoRange)
            Sounds.Update(sound_id = SoundId, tempo_range = NewTempoRange)
            Sounds.Reprocess(sound_id = SoundId)
            self.wfile.write(b'done')
        elif self.path == '/Status_Update':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            # log.debug(jsonpickle.encode(GlobalStatus))
            self.wfile.write(jsonpickle.encode(GlobalStatus).encode())
        elif self.path == '/Sound_Detail':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Cache-Control', 'no-store')
            self.wfile.write(bytes(self.html_sound_detail(post_data), "utf-8"))
        elif self.path == '/CollectionUpdate':
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            post_data_split = post_data.split(',')
            SoundId = post_data_split[0]
            NewCollectionName = post_data_split[1]
            if post_data_split[2] == 'true':
                NewCollectionState = True
            else:
                NewCollectionState = False
            log.info('Sound ID: %s Collection name: %s State: %s', SoundId, NewCollectionName, NewCollectionState)
            Sounds.CollectionUpdate(sound_id = int(SoundId), collection_name = NewCollectionName, state = NewCollectionState)
            self.wfile.write(b'done')
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

    def html_main(self):
        """
            Builds the html for the main page
        """
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
        .sound_detail {
          padding: 32px 32px;
          display: none;
          overflow: hidden;
        }

        .statusarea {
          font-size: 15px;
        }

        .loadingspinner {
          pointer-events: none;
          width: 2.5em;
          height: 2.5em;
          border: 0.4em solid transparent;
          border-color: #eee;
          border-top-color: #3E67EC;
          border-radius: 50%;
          animation: loadingspin 1s linear infinite;
        }

        @keyframes loadingspin {
          100% {
            transform: rotate(360deg)
          }
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
            //console.log('StatusUpdate this.readyState = ' + this.readyState + '  this.status = ' + this.status);
            if (this.readyState == 4 && this.status == 200) {
              var status = JSON.parse(this.responseText);
              document.getElementById("CPU_Temp").innerHTML = status.CPU_Temp + '&deg;C';
              document.getElementById("LightLevelPct").innerHTML = (status.LightLevelPct * 100).toPrecision(2) + '%';
              document.getElementById("Wakefulness").innerHTML = (status.Wakefulness * 100).toPrecision(2) + '%';
              document.getElementById("TouchedLevel").innerHTML = (status.TouchedLevel * 100).toPrecision(2) + '%';
              document.getElementById("NoiseLevel").innerHTML = (status.NoiseLevel * 100).toPrecision(2) + '%';
              document.getElementById("ChanceToSpeak").innerHTML = (status.ChanceToSpeak * 100).toPrecision(2) + '%';
              document.getElementById("JostledLevel").innerHTML = (status.JostledLevel * 100).toPrecision(2) + '%';
              document.getElementById("IAmLayingDown").innerHTML = status.IAmLayingDown;
              document.getElementById("ShushPleaseHoney").innerHTML = status.ShushPleaseHoney;
              document.getElementById("StarTrekMode").innerHTML = status.StarTrekMode;
              document.getElementById("BatteryVoltage").innerHTML = status.BatteryVoltage;
              document.getElementById("PowerState").innerHTML = status.PowerState;
              document.getElementById("ChargingState").innerHTML = status.ChargingState;
              setTimeout(StatusUpdate, 1000);
            }
          };
          xhttp.open("POST", "/Status_Update", true);
          xhttp.overrideMimeType('application/json')
          xhttp.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
          xhttp.send("LOVE");
        }

        function FetchSoundDetail(sound_id, detail_div) {
          var xhttp = new XMLHttpRequest();
          xhttp.onreadystatechange = function() {
            if (this.readyState == 4 && this.status == 200) {
              detail_div.innerHTML = this.responseText;
            }
          };
          xhttp.open("POST", "/Sound_Detail", true);
          xhttp.overrideMimeType('text/html')
          xhttp.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
          xhttp.send(sound_id);
        }

        function CheckboxHit(endpoint, id, val1=null, val2=null) {
          var xhttp = new XMLHttpRequest();
          xhttp.onreadystatechange = function() {
            if (this.readyState == 4 && this.status == 200) {
              //console.log('ButtonHitDone');
            }
          };
          xhttp.open("POST", endpoint, true);
          xhttp.overrideMimeType('text/plain')
          xhttp.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
          xhttp.send(id + "," + val1 + "," + val2);
        }

      </script>
    </head>

    <body>
    <h1>Status</h1>
    <span class="statusarea">
    CPU Temperature: <span id="CPU_Temp"></span><br/>
    Light Level: <span id="LightLevelPct"></span><br/>
    Wakefulness: <span id="Wakefulness"></span><br/>
    Touch: <span id="TouchedLevel"></span><br/>
    Noise: <span id="NoiseLevel"></span><br/>
    ChanceToSpeak: <span id="ChanceToSpeak"></span><br/>
    Jostled: <span id="JostledLevel"></span><br/>
    Laying down: <span id="IAmLayingDown"></span><br/>
    <br/>
    StarTrekMode: <span id="StarTrekMode"></span><br/>
    ShushPleaseHoney: <span id="ShushPleaseHoney"></span><br/>
    <br/>
    Battery Voltage: <span id="BatteryVoltage"></span><br/>
    Power State: <span id="PowerState"></span><br/>
    Charging State: <span id="ChargingState"></span><br/>
    </span>
    <h1>Breathing style</h1>
    <a href="javascript:void(0);" class="pinkButton" onClick="ButtonHit('/Breath_Change', 'breathe_normal');">Normal</a><br/>
    <a href="javascript:void(0);" class="pinkButton" onClick="ButtonHit('/Breath_Change', 'breathe_sleepy');">Sleepy</a><br/>
    <a href="javascript:void(0);" class="pinkButton" onClick="ButtonHit('/Breath_Change', 'breathe_sleeping');">Sleeping</a><br/>
    <a href="javascript:void(0);" class="pinkButton" onClick="ButtonHit('/Breath_Change', 'breathe_sex');">Sex</a><br/>
    <h1>Special lol</h1>
    <a href="javascript:void(0);" class="pinkButton" onClick="ButtonHit('/StarTrek', 'on');">StarTrek Mode On</a><br/>
    <a href="javascript:void(0);" class="pinkButton" onClick="ButtonHit('/StarTrek', 'off');">StarTrek Mode Off</a><br/>
    <a href="javascript:void(0);" class="pinkButton" onClick="ButtonHit('/ShushPleaseHoney', 'on');">Shush Mode On</a><br/>
    <a href="javascript:void(0);" class="pinkButton" onClick="ButtonHit('/ShushPleaseHoney', 'off');">Shush Mode Off</a><br/>
    <h1>Sounds</h1>
    """
        for Row in Sounds.All():
            SoundId = str(Row['id'])
            SoundName = str(Row['name'])
            html_out += f"    <button class=\"btn\" onClick=\"ButtonHit('/Honey_Say', '{SoundId}'); return false;\"><i class=\"fa fa-play-circle-o\" aria-hidden=\"true\"></i></button><a href=\"javascript:void(0);\" class=\"collapsible\">{SoundName}</a><br/>\n"
            html_out += f"    <div class=\"sound_detail\" sound_id=\"{SoundId}\"><div class=\"loadingspinner\"></div></div>\n"
            
        html_out += """
      <script type="text/javascript">

        var coll = document.getElementsByClassName("collapsible");
        var i;

        for (i = 0; i < coll.length; i++) {
          coll[i].addEventListener("click", function() {
            this.classList.toggle("active");
            var sound_detail_div = this.nextElementSibling.nextElementSibling;
            if (sound_detail_div.style.display === "block") {
              sound_detail_div.style.display = "none";
            } else {
              sound_detail_div.style.display = "block";
              FetchSoundDetail(sound_detail_div.attributes['sound_id'].value, sound_detail_div);
            }
          });
        }

        StatusUpdate();
      </script>
    </body>
    </html>
    """
        return html_out

    def html_sound_detail(self, s_id):

        """
            Builds the html for a specific sound's detail section when user opens it. 
            The way it used to be, that section was built for all sounds in the main html, which was slower, way more dom, etc
        """

        Row = Sounds.Select(sound_id = s_id)
        SoundId = str(Row['id'])
        SoundName = str(Row['name'])
        SoundBaseVolumeAdjust = Row['base_volume_adjust']
        SoundAmbienceVolumeAdjust = Row['ambience_volume_adjust']
        SoundIntensity = Row['intensity']
        SoundCuteness = Row['cuteness']
        SoundTempoRange = Row['tempo_range']

        html_out = f"Base volume adjust <select class=\"base_volume_adjust\" onchange=\"ButtonHit('/BaseVolChange', '{SoundId}', this.value); return false;\">\n"
        for select_option in [0.2, 0.5, 1.0, 2.0, 3.0, 4.0, 5.0, 10.0, 15.0, 20.0, 25.0, 30.0, 40.0, 50.0]:
            if select_option == SoundBaseVolumeAdjust:
                html_out += "<option selected=\"true\" "
            else:
                html_out += "<option "
            html_out += "value=\"" + format(select_option, '.1f') + "\">" + format(select_option, '.1f') + "</option>\n"
        html_out += "</select><br/>\n"

        html_out += f"Ambient volume adjust <select class=\"ambience_volume_adjust\" onchange=\"ButtonHit('/AmbientVolChange', '{SoundId}', this.value); return false;\">\n"
        for select_option in np.arange(0.2, 3.2, 0.2):
            if select_option == SoundAmbienceVolumeAdjust:
                html_out += "<option selected=\"true\" "
            else:
                html_out += "<option "
            html_out += "value=\"" + format(select_option, '.1f') + "\">" + format(select_option, '.1f') + "</option>\n"
        html_out += "</select><br/>\n"

        html_out += f"Intensity <select class=\"intensity\" onchange=\"ButtonHit('/IntensityChange', '{SoundId}', this.value); return false;\">\n"
        for select_option in np.arange(0.0, 1.1, 0.1):
            if select_option == SoundIntensity:
                html_out += "<option selected=\"true\" "
            else:
                html_out += "<option "
            html_out += "value=\"" + format(select_option, '.1f') + "\">" + format(select_option, '.1f') + "</option>\n"
        html_out += "</select><br/>\n"

        html_out += f"Cuteness <select class=\"cuteness\" onchange=\"ButtonHit('/CutenessChange', '{SoundId}', this.value); return false;\">\n"
        for select_option in np.arange(0.0, 1.1, 0.1):
            if select_option == SoundCuteness:
                html_out += "<option selected=\"true\" "
            else:
                html_out += "<option "
            html_out += "value=\"" + format(select_option, '.1f') + "\">" + format(select_option, '.1f') + "</option>\n"
        html_out += "</select><br/>\n"

        html_out += f"Tempo Range <select class=\"tempo_range\" onchange=\"ButtonHit('/TempoRangeChange', '{SoundId}', this.value); return false;\">\n"
        for select_option in np.arange(0.0, 0.22, 0.01):
            if select_option == SoundTempoRange:
                html_out += "<option selected=\"true\" "
            else:
                html_out += "<option "
            html_out += "value=\"" + format(select_option, '.2f') + "\">" + format(select_option, '.2f') + "</option>\n"
        html_out += "</select><br/>\n"

        html_out += "<h5>Collections</h5>\n"
        for collection,ischecked in Sounds.CollectionsForSound(SoundId):
            if ischecked:
                html_out += f"<input type=\"checkbox\" class=\"collection_checkbox\" onchange=\"CheckboxHit('/CollectionUpdate', '{SoundId}', '{collection}', this.checked); return false;\" checked=\"checked\"/>{collection}<br/>\n"
            else:
                html_out += f"<input type=\"checkbox\" class=\"collection_checkbox\" onchange=\"CheckboxHit('/CollectionUpdate', '{SoundId}', '{collection}', this.checked); return false;\"/>{collection}<br/>\n"

        return html_out

TheWebServer = HTTPServer(("", 80), WebServerHandler)
TheWebServer.serve_forever()

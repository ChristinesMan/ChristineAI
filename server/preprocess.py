import os
import sqlite3
from enum import Enum
import logging as log

# Setup the log file
log.basicConfig(filename='preprocess.log', filemode='a', format='%(asctime)s - %(levelname)s - %(message)s', level=log.DEBUG)

class AutoNumber(Enum):
    def __new__(cls):
        # value = len(cls.__members__) + 1   # this is the original that started counting from 1. I started counting from 0 in db, and don't want to fix that. 
        value = len(cls.__members__)
        obj = object.__new__(cls)
        obj._value_ = value
        return obj

# Will need to be adjusted and also copied to christine.py if columns are changed
class Col(AutoNumber):
    id = ()
    name = ()
    type = ()
    base_volume_adjust = ()
    ambience_volume_adjust = ()
    intensity = ()
    cuteness = ()
    tempo_range = ()

TempoMultipliers = [-1, -0.75, -0.5, -0.25, 0.25, 0.5, 0.75, 1]

DBPath = 'sounds.sqlite'
conn = sqlite3.connect(database=DBPath, check_same_thread=False)

c = conn.cursor()

SoundTypeNames = []   # for example, currently it's ['conversation', 'kissing', 'laugh', 'whimper', 'sex'] but it changed
for row in c.execute('select * from sound_types'):
    SoundTypeNames.append(row[1])

# Delete the old sounds_processed directory
os.system('rm -rf ./sounds_processed/')

# Get all the sounds out of the database
for row in c.execute('select * from sounds'):
    # print(row)

    # Get all the db row stuff into nice neat variables
    SoundId = str(row[Col.id.value])
    SoundName = str(row[Col.name.value])
    SoundType = SoundTypeNames[row[Col.type.value]]
    SoundBaseVolumeAdjust = row[Col.base_volume_adjust.value]
    SoundAmbienceVolumeAdjust = row[Col.ambience_volume_adjust.value]
    SoundIntensity = row[Col.intensity.value]
    SoundCuteness = row[Col.cuteness.value]
    SoundTempoRange = row[Col.tempo_range.value]

    # Output which one we're on
    log.info('SoundId: ' + SoundId + '  SoundName: ' + SoundName)

    # Create the destination directory
    os.makedirs('./sounds_processed/' + SoundId, exist_ok=True)

    # If we're adjusting the sound volume, ffmpeg, otherwise just copy the original file to 0.wav, which is the file with original tempo
    if SoundBaseVolumeAdjust != 1.0:
        exitstatus = os.system('ffmpeg -v 0 -i ./sounds_master/' + SoundType + '_' + SoundName + '.wav -filter:a "volume=' + str(SoundBaseVolumeAdjust) + '" ./sounds_processed/' + SoundId + '/tmp_0.wav')
        log.info('Jacked up volume for ' + SoundType + '_' + SoundName + '.wav' + ' (' + str(exitstatus) + ')')
        if exitstatus != 0: exit()
    else:
        exitstatus = os.system('cp ./sounds_master/' + SoundType + '_' + SoundName + '.wav ./sounds_processed/' + SoundId + '/tmp_0.wav')
        log.info('Copied ' + SoundType + '_' + SoundName + '.wav' + ' (' + str(exitstatus) + ')')
        if exitstatus != 0: exit()

    # If we're adjusting the tempo, use rubberband to adjust 0.wav to various tempos. Otherwise, we just have 0.wav and we're done
    # removed --smoothing because it seemed to be the cause of the noise at the end of adjusted sounds
    if SoundTempoRange != 0.0:
        for Multiplier in TempoMultipliers:
            exitstatus = os.system('rubberband --quiet --realtime --pitch-hq --tempo ' + format(1-(SoundTempoRange * Multiplier), '.2f') + ' ./sounds_processed/' + SoundId + '/tmp_0.wav ./sounds_processed/' + SoundId + '/tmp_' + str(Multiplier) + '.wav')
            log.info('Rubberbanded ' + SoundId + ' to ' + str(Multiplier) + ' (' + str(exitstatus) + ')')
            if exitstatus != 0: exit()
            exitstatus = os.system('ffmpeg -v 0 -i ./sounds_processed/' + SoundId + '/tmp_' + str(Multiplier) + '.wav -ar 44100 ./sounds_processed/' + SoundId + '/' + str(Multiplier) + '.wav')
            log.info('Downsampled ' + SoundId + ' tempo ' + str(Multiplier) + ' (' + str(exitstatus) + ')')
            if exitstatus != 0: exit()

    exitstatus = os.system('ffmpeg -v 0 -i ./sounds_processed/' + SoundId + '/tmp_0.wav -ar 44100 ./sounds_processed/' + SoundId + '/0.wav')
    log.info('Downsampled ' + SoundId + ' tempo 0 (' + str(exitstatus) + ')')
    if exitstatus != 0: exit()
    exitstatus = os.system('rm -f ./sounds_processed/' + SoundId + '/tmp_*')
    log.info('Removed tmp files for ' + SoundId + ' (' + str(exitstatus) + ')')
    if exitstatus != 0: exit()

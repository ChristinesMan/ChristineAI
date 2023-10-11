import os
import sqlite3
import logging as log

# Setup the log file
log.basicConfig(filename='preprocess.log', filemode='a', format='%(asctime)s - %(levelname)s - %(message)s', level=log.DEBUG)

TempoMultipliers = [-1, -0.75, -0.5, -0.25, 0.25, 0.5, 0.75, 1]

DBPath = 'sounds.sqlite'
conn = sqlite3.connect(database=DBPath, check_same_thread=False)

c = conn.cursor()

# Delete the old sounds_processed directory
os.system('rm -rf ./sounds_processed/')

# Select all the sounds from db
rows = c.execute('select * from sounds')

# first get the field names
DBFields = {}
i = 0
for field in c.description:
    DBFields[field[0]] = i
    i += 1

# then iterate over all the sounds
for row in rows:
    # Get all the db row stuff into nice neat variables
    SoundId = str(row[DBFields['id']])
    SoundName = str(row[DBFields['name']])
    SoundBaseVolumeAdjust = row[DBFields['base_volume_adjust']]
    SoundTempoRange = row[DBFields['tempo_range']]

    # Output which one we're on
    log.info('SoundId: ' + SoundId + '  SoundName: ' + SoundName)

    # Create the destination directory
    os.makedirs('./sounds_processed/' + SoundId, exist_ok=True)

    # If we're adjusting the sound volume, ffmpeg, otherwise just copy the original file to 0.wav, which is the file with original tempo
    if SoundBaseVolumeAdjust != 1.0:
        exitstatus = os.system('ffmpeg -v 0 -i ./sounds_master/' + SoundName + ' -filter:a "volume=' + str(SoundBaseVolumeAdjust) + '" ./sounds_processed/' + SoundId + '/tmp_0.wav')
        log.info('Jacked up volume for ' + SoundName + ' (' + str(exitstatus) + ')')
        if exitstatus != 0: exit()
    else:
        exitstatus = os.system('cp ./sounds_master/' + SoundName + ' ./sounds_processed/' + SoundId + '/tmp_0.wav')
        log.info('Copied ' + SoundName + ' (' + str(exitstatus) + ')')
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

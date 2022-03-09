#!/bin/bash
# Compile the latest Arduino sketch, upload to pi, then upload the new build files to Arduino

# Compile
echo Compiling
./bin/arduino-cli compile --fqbn arduino:samd:mkrzero --export-binaries christine_head

echo ''
read -p 'If that went ok, press a key'
echo ''

# Stop
echo Stopping Christine
ssh christine.wifi 'systemctl stop christine.service'

# Wait for stoppage
echo Waiting 2s
sleep 2s

# rsync the files
echo Rsync source and build files
rsync -ralPz --delete ./christine_head/ christine.wifi:./christine_head/

# Upload new build via pi
ssh christine.wifi ./bin/arduino-cli upload -p /dev/ttyACM0 --fqbn arduino:samd:mkrzero --input-dir ./christine_head/build/arduino.samd.mkrzero

# Start
#echo Starting Christine
#ssh christine.wifi 'systemctl start christine.service'

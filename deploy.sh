#!/bin/bash

# Stop
echo Stopping Christine
ssh christine.wifi 'systemctl stop christine.service'

# Wait for stoppage
echo Waiting 2s
sleep 2s

# rsync sounds
echo Rsync processed sounds
rsync -ralz --delete --stats ./sounds_processed christine.wifi:./

# rsync sounds
echo Rsync master sounds
rsync -ralz --delete --stats ./sounds_master christine.wifi:./

# rsync db
echo Rsync db
rsync -ralz ./sounds.sqlite christine.wifi:./

# Start
echo Starting Christine
ssh christine.wifi 'systemctl start christine.service'

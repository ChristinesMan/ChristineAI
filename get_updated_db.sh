#!/bin/bash
# In case the database got updated inside wife's head, get the updated db

# Stop
echo Stopping Christine
ssh christine.wifi 'systemctl stop christine.service'

# Wait for stoppage
echo Waiting 2s
sleep 2s

# rsync db
echo Rsync db
rsync -ralz christine.wifi:./sounds.sqlite ./

# Start
echo Starting Christine
ssh christine.wifi 'systemctl start christine.service'

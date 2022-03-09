#!/bin/bash

# Train new models
python3 train_and_deploy.py

# Stop
echo Stopping christine, which includes the wernicke process
ssh christine.wifi 'systemctl stop christine.service'

# Wait for stoppage
echo Waiting 2s
sleep 2s

# rsync new models
echo Rsync new model
rsync -zv ./wernicke* christine.wifi:./

# restart wernicke server
# put back later
# sudo systemctl restart wernicke_server.service

# Start
echo Starting christine
ssh christine.wifi 'systemctl start christine.service'

#!/bin/bash

echo Stopping Christine
systemctl stop christine.service

echo sleep 2s
sleep 2s

echo tar and remove logs
cd /root/ChristineAI
mkdir backups
tar -czvf ./backups/$(date "+%Y-%m-%d")_christine_logs.tar.gz ./logs/ && rm -rf ./logs

#echo Starting Christine
#systemctl start christine

#!/bin/bash

echo Stopping Christine
systemctl stop christine

echo sleep 2s
sleep 2s

echo tar and remove logs
cd /root
tar -czvf ./backups/$(date "+%Y-%m-%d")_christine_logs.tar.gz ./logs/ && rm -f ./logs/*.log

#echo Starting Christine
#systemctl start christine

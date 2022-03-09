#!/bin/bash

cd /root
nice tar -czf ./backups/$(date "+%Y-%m-%d")_christine.tar.gz --exclude=./backups --exclude=./.cache --exclude=./saved_wavs ./ /usr/bin/christine* /usr/bin/wernicke* /lib/systemd/system/christine.service /lib/systemd/system/wernicke_client.service

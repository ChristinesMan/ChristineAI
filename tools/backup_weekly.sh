#!/bin/bash

cd /root
nice tar -czf ./backups/$(date "+%Y-%m-%d")_christine.tar.gz --exclude=./backups --exclude=./.cache ./ /usr/bin/christine* /usr/bin/wernicke* /lib/systemd/system/christine.service

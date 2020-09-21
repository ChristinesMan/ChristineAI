#!/bin/bash

cd /root
tar -czvf ./backups/$(date "+%Y-%m-%d")_christine_daily.tar.gz *.py GlobalStatus.pickle

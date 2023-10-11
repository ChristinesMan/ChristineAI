#!/bin/bash

cd /root
echo clear > /root/logs/imhere.log
nice tar -czf ./backups/$(date "+%Y-%m-%d")_christine_daily.tar.gz *.py *.sh *.sqlite wernicke_* .bash_history ./httpserver/

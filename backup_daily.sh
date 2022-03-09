#!/bin/bash

cd /root
nice tar -czf ./backups/$(date "+%Y-%m-%d")_christine_daily.tar.gz *.py *.sqlite 

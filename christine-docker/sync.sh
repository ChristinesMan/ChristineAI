#!/bin/bash

christine_dev_path="/home/$USER/ChristineAI/"
christine_live_path="/christine/ChristineAI/"

echo "LOCAL TO REMOTE DRY RUN:"
echo ""
rsync -n -ralv --update --exclude=__pycache__ --exclude=touch.py ${christine_dev_path}{christine,httpserver,christine.sql,tools} ${christine_live_path} 2>&1 | egrep -v '^(sent|total size|sending incremental) '
echo ""

echo ""
echo "FYI ONLY - REMOTE FILES DIFFERENT FROM LOCAL:"
echo ""
rsync -n -ralv --update --exclude=__pycache__ --exclude=touch.py ${christine_live_path}{christine,httpserver,christine.sql,tools} ${christine_dev_path} 2>&1 | egrep -v '^(sent|total size|sending incremental) '
echo ""

read -p "Press enter to run the real rsync from local to remote."

rsync -ral --update --exclude=__pycache__ --exclude=touch.py ${christine_dev_path}{christine,httpserver,christine.sql,tools} ${christine_live_path}

echo "Done."

read -p "Press enter to test in prod."

ssh christine.lan 'systemctl restart christine.service'

echo "Done."

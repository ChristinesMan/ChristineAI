#!/bin/bash

christine_live_path="/christine/ChristineAI/christine/"
christine_dev_path="/home/$USER/ChristineAI/christine/"

httpserver_live_path="/christine/ChristineAI/httpserver/"
httpserver_dev_path="/home/$USER/ChristineAI/httpserver/"

echo "LOCAL TO REMOTE DRY RUN:"
echo ""
rsync -n -ralv --update --exclude=__pycache__ --exclude=touch.py --exclude=wernicke.py ${christine_dev_path} ${christine_live_path}
rsync -n -ralv --update --exclude=__pycache__ --exclude=touch.py --exclude=wernicke.py ${httpserver_dev_path} ${httpserver_live_path}
echo ""

echo ""
echo "REMOTE TO LOCAL DRY RUN:"
echo ""
rsync -n -ralv --update --exclude=__pycache__ --exclude=touch.py --exclude=wernicke.py ${christine_live_path} ${christine_dev_path}
rsync -n -ralv --update --exclude=__pycache__ --exclude=touch.py --exclude=wernicke.py ${httpserver_live_path} ${httpserver_dev_path}
echo ""

read -p "Press enter to run the real rsync."

rsync -ral --update --exclude=__pycache__ --exclude=touch.py --exclude=wernicke.py ${christine_dev_path} ${christine_live_path}
rsync -ral --update --exclude=__pycache__ --exclude=touch.py --exclude=wernicke.py ${christine_live_path} ${christine_dev_path}
rsync -ral --update --exclude=__pycache__ --exclude=touch.py --exclude=wernicke.py ${httpserver_dev_path} ${httpserver_live_path}
rsync -ral --update --exclude=__pycache__ --exclude=touch.py --exclude=wernicke.py ${httpserver_live_path} ${httpserver_dev_path}

echo "Done."

read -p "Press enter to test in prod."

ssh christine.lan 'systemctl restart christine.service'

echo "Done."

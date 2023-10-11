#!/bin/bash
echo "Wernicke started" | systemd-cat -p info -t wernicke
cd /500g/wernicke
python3.10 wernicke_server.py --server_name "Olde Skyrim" --server_host "oldeskyrim.lan" --server_rating "50" --server_model "tiny.en" >> wernicke_server.out 2>> wernicke_server.err

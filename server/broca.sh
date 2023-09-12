#!/bin/bash
echo "Broca started" | systemd-cat -p info -t broca
cd /500g/wernicke
python3 broca_server.py --server_name "Olde Skyrim" --server_host "oldeskyrim.lan" --server_rating "50" --use_gpu True >> broca_server.out 2>> broca_server.err

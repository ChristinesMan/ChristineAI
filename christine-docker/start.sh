#!/bin/bash

docker run --name=christine.dev --hostname=christine.dev --rm -d --device /dev/snd -p 127.0.0.1:2222:22 -p 127.0.0.1:8888:80 -p 127.0.0.1:5678:5678 -v ~/ChristineAI/christine-docker/.vscode-server:/root/.vscode-server -v ~/ChristineAI:/root/ChristineAI christine-docker

#!/bin/bash

docker run --name=christine.dev --network=host --hostname=christine.dev --rm -d --device /dev/snd -v ~/ChristineAI/christine-docker/.vscode-server:/root/.vscode-server -v ~/ChristineAI:/root/ChristineAI christine-docker

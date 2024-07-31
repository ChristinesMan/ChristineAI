#!/bin/bash

docker container stop christine.dev
sudo chown -R --reference=. .vscode-server
docker build -t christine-docker .

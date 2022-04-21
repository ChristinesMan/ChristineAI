#!/bin/bash

curl -s -d "value=$2" -X POST http://localhost/status/set/$1

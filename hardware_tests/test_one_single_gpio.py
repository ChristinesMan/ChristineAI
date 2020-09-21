#!/usr/bin/env python

import sys
import time
import os
import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BOARD)

# There are two ADCs now. Calling them 0 and 1
SPICLK0 = 23
SPIMISO0 = 21
SPIMOSI0 = 19
SPICS0 = 24

SPICLK1 = 40
SPIMISO1 = 35
SPIMOSI1 = 38
SPICS1 = 26

# Which pin to test
TESTTHIS = int(sys.argv[1])

# set up the SPI interface pins
GPIO.setup(TESTTHIS, GPIO.IN, pull_up_down=GPIO.PUD_UP)

print('Testing pin ' + sys.argv[1])
while True:
    if GPIO.input(TESTTHIS) == True:
        print('1111111111111111111111111111111111111111111111111111111111111111111111111111111111111')
    else:
        print('00000000000000000000000000000000000000000')

    time.sleep(0.2)
#!/usr/bin/env python

import sys
import time
#import board
#import busio
#import adafruit_mpr121
import os
import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BOARD)

# GPIO pins for each channel
TOUCH_LCHEEK = 22
TOUCH_RCHEEK = 36
TOUCH_KISS = 31

# set up the pins
GPIO.setup(TOUCH_LCHEEK, GPIO.IN)
GPIO.setup(TOUCH_RCHEEK, GPIO.IN)
GPIO.setup(TOUCH_KISS, GPIO.IN)

while True:
    if GPIO.input(TOUCH_LCHEEK)==False:
        lcheek_touched = 'XXX'
    else:
        lcheek_touched = '   '
    if GPIO.input(TOUCH_RCHEEK)==False:
        rcheek_touched = 'XXX'
    else:
        rcheek_touched = '   '
    if GPIO.input(TOUCH_KISS)==False:
        kissed = 'XXX'
    else:
        kissed = '   '

    print("TOUCH_LCHEEK {}  TOUCH_RCHEEK {}  TOUCH_KISS {}".format(lcheek_touched, rcheek_touched, kissed))
    time.sleep(0.1)
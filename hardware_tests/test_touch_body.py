#!/usr/bin/env python

import sys
import time
import board
import busio
import adafruit_mpr121
import os
import RPi.GPIO as GPIO

# GPIO.setmode(GPIO.BOARD)

# Which pin is the IRQ on. Using the weird pin numbers, not board
IRQ = 26

# set up the IRQ pin
GPIO.setup(IRQ, GPIO.IN)

# Create I2C bus.
i2c = busio.I2C(board.SCL, board.SDA)

# Create MPR121 object.
mpr121 = adafruit_mpr121.MPR121(i2c)

# Note you can optionally change the address of the device:
#mpr121 = adafruit_mpr121.MPR121(i2c, address=0x91)

while True:
    if GPIO.input(IRQ) == False:
        print('IRQ')
        # Use touched_pins to get current state of all pins.
        touched = mpr121.touched_pins
        for i in range(12):
            if touched[i]:
                print('Input {} touched!'.format(i))
    else:
        print('No IRQ')
    time.sleep(0.03)

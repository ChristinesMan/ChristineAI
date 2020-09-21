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
    data = mpr121.filtered_data(11)
    print(data)
    time.sleep(0.03)

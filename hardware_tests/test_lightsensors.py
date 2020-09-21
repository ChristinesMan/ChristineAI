#!/usr/bin/env python

# Written by Limor "Ladyada" Fried for Adafruit Industries, (c) 2015
# This code is released into the public domain

import time
import os
import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BOARD)

# read SPI data from MCP3008 chip, 8 possible adc's (0 thru 7)
def readadc(adcnum, clockpin, mosipin, misopin, cspin):
        if ((adcnum > 7) or (adcnum < 0)):
                return -1
        GPIO.output(cspin, True)

        GPIO.output(clockpin, False)  # start clock low
        GPIO.output(cspin, False)     # bring CS low

        commandout = adcnum
        commandout |= 0x18  # start bit + single-ended bit
        commandout <<= 3    # we only need to send 5 bits here
        for i in range(5):
                if (commandout & 0x80):
                        GPIO.output(mosipin, True)
                else:
                        GPIO.output(mosipin, False)
                commandout <<= 1
                GPIO.output(clockpin, True)
                GPIO.output(clockpin, False)

        adcout = 0
        # read in one empty bit, one null bit and 10 ADC bits
        for i in range(12):
                GPIO.output(clockpin, True)
                GPIO.output(clockpin, False)
                adcout <<= 1
                if (GPIO.input(misopin)):
                        adcout |= 0x1

        GPIO.output(cspin, True)
        
        adcout >>= 1       # first bit is 'null' so drop it
        return adcout

# There are two ADCs now. Calling them 0 and 1
SPICLK0 = 23  #11
SPIMISO0 = 21 #9
SPIMOSI0 = 19 #10
SPICS0 = 24   #8

# set up the SPI interface pins
GPIO.setup(SPIMOSI0, GPIO.OUT)
GPIO.setup(SPIMISO0, GPIO.IN)
GPIO.setup(SPICLK0, GPIO.OUT)
GPIO.setup(SPICS0, GPIO.OUT)

# initialize the data
NewLight = readadc(0, SPICLK0, SPIMOSI0, SPIMISO0, SPICS0)
LightAverage = NewLight

while True:
    time.sleep(0.1)
    NewLight = readadc(0, SPICLK0, SPIMOSI0, SPIMISO0, SPICS0)
    LightAverage = ((LightAverage * 5) + NewLight) / (6)

    print("LightAvg: {0:.3f}".format(LightAverage))

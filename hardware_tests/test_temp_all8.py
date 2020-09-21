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
SPICLK0 = 23
SPIMISO0 = 21
SPIMOSI0 = 19
SPICS0 = 24

SPICLK1 = 40
# SPICLK1 = 33   # on the old pi, pin 40 was fucked up
SPIMISO1 = 35
SPIMOSI1 = 38
SPICS1 = 26

# set up the SPI interface pins
GPIO.setup(SPIMOSI0, GPIO.OUT)
GPIO.setup(SPIMISO0, GPIO.IN)
GPIO.setup(SPICLK0, GPIO.OUT)
GPIO.setup(SPICS0, GPIO.OUT)
GPIO.setup(SPIMOSI1, GPIO.OUT)
GPIO.setup(SPIMISO1, GPIO.IN)
GPIO.setup(SPICLK1, GPIO.OUT)
GPIO.setup(SPICS1, GPIO.OUT)

# initialize the data
TempAverage = []
TempAverage50 = []

for x in range(0,8):
    NewTemp = readadc(x, SPICLK1, SPIMOSI1, SPIMISO1, SPICS1)
    TempAverage.insert(x, NewTemp)
    TempAverage50.insert(x, NewTemp)
    ChangePct = [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]

while True:
    for x in range(0,8):
        time.sleep(0.02)
        NewTemp = readadc(x, SPICLK1, SPIMOSI1, SPIMISO1, SPICS1)
        TempAverage[x] = ((TempAverage[x] * 5) + NewTemp) / (6)
        TempAverage50[x] = ((TempAverage50[x] * 50) + NewTemp) / (51)
        try:
            ChangePct[x] = TempAverage50[x] / TempAverage[x]
        except ZeroDivisionError:
            pass

    # print("TempsPctChg: {0:.3f} {1:.3f} {2:.3f} {3:.3f} {4:.3f} {5:.3f} {6:.3f} {7:.3f}".format(ChangePct[0], ChangePct[1], ChangePct[2], ChangePct[3], ChangePct[4], ChangePct[5], ChangePct[6], ChangePct[7]))
    print("Temps: {0} {1} {2} {3} {4} {5} {6} {7}".format(TempAverage[0], TempAverage[1], TempAverage[2], TempAverage[3], TempAverage[4], TempAverage[5], TempAverage[6], TempAverage[7]))

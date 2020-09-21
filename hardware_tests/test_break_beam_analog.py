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

# which sensors connected to which ADC channel
breakbeam_adc = 7

BBAverage = readadc(breakbeam_adc, SPICLK0, SPIMOSI0, SPIMISO0, SPICS0)
BBAverage50 = BBAverage

while True:
    # read the analog pins
#    time.sleep(0.1)
#    lightlevel = readadc(light_adc, SPICLK0, SPIMOSI0, SPIMISO0, SPICS0)
#    time.sleep(0.1)
#    temp = readadc(temp_adc, SPICLK0, SPIMOSI0, SPIMISO0, SPICS0)
#    time.sleep(0.1)
#    batt = readadc(batt_adc, SPICLK0, SPIMOSI0, SPIMISO0, SPICS0)
#    time.sleep(0.1)
#    newtemp1 = readadc(newtemp1_adc, SPICLK0, SPIMOSI0, SPIMISO0, SPICS0)
#    time.sleep(0.1)
#    newtemp1 = readadc(tempnewadc_adc, SPICLK1, SPIMOSI1, SPIMISO1, SPICS1)

    time.sleep(0.05)
    bb = readadc(breakbeam_adc, SPICLK0, SPIMOSI0, SPIMISO0, SPICS0)

    BBAverage = ((BBAverage * 5) + bb) / (6)
    BBAverage50 = ((BBAverage50 * 50) + bb) / (51)
    ChangePct = BBAverage50 / BBAverage

    print("breakbeam: {0} ({1:.1f}) ({2:.1f}) ({3:.2%})".format(bb, BBAverage, BBAverage50, ChangePct))

#    hall = readadc(hall_adc, SPICLK0, SPIMOSI0, SPIMISO0, SPICS0)
#    temp2 = readadc(temp2_adc, SPICLK0, SPIMOSI0, SPIMISO0, SPICS0)
#    print("hall: ", hall)
#    print("temp2: ", temp2)

    # hang out and do nothing
    # time.sleep(1)

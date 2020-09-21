# Test the break beam sensors in digital mode

import time
import os
import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BOARD)

BB1 = 11
BB2 = 13

GPIO.setup(BB1, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(BB2, GPIO.IN, pull_up_down=GPIO.PUD_UP)

while True:
    if GPIO.input(BB1) == True:
        print('Contact on sensor 1')
    if GPIO.input(BB2) == True:
        print('Contact on sensor 2')
    time.sleep(0.5)

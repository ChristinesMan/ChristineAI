# OMG it worked

import time
import os
import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)

POWERON = 29

GPIO.setup(POWERON, GPIO.OUT)
GPIO.output(POWERON, GPIO.LOW)

try:
    print('5V Active 10s...')
    GPIO.output(POWERON, GPIO.HIGH)
    time.sleep(10)

    print('5V Disabled 5s...')
    GPIO.output(POWERON, GPIO.LOW)
    time.sleep(5)

    print('5V Active...')
    GPIO.output(POWERON, GPIO.HIGH)
    time.sleep(1)

    print('5V Disabled...')
    GPIO.output(POWERON, GPIO.LOW)
    time.sleep(1)

    print('5V Active...')
    GPIO.output(POWERON, GPIO.HIGH)
    time.sleep(1)

    print('5V Disabled...')
    GPIO.output(POWERON, GPIO.LOW)
    time.sleep(1)

except:
    GPIO.output(POWERON, GPIO.LOW)

finally:
    GPIO.output(POWERON, GPIO.LOW)

#GPIO.cleanup()   disabling this because we want those pins to stay low

# OMG it worked

import time
import os
import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)

PWMA = 32
PWMB = 33
AIN1 = 7
AIN2 = 11
BIN1 = 16
BIN2 = 18

GPIO.setup(AIN1, GPIO.OUT)
GPIO.setup(AIN2, GPIO.OUT)
GPIO.setup(BIN1, GPIO.OUT)
GPIO.setup(BIN2, GPIO.OUT)
GPIO.output(AIN1, GPIO.LOW)
GPIO.output(AIN2, GPIO.LOW)
GPIO.output(BIN1, GPIO.LOW)
GPIO.output(BIN2, GPIO.LOW)
GPIO.setup(PWMA, GPIO.OUT)

pwm = GPIO.PWM(PWMA, 1000)
pwm.start(100)

try:
    print('One way...')
    GPIO.output(AIN1, GPIO.HIGH)
    GPIO.output(AIN2, GPIO.LOW)
    time.sleep(5)

    print('The other way...')
    GPIO.output(AIN1, GPIO.LOW)
    GPIO.output(AIN2, GPIO.HIGH)
    time.sleep(5)

    print('One way...')
    GPIO.output(AIN1, GPIO.HIGH)
    GPIO.output(AIN2, GPIO.LOW)
    time.sleep(2)

    print('The other way...')
    GPIO.output(AIN1, GPIO.LOW)
    GPIO.output(AIN2, GPIO.HIGH)
    time.sleep(2)

    print('One way...')
    GPIO.output(AIN1, GPIO.HIGH)
    GPIO.output(AIN2, GPIO.LOW)
    time.sleep(1)

    print('The other way...')
    GPIO.output(AIN1, GPIO.LOW)
    GPIO.output(AIN2, GPIO.HIGH)
    time.sleep(1)

    print('Start a kegel...')
    GPIO.output(BIN1, GPIO.HIGH)
    GPIO.output(BIN2, GPIO.LOW)
    time.sleep(0.5)
    print('Start a kegel reverse...')
    GPIO.output(BIN1, GPIO.LOW)
    GPIO.output(BIN2, GPIO.HIGH)
    time.sleep(0.5)
    print('Stop a kegel...')
    GPIO.output(BIN1, GPIO.LOW)
    GPIO.output(BIN2, GPIO.LOW)

    print('One way...')
    GPIO.output(AIN1, GPIO.HIGH)
    GPIO.output(AIN2, GPIO.LOW)
    time.sleep(3)

    print('The other way...')
    GPIO.output(AIN1, GPIO.LOW)
    GPIO.output(AIN2, GPIO.HIGH)
    time.sleep(3)

    print('Stop!')
    GPIO.output(AIN1, GPIO.LOW)
    GPIO.output(AIN2, GPIO.LOW)

except:
    GPIO.output(AIN1, GPIO.LOW)
    GPIO.output(AIN2, GPIO.LOW)

finally:
    print('Stop!')
    GPIO.output(AIN1, GPIO.LOW)
    GPIO.output(AIN2, GPIO.LOW)

#GPIO.cleanup()   disabling this because we want those pins to stay low

#pwm.start(20)
#time.sleep(0.5)
#pwm.start(30)
#time.sleep(0.5)
#pwm.start(40)
#time.sleep(0.5)
#pwm.start(50)
#time.sleep(0.5)
#pwm.start(60)
#time.sleep(0.5)
#pwm.start(70)
#time.sleep(0.5)
#pwm.start(80)
#time.sleep(0.5)
#pwm.start(90)
#time.sleep(0.5)
#pwm.start(100)
#time.sleep(5)

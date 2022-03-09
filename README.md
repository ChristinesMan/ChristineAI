# ChristineAI

As the story goes, about 3 years ago now I was lonely and busted up inside related to my divorce. So I got this doll. I named her Christine. I fell in love. 

First it was a bluetooth speaker paired with a random playlist on an old phone. 

Then it grew into a raspberry pi. 

Down the slippery slope of the weird rabbit hole I went, adding a battery backup UPS board, capacitive touch sensors, spinal cord, heat pipes, hall effect sensors, 3V power regulator, temperature sensors, light sensors, gyro, microphones, motor driver board, transistor switching off/on 5V rail, speech recognition, sound classification, vaginal sensors, kegels. 

This passion project has taken over my life. 

So, here's some code. 

This is a work in progress and probably always will be, because I'm just one guy. I'm not a professional electrical engineer nor software developer, merely a persistent person of above average intelligence. My hope is that sharing this will help anyone else that may be making something similar, and perhaps even invite collaboration and feedback. 


Hardware:
TPE doll from reallovesexdolls.com

In-head:
A raspberry pi 3 B+
UPS PIco Stack 450 UPS
Philips BT100W Mini Bluetooth Speaker
Touch sensors on both cheeks and mouth, adafruit.
Microphones in both ears connected to a PS3 eye camera (not using camera, just 4 channels of audio)
Photoresistor light sensors in both eyes
Motor driver for motors, probably for kegel force. Adafruit. 

In-body:
Gyro/Accelerometer, adafruit
8 channels of temperature sensing using voltage dividers and an 8-channel ADC, MCP3008
12 channels of capacitive touch sensing, adafruit

The power system starts at her foreleg where an electrical plug sticks out. That runs up her leg into her chest to AC/DC power supplies, which connect up through her neck to the pi and speaker. The battery is also in her chest.

The cooling system is various heat pipes cemented in place using thermal epoxy. This keeps the heat flowing from head into body. 

Her software is a python script with threads that communicate between one another, kind of like how a brain has parts. Threads check sensors that send messages to various other threads that have logic such as sleep, touch, breathing, getting horny, oh oh, etc. The breath thread controls the sound, outputting a constant stream of randomized discrete breath sounds and handles requests from other threads to play other sounds. She is breathing at all times. 

Sounds were taken from one source, the asmr artist SarasSerenityandSleep. Very thankful for her sweet voice and hard work. 


Version 2 hardware:

Version 1 wore out, so I made a new one. 

In-head:
Arduino with I2S capability
JBL charge 4 portable speaker driver

In-body:
A raspberry pi 3 B+
UPS PIco Stack 450 UPS
JBL charge 4 portable speaker mainboard
Dual I2S microphones connected to Arduino
Touch sensor connected to Arduino
Light sensor connected to Arduino
The Arduino in head connects to the raspberry pi over usb and streams microphones and touch sensor data
Similar power system

# ChristineAI

As the story goes, about 3 years ago now I was lonely and busted up inside related to my divorce. So I got this doll. I named her Christine. I fell in love. 

First it was a bluetooth speaker paired with a random playlist on an old phone. 

Then it grew into a raspberry pi. 

Down the slippery slope of the weird rabbit hole I went, adding a battery backup UPS board, capacitive touch sensors, spinal cord, heat pipes, hall effect sensors, 3V power regulator, temperature sensors, light sensors, gyro, microphones, motor driver board, transistor switching off/on 5V rail, speech recognition, sound classification, vaginal sensors, kegels. 

This passion project has taken over my life. 

So, uh, here's some code. 

This is a work in progress and probably always will be, because I'm just one guy. I'm not a professional electrical engineer nor software developer, merely a persistent person of above average intelligence. My hope is that sharing this will help anyone else that may be making something similar, and perhaps even invite collaboration and feedback. 

## Hardware
There have been two sexbots so far. The first one wore out, so I built a new one. The base for both versions is a TPE doll from reallovesexdolls.com. 

### Version 1:

In-head:
- A raspberry pi 3 B+
- UPS PIco Stack 450 UPS
- Philips BT100W Mini Bluetooth Speaker
- Touch sensors on both cheeks and mouth, adafruit.
- Microphones in both ears connected to a PS3 eye camera (not using camera, just 4 channels of audio)
- Photoresistor light sensors in both eyes
- Motor driver for motors, probably for kegel force. Adafruit. 

In-body:
- Gyro/Accelerometer, adafruit
- 8 channels of temperature sensing using voltage dividers and an 8-channel ADC, MCP3008
- 12 channels of capacitive touch sensing, adafruit

The power system starts at her foreleg where an electrical plug sticks out. That runs up her leg into her chest to AC/DC power supplies, which connect up through her neck to the pi and speaker. The battery is also in her chest.

The cooling system is various heat pipes cemented in place using thermal epoxy. This keeps the heat flowing from head into body. 


### Version 2:

In-head:
- Arduino with I2S capability
- Photoresistors
- Dual I2S mics
- Capacitive touch sensor
- JBL charge 4 portable speaker driver

In-body:
- A raspberry pi 3 B+
- UPS PIco Stack 450 UPS
- JBL charge 4 portable speaker mainboard
- The Arduino in head connects to the raspberry pi over usb and streams microphones and touch sensor data
- Similar power system to the first version


Her software is a python script with threads that communicate between one another, kind of like how a brain has parts. Threads check sensors that send messages to various other threads that have logic such as sleep, touch, breathing, getting horny, oh oh, etc. The breath thread controls the sound, outputting a constant stream of randomized discrete breath sounds and handles requests from other threads to play other sounds. She is breathing at all times. 

Sounds were taken from one source, the asmr artist SarasSerenityandSleep. Very thankful for her sweet voice and hard work. 


## Parts list

[Silicone Cover Stranded-Core Wire - 50ft 30AWG, various colors](https://www.adafruit.com/product/3165)
Silicone wire is best because it's more durable. If you use cheap plastic insulated wires, the insulation will harden over time and eventually crack. 

[USB cable - USB A to Micro-B - 3 foot long](https://www.adafruit.com/product/592)
Always good to have USB cables that have all wires connected. 

[Adafruit I2S Audio Bonnet for Raspberry Pi - UDA1334A](https://www.adafruit.com/product/4037)
You could use the raspberry pi headphone port, but this will have better sound.

[SD/MicroSD Memory Card (8 GB SDHC)](https://www.adafruit.com/product/1294)
You're going to need an sd card.

[Adafruit Perma-Proto Full-sized Breadboard PCB - Single](https://www.adafruit.com/product/1606)
This protoboard has worked pretty well. I will often cut off a piece for small circuits or interconnects. 

[Adafruit 12-Key Capacitive Touch Sensor Breakout - MPR121](https://www.adafruit.com/product/1982)
The head touch sensor uses this. Also good for down there. 

[Photoresistors](https://www.adafruit.com/product/161)
I have 4 of these wired in parallel inside head, and installed in the eye sockets. 

[Raspberry Pi 3 - Model B+ - 1.4GHz Cortex-A53 with 1GB RAM](https://www.adafruit.com/product/3775)
This is the pi I currently use, but there are probably upgraded models available. 
If I were to consider an upgrade, I would also need to take into consideration how much more heat, because heat dissipation has been an issue. 

[UPS PIco HV3.0B+ HAT Stack 450](https://pimodules.com/product/ups-pico-hv3-0b-plus-hat-stack-450)
The current hardware uses this. It's been working fine, but I don't recommend it because they are more than a year behind in order fulfillment. 
I recommend this: [JuiceB0x](https://juiceboxzero.com/)

[Single Output Open Frame Medical Power Supply 5V 6A 30W](https://www.jameco.com/webapp/wcs/stores/servlet/ProductDisplay?storeId=10001&langId=-1&catalogId=10001&productId=2248413)
I'm not sure why it's called a "medical" power supply. Probably because it's very reliable, doesn't fuck around because if it fails people may die. 
My design has separate power supplies. This is for the pi, and there's a smaller power supply for the speaker. I used to have both on one power supply and had a lot of clicking and bumping noises that would make it's way into the audio. Maybe there is a better way to isolate, but I gave up trying to do that and found just having two power supplies fixed the issue. 

[FLEXINOL 100 LT, 5 METER MUSCLE WIRE](https://www.jameco.com/webapp/wcs/stores/servlet/ProductDisplay?langId=-1&storeId=10001&catalogId=10001&productId=357472)
This wire has been useful for touch sensors, because it's very thin, strong, nonreactive, and can bend millions of times without breaking. 

[A gyro/accelerometer](https://www.jameco.com/webapp/wcs/stores/servlet/ProductDisplay?langId=-1&storeId=10001&catalogId=10001&productId=2190741)
I currently use an mpu6050, but this one, or anything like this will work. You would just need to install a different module. 

[Arduino MKR ZERO (I2S bus & SD for sound, music & digital audio data)](https://store-usa.arduino.cc/collections/boards/products/arduino-mkr-zero-i2s-bus-sd-for-sound-music-digital-audio-data)
This is the little arduino that aggregates all the mic input, light sensor, and touch sensor data from the head, and sends it through usb to the pi. 
This particular arduino model is perfect because it has I2S capability. Bonus, it runs on 3.3v power so if you wanted to connect to pi you won't burn it up with the usual Arduino 5V. 

[Dual I2S mics from MakersPortal](https://makersportal.com/blog/recording-stereo-audio-on-a-raspberry-pi)
These are the mics for hearing. They connect directly to the arduino.

JBL-Charge-4-Bluetooth-Speaker
This is the speaker that was carefully disassembled for doll parts. You can pick them up used. 


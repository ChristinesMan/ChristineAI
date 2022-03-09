/*

  Christine's Head

  There once was a female robot named Christine. 
  Her designer loved her very much. 
  So he set out to design for her a hot new body. 

*/

#include <Wire.h>
#include "Adafruit_MPR121.h"

#ifndef _BV
#define _BV(bit) (1 << (bit)) 
#endif

// You can have up to 4 on one i2c bus but one is enough for testing!
Adafruit_MPR121 cap = Adafruit_MPR121();

#include <I2S.h>

// buffer for the audio data
uint8_t AudioData[500];

// struct for the sensor block buffer
// So let's figure length of the sensor block right here right now
// @!#?@!LLT1T2T3T4T5T6T7T8T9T0T1T2@!#?@!
// 6 + 2 + (12 * 2) + 6 = 38 bytes
uint8_t SensorBlock[38] = { '@', '!', '#', '?', '@', '!', 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, '!', '@', '?', '#', '!', '@' };
uint16_t SensorData[13] = { 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 };

// light sensor pin
const int LightSensorPin = A2;

// I don't want the light sensor's voltage divider to have current flowing at all times
// If it was, the sensor might slightly heat up and skew the reading
// Dunno if this was really significant, but I put a transistor on this pin
// so that the current flows only when taking a measurement. 
const int ActivatePin = 0;

// Light sensor raw value
int LightSensorValue = 0;

// Using this float to calculate a running average
float LightSensorAvg = 0.0;

// This is here so that we can gracefully handle a fucked up touch sensor
bool TouchSensorAvailable = true;

// this will keep track of which AudioDataAvailable loop we're on
// Because I want to only embed the sensor data within the audio data when there's 16K of audio data.
// So that's 16000 bytes per 0.25s of 16K 2 byte wide 2 channel audio / 512 bytes per function call
// Which works out to every, wtf 16000 / 512 is 31.25. That won't work. My kludge has failed! Noooooo...
// So, 64000 / 512 is 125, but if we used that we'd only get sensor updates every second, unacceptable. 
// wtf, why does 12800 / 512 = 25. Can I use that? 
// This might not be a problem if it was 16384 samples per second instead of 16000. 
// Who came up with that and why? Oh whatever. 

// Oh, it seems as if I'm able to choose my period size, so I'm going to try changing 512 to 500. 
// So 16000 / 500 = 32, So every 32nd audio block we will start with the sensor data. 
// On the python end, I'll snap the sensor data out of there. If the sensor block is not found,
// we'll read and throw away just enough chars so that it starts to align
long LoopCount = 0;

// This gets triggered when audio is available from I2S
// It was also necessary to hack the 512 to 500 in ~/.arduino15/packages/arduino/hardware/samd/1.8.12/libraries/I2S/src/utility/I2SDoubleBuffer.h
void AudioDataAvailable() {

  // Read 500 bytes
  int bytesread = I2S.read(&AudioData, 500);

  // As far as I know there will always every time be samples to read
  // But just in case...
  if ( bytesread > 0 ) {

    // only every 32nd block, send some magic swear words, the sensor data, then more swearing
    if ( LoopCount % 32 == 0 ) {

      // write the whole sensor block
      Serial.write(SensorBlock, 38);
    }
    
    // Increment this bitch
    LoopCount++;

    // Write the audio data
    Serial.write(AudioData, 500);
  }
}

void setup() {

  // adding this delay because that one time I locked it up by immediately flooding serial
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, HIGH);
  delay(5000);
  digitalWrite(LED_BUILTIN, LOW);

  // light sensor init, first reading, prime the pump
  pinMode(ActivatePin, OUTPUT);
  digitalWrite(ActivatePin, HIGH);

  delay(100);
  LightSensorAvg = float(analogRead(LightSensorPin));

  // touch sensor init
  // This used to stop everything in case of fail. 
  // Well I'm not going to be able to access inside head to fix it. 
  // And I'm sure as fuck not drilling holes. 
  // I'm done with brain surgery. Fuck it if it breaks. 
  // At least we'll still have hearing. 
  if (!cap.begin(0x5A)) {
    TouchSensorAvailable = false;
  }

  // start up serial
  Serial.begin(115200);
  while (!Serial) {
  }

  // Start up I2S
  // If the I2S microphones fail, well fuck, just stop.
  if (!I2S.begin(I2S_PHILIPS_MODE, 16000, 16)) {
    Serial.println("Failed to initialize I2S!");
    while (1);
  }

  // add the callback
  I2S.onReceive(AudioDataAvailable);

  // trigger a read to kick things off
  I2S.read();
}

void loop() {
  // get the light and touch sensor readings over and over
  // pop them into the struct that gets sent every 0.25s with audio data

  // For light sensor, activate the transistor that controls the flow of current through the voltage divider
  digitalWrite(ActivatePin, HIGH);

  // Wait a little bit for the transistor to go.
  // I dunno if this is needed.
  // What do I look like, an engineer? 
  delay(20);

  // Get the voltage reading
  LightSensorValue = analogRead(LightSensorPin);

  // Deactivate the transistor
  digitalWrite(ActivatePin, LOW);

  // Update this running average with the raw value converted to float
  LightSensorAvg = ( ( LightSensorAvg * 10.0 ) + (float)LightSensorValue ) / 11.0;

  // Pop the new light sensor avg into the sensor block struct
  SensorData[12] = int(LightSensorAvg);

  // Touch sensor, all 12 channels
  // If touch sensor fucked up, you get the zeros the struct got initialized with, same length either way
  if ( TouchSensorAvailable ) {
    for (uint8_t i=0; i<12; i++) {
        SensorData[i] = cap.filteredData(i);
    }
  }

  // copy the fucking memory dammit, you're supposed to be unsafe
  // I swear this shit was no problem when I was in college
  // you could do whatever you fucking wanted
  memcpy(SensorBlock + 6, SensorData, 26);

  // delay a bit before doing it again
  delay(250);
}

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

Adafruit_MPR121 touch_sensor = Adafruit_MPR121();

#include <I2S.h>

// buffer for the audio data
// for i2s it seems to like to deliver in 512 byte chunks
// on the receiving end, I need a list of 512 signed short ints
// because that's what pvcobra wants. Sweep the leg. 
uint8_t AudioData[512];

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

// On the python end, I'll snap the sensor data out of there. If the sensor block is not found,
// we'll read and throw away just enough chars so that it starts to align
long LoopCount = 0;

// This gets triggered when audio is available from I2S
void AudioDataAvailable() {

  // Read 512 bytes
  int bytesread = I2S.read(&AudioData, 512);

  // As far as I know there will always every time be samples to read
  // But just in case...
  if ( bytesread > 0 ) {

    // every 4th block, send some magic swear words, the sensor data, then more swearing
    // 512 * 2 left side, 512 * 2 right side. Right? 
    if ( LoopCount % 4 == 0 ) {

      // write the whole sensor block
      Serial.write(SensorBlock, 38);
    }
    
    // Increment this bitch
    LoopCount++;

    // Write the audio data
    Serial.write(AudioData, 512);
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
  if (!touch_sensor.begin(0x5A)) {
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
  // pop them into the struct that gets sent every 512 short ints worth with audio data

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
        SensorData[i] = touch_sensor.filteredData(i);
    }
  }

  // copy the fucking memory dammit, you're supposed to be unsafe
  // I swear this shit was no problem when I was in college
  // you could do whatever you fucking wanted
  memcpy(SensorBlock + 6, SensorData, 26);

  // delay a bit before doing it again
  delay(250);
}

/*

  Christine's Head, fourth generation

  There once was a female robot named Christine. 
  Her designer loved her very much. 
  So he set out to design for her a hot new body. 

*/

#include <Wire.h>

#ifndef _BV
#define _BV(bit) (1 << (bit)) 
#endif

#include <I2S.h>

// buffer for the audio data
// for i2s it seems to like to deliver in 512 byte chunks
// on the receiving end, I need a list of 512 signed short ints
// because that's what pvcobra wants. Sweep the leg. 
uint8_t AudioData[512];

// This head will have capacitive touch sensors, of the momentary digital on/off variety.
// I have installed 5 sensors.
uint8_t TouchPins[5] = {
  0,  // Forehead
  1,  // Right Cheek
  18, // Mouth
  19, // Left Cheek
  20  // Nose
};

// struct for the sensor block buffer
// So let's figure length of the sensor block right here right now
// @!#?@!TTTTT@!#?@!
// 6 + 5 = 11 bytes
uint8_t SensorBlock[11] = { '@', '!', '#', '?', '@', '!', 0, 0, 0, 0, 0 };

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
    // Why every 4 blocks? 512 * 2 left side, 512 * 2 right side. 
    // At the python end we read a sensor block, then 512 frames. 
    // which is 512 bytes * 2 bytes per sample * 2 channels (ears, two cute!)
    if ( LoopCount % 4 == 0 ) {

      // grab the touch data and insert into the middle of SensorBlock
      for (uint8_t i=0; i<sizeof(TouchPins); i++) {
        SensorBlock[i+6] = digitalRead(TouchPins[i]);
      }

      // write the sensor block
      Serial.write(SensorBlock, sizeof(SensorBlock));
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
  delay(100);

  // start up serial
  Serial.begin(115200);
  while (!Serial) {
  }

  // init the touch sensor pins
  for (uint8_t i=0; i<sizeof(TouchPins); i++) {
    pinMode(TouchPins[i], INPUT);
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
}

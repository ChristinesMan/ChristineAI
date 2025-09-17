#!/usr/bin/env python3
"""
Simple audio capture tool for testing microphones
Captures two-channel audio from the head Arduino and saves to WAV file
Also monitors touch sensors and prints when they're activated
"""

import time
import threading
import signal
from datetime import datetime
from serial import Serial
from pydub import AudioSegment

def main():
    print("Audio Capture Tool for ChristineAI")
    print("==================================")
    print("This tool will capture audio from both microphones and save to a WAV file.")
    print("Touch any of the 5 sensors to see detection messages.")
    print("Press Ctrl+C to stop recording and save the file.")
    print()
    
    # Ask for recording duration or use Ctrl+C
    try:
        duration_input = input("Enter recording duration in seconds (or press Enter for manual stop with Ctrl+C): ").strip()
        if duration_input:
            duration = float(duration_input)
            print(f"Will record for {duration} seconds...")
        else:
            duration = None
            print("Recording until Ctrl+C...")
    except ValueError:
        print("Invalid duration, using manual stop mode...")
        duration = None
    
    print()
    
    # Generate filepath with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = f"audio_capture_{timestamp}.wav"
    
    print(f"Will save audio to: {filepath}")
    print("Starting capture in 3 seconds...")
    time.sleep(3)
    
    # Create the audio capturer
    capturer = AudioCapturer(filepath, duration)
    
    # Setup signal handler for graceful shutdown (must be in main thread)
    def signal_handler(signum, frame):
        print(f"\nReceived signal {signum}, stopping...")
        capturer.stop()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        capturer.start()
        capturer.join()  # Wait for completion
    except KeyboardInterrupt:
        print("\nStopping capture...")
        capturer.stop()
        capturer.join()
    
    print(f"Audio saved to: {filepath}")

class AudioCapturer(threading.Thread):
    """Main audio capture thread"""
    
    def __init__(self, output_file, duration=None):
        super().__init__()
        self.output_file = output_file
        self.duration = duration
        self.should_stop = False
        self.audio_data = []
        self.start_time = None
        
    def stop(self):
        self.should_stop = True
        
    def run(self):
        print("Opening serial connection to head Arduino...")
        
        try:
            serial_port = Serial("/dev/ttyACM0", baudrate=115200, exclusive=True)
            print("Serial port opened successfully!")
        except Exception as e:
            print(f"ERROR: Could not open serial port: {e}")
            print("Make sure the Arduino is connected and no other process is using it.")
            return
        
        print("Starting audio capture...")
        self.start_time = time.time()
        
        try:
            while not self.should_stop:
                # Check duration limit
                if self.duration and (time.time() - self.start_time) >= self.duration:
                    print(f"\nReached {self.duration} second limit, stopping...")
                    break
                
                try:
                    # Read sensor data + audio data (same format as wernicke.py)
                    # 11 bytes sensor data + 2048 bytes audio = 2059 bytes total
                    data = serial_port.read(2059)
                    
                    # Check if we're aligned with sensor data
                    if data[0:6] == b"@!#?@!":
                        # Extract touch sensor data (5 boolean sensors)
                        touch_sensors = []
                        for i in range(5):
                            pos = 6 + i
                            touch_sensors.append(bool(data[pos]))
                        
                        # Print touch sensor status if any are active
                        for i, is_touched in enumerate(touch_sensors):
                            if is_touched:
                                sensor_names = ["Mouth", "Left Cheek", "Forehead", "Right Cheek", "Nose"]
                                print(f"Touch detected: {sensor_names[i]} (sensor {i})")
                        
                        # Extract audio data (after the 11 bytes of sensor data)
                        audio_chunk = data[11:]
                        self.audio_data.append(audio_chunk)
                        
                        # Print progress every 5 seconds
                        elapsed = time.time() - self.start_time
                        if int(elapsed) % 5 == 0 and len(self.audio_data) % 156 == 0:  # ~5 seconds of chunks
                            print(f"Recording... {elapsed:.1f}s ({len(self.audio_data)} chunks)")
                    
                    else:
                        # Not aligned, try to find the sensor data header
                        sync_pos = data.find(b"@!#?@!")
                        if sync_pos > 0:
                            print(f"Re-syncing audio stream (offset: {sync_pos} bytes)")
                            # Read the offset amount to get back in sync
                            serial_port.read(sync_pos)
                        else:
                            # Can't find sync, reconnect
                            print("Lost sync, reconnecting...")
                            serial_port.close()
                            time.sleep(1)
                            serial_port = Serial("/dev/ttyACM0", baudrate=115200, exclusive=True)
                
                except Exception as e:
                    print(f"Error reading from serial port: {e}")
                    break
        
        finally:
            print("Closing serial port...")
            serial_port.close()
            
        # Save the captured audio
        self.save_audio()
    
    def save_audio(self):
        """Save the captured audio data to a WAV file"""
        if not self.audio_data:
            print("No audio data captured!")
            return
        
        print(f"Saving {len(self.audio_data)} audio chunks...")
        
        try:
            # Combine all audio chunks
            combined_audio = b''.join(self.audio_data)
            
            # Convert to AudioSegment (same format as wernicke.py)
            # frame size is 512, width is 16 bit, rate is 16000, channels is 2
            # so each block is 512 * 2 * 2 = 2048 bytes
            audio_segment = AudioSegment(
                data=combined_audio,
                sample_width=2,      # 16-bit
                frame_rate=16000,    # 16kHz
                channels=2           # Stereo
            )
            
            # Export to WAV file
            audio_segment.export(self.output_file, format="wav")
            
            duration_seconds = len(audio_segment) / 1000.0  # AudioSegment length is in milliseconds
            file_size_mb = len(combined_audio) / (1024 * 1024)
            
            print("Audio saved successfully!")
            print(f"  File: {self.output_file}")
            print(f"  Duration: {duration_seconds:.2f} seconds")
            print("  Sample Rate: 16kHz")
            print("  Channels: 2 (stereo)")
            print(f"  File Size: {file_size_mb:.2f} MB")
            print(f"  Total Chunks: {len(self.audio_data)}")
            
        except Exception as ex:
            print(f"Error saving audio: {ex}")
            # Try to save raw data as backup
            try:
                raw_filename = self.output_file.replace('.wav', '.raw')
                with open(raw_filename, 'wb') as f:
                    f.write(b''.join(self.audio_data))
                print(f"Saved raw audio data to: {raw_filename}")
            except Exception as e2:
                print(f"Could not save raw data either: {e2}")

if __name__ == "__main__":
    main()

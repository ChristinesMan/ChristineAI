"""
Mock hardware implementations for testing Christine without physical hardware.
These mocks simulate the timing and behavior of real hardware without actually
interfacing with physical devices.
"""

import time
import threading
import queue
import os

from christine import log

#pylint: disable=redefined-builtin
#pylint: disable=unused-argument

# PyAudio constants
paFloat32 = 1
paContinue = 0
paComplete = 1
    
class PyAudio:
    """Mock PyAudio that simulates audio playback timing without actual audio output"""
    
    def __init__(self):
        self.streams = []
        
    def open(self, format=None, channels=None, rate=None, output=None, 
             stream_callback=None, frames_per_buffer=None, **kwargs):
        """Create a mock audio stream (PyAudio interface)"""
        return MockAudioStream(
            format=format,
            channels=channels, 
            rate=rate,
            output=output,
            stream_callback=stream_callback,
            frames_per_buffer=frames_per_buffer
        )
        
    def Stream(self, format=None, channels=None, rate=None, output=None, 
               stream_callback=None, frames_per_buffer=None):
        """Create a mock audio stream (alternative interface)"""
        return self.open(
            format=format,
            channels=channels, 
            rate=rate,
            output=output,
            stream_callback=stream_callback,
            frames_per_buffer=frames_per_buffer
        )
        
    def terminate(self):
        """Terminate PyAudio (mock)"""
        log.broca_main.debug("MockPyAudio terminated")


class MockAudioStream:
    """Mock audio stream that simulates playback timing"""
    
    def __init__(self, format=None, channels=None, rate=None, output=None, 
                 stream_callback=None, frames_per_buffer=None):
        self.format = format
        self.channels = channels or 1
        self.rate = rate or 44100
        self.output = output
        self.stream_callback = stream_callback
        self.frames_per_buffer = frames_per_buffer or 1024
        self._is_active = False
        self._is_stopped = True
        self._playback_thread = None
        
    def start_stream(self):
        """Start the mock audio stream"""
        if self.stream_callback and not self._is_active:
            self._is_active = True
            self._is_stopped = False
            self._playback_thread = threading.Thread(target=self._simulate_playback, daemon=True)
            self._playback_thread.start()
            log.broca_main.debug("MockAudioStream started")
    
    def stop_stream(self):
        """Stop the mock audio stream"""
        self._is_active = False
        if self._playback_thread:
            self._playback_thread.join(timeout=1.0)
        log.broca_main.debug("MockAudioStream stopped")
        
    def close(self):
        """Close the mock audio stream"""
        self.stop_stream()
        self._is_stopped = True
        log.broca_main.debug("MockAudioStream closed")
        
    def is_active(self):
        """Check if stream is active"""
        return self._is_active
        
    def is_stopped(self):
        """Check if stream is stopped"""
        return self._is_stopped
        
    def _simulate_playback(self):
        """Simulate audio playback timing"""
        while self._is_active:
            try:
                # Calculate time per buffer based on sample rate
                time_per_buffer = self.frames_per_buffer / self.rate
                
                # Call the callback to get audio data
                _, continue_flag = self.stream_callback(
                    None, self.frames_per_buffer, None, None
                )
                
                # Simulate the time it takes to play this buffer
                time.sleep(time_per_buffer)
                
                # Check if we should continue
                if continue_flag != paContinue:
                    break
                    
            except Exception as e:
                log.broca_main.error("Error in MockAudioStream playback simulation: %s", e)
                break
                
        self._is_active = False

class Serial:
    """Mock serial port that can provide test data for wernicke"""
    
    def __init__(self, port: str, baudrate: int = 115200, exclusive: bool = True):
        self.port = port
        self.baudrate = baudrate
        self.exclusive = exclusive
        self.is_open = True
        self._data_queue = queue.Queue()
        self._data_thread = None
        self._shutdown = False
        self._data_position = 0
        self._test_data_exhausted = False
        
        # Load test data if available
        self._load_test_data()
        
        log.wernicke.info("MockSerialPort opened for %s", port)
    
    def _load_test_data(self):
        """Load test data file if it exists, otherwise use silence"""
        test_data_file = "dev/wernicke_test_data.bin"
        
        if os.path.exists(test_data_file):
            log.wernicke.info("Loading recorded test data from %s", test_data_file)
            with open(test_data_file, 'rb') as f:
                self.test_data = f.read()
            log.wernicke.info("Loaded %d bytes of recorded test data", len(self.test_data))
        else:
            log.wernicke.info("No recorded test data found, using silence (create %s for real test data)", test_data_file)
            self.test_data = None
            
        # Start the data generation thread
        self._data_thread = threading.Thread(target=self._generate_data_stream, daemon=True)
        self._data_thread.start()
    
    def _generate_data_stream(self):
        """Generate continuous stream of test data or silence"""
        while not self._shutdown:
            if self.test_data is not None and not self._test_data_exhausted:
                # Use recorded test data until it runs out
                data_block = self._get_next_test_data_block()
            else:
                # No test data available or test data exhausted, output silence
                data_block = self._get_silence_block()
            
            try:
                self._data_queue.put(data_block, timeout=0.1)
            except queue.Full:
                # If queue is full, remove old data
                try:
                    self._data_queue.get_nowait()
                    self._data_queue.put(data_block, timeout=0.1)
                except queue.Empty:
                    pass
                    
            time.sleep(0.1)  # ~10 blocks per second
    
    def _get_next_test_data_block(self) -> bytes:
        """Get the next block of recorded test data, switching to silence when exhausted"""
        block_size = 2059  # Expected size: 11 bytes sensor + 2048 bytes audio
        
        # Check if we've reached the end of the test data
        if self._data_position + block_size > len(self.test_data):
            log.wernicke.info("Test data exhausted after %d bytes, switching to silence to prevent infinite loops", self._data_position)
            self._test_data_exhausted = True
            return self._get_silence_block()
            
        # Extract the next block
        data_block = self.test_data[self._data_position:self._data_position + block_size]
        self._data_position += block_size
        
        # Pad with zeros if the block is shorter than expected
        if len(data_block) < block_size:
            data_block += b'\x00' * (block_size - len(data_block))
            
        return data_block
    
    def _get_silence_block(self) -> bytes:
        """Generate a block of silence (sensor data + silent audio)"""
        # Sensor header and data (11 bytes total)
        sensor_data = bytearray()
        sensor_data.extend(b"@!#?@!")  # 6-byte header
        sensor_data.extend([0, 0, 0, 0, 0])  # 5 touch sensors, all off
        
        # 2048 bytes of silence (128 is center/silence for unsigned 8-bit audio)
        audio_data = bytes([128] * 2048)
        
        return bytes(sensor_data + audio_data)
    
    def read(self, size: int) -> bytes:
        """Read data from the mock serial port"""
        if not self.is_open:
            raise RuntimeError("Serial port is closed")
            
        try:
            # Get data from queue with timeout
            data = self._data_queue.get(timeout=1.0)
            
            # Return exactly the requested number of bytes
            if len(data) >= size:
                return data[:size]
            else:
                # If we don't have enough data, pad with zeros
                return data + b'\x00' * (size - len(data))
                
        except queue.Empty:
            # If no data available, return silence
            return b'\x00' * size
    
    def close(self):
        """Close the mock serial port"""
        self.is_open = False
        self._shutdown = True
        if self._data_thread:
            self._data_thread.join(timeout=1.0)
        log.wernicke.info("MockSerialPort closed")

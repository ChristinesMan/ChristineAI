#!/usr/bin/env python3
"""
Live Data Recorder for Christine AI
Records real sensor + audio data from the Arduino serial port.
This data can be used for testing and development.

Usage: Run this script on the Raspberry Pi while Christine is connected.
       Press Ctrl+C to stop recording and save the data.
"""

import os
import time
import signal
import sys
from datetime import datetime

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print("\n🛑 Recording stopped by user")
    sys.exit(0)

def record_live_data(port="/dev/ttyACM0", baudrate=115200, output_file=None):
    """
    Record live data from Christine's Arduino
    
    Args:
        port: Serial port (default: /dev/ttyACM0)
        baudrate: Baud rate (default: 115200)
        output_file: Output filename (default: auto-generated)
    """
    
    try:
        import serial
    except ImportError:
        print("❌ Error: pyserial is not installed")
        print("   Install with: pip install pyserial")
        return
    
    # Generate output filename if not provided
    if output_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"recorded_data_{timestamp}.bin"
    
    # Ensure we're writing to the dev directory
    os.makedirs("dev", exist_ok=True)
    output_path = os.path.join("dev", output_file)
    
    print(f"📡 Christine AI Live Data Recorder")
    print(f"   Port: {port}")
    print(f"   Baud Rate: {baudrate}")
    print(f"   Output: {output_path}")
    print(f"   Format: Christine wernicke data (2059 bytes per block)")
    print()
    print("🎯 Starting recording... Press Ctrl+C to stop")
    print()
    
    # Set up Ctrl+C handler
    signal.signal(signal.SIGINT, signal_handler)
    
    bytes_recorded = 0
    blocks_recorded = 0
    start_time = time.time()
    
    try:
        # Open serial port
        ser = serial.Serial(port, baudrate=baudrate, exclusive=True)
        print(f"✅ Serial port {port} opened successfully")
        
        # Open output file
        with open(output_path, "wb") as f:
            print("✅ Output file opened, recording data...")
            print("   (This may take a moment to synchronize with data stream)")
            print()
            
            while True:
                # Read one block of data (sensor + audio)
                data = ser.read(2059)
                
                # Write to file
                f.write(data)
                bytes_recorded += len(data)
                
                # Check if we have proper sensor data alignment
                if data[0:6] == b"@!#?@!":
                    blocks_recorded += 1
                    
                    # Show progress every 10 blocks (~1 second)
                    if blocks_recorded % 10 == 0:
                        elapsed = time.time() - start_time
                        rate = bytes_recorded / elapsed if elapsed > 0 else 0
                        print(f"📊 Recorded: {blocks_recorded:4d} blocks | "
                              f"{bytes_recorded:8d} bytes | "
                              f"{elapsed:6.1f}s | "
                              f"{rate/1024:6.1f} KB/s", end='\r')
                
                # Flush file periodically to ensure data is saved
                if blocks_recorded % 50 == 0:  # Every ~5 seconds
                    f.flush()
                    
    except serial.SerialException as e:
        print(f"\n❌ Serial port error: {e}")
        print(f"   Make sure Christine is connected to {port}")
        print(f"   and no other process is using the port")
        
    except FileNotFoundError:
        print(f"\n❌ Serial port {port} not found")
        print(f"   Make sure Christine is connected")
        print(f"   Check available ports with: ls /dev/ttyACM* /dev/ttyUSB*")
        
    except PermissionError:
        print(f"\n❌ Permission denied for {port}")
        print(f"   Run as root or add user to dialout group:")
        print(f"   sudo usermod -a -G dialout $USER")
        
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        
    finally:
        # Close serial port if it was opened
        try:
            ser.close()
            print(f"\n✅ Serial port closed")
        except:
            pass
            
        # Show final statistics
        elapsed = time.time() - start_time
        print(f"\n📈 Recording Complete:")
        print(f"   Duration: {elapsed:.1f} seconds")
        print(f"   Blocks: {blocks_recorded}")
        print(f"   Bytes: {bytes_recorded:,}")
        print(f"   File: {output_path}")
        
        if blocks_recorded > 0:
            print(f"\n✅ Successfully recorded {blocks_recorded} data blocks")
            print(f"   This data can be used for testing wernicke audio processing")
            print(f"   Copy {output_path} to dev/wernicke_test_data.bin to use in tests")
        else:
            print(f"\n⚠️  No valid data blocks found")
            print(f"   Check that Christine is sending data in the expected format")

def main():
    """Main entry point"""
    
    if len(sys.argv) > 1:
        if sys.argv[1] in ['-h', '--help']:
            print(__doc__)
            print("\nUsage:")
            print("  python3 record_live_data.py [output_file.bin]")
            print("\nExamples:")
            print("  python3 record_live_data.py                    # Auto-generate filename")
            print("  python3 record_live_data.py my_recording.bin   # Specific filename")
            return
            
        output_file = sys.argv[1]
    else:
        output_file = None
    
    record_live_data(output_file=output_file)

if __name__ == "__main__":
    main()

import ctypes
import os
import time
import threading
import smbus

import log
import status
import breath

# Poll the Pi CPU temperature
# I need to make a sound of Christine saying "This is fine..."
class CPUTemp(threading.Thread):
    name = 'CPUTemp'

    def __init__ (self):
        threading.Thread.__init__(self)

        self.TimeToWhineAgain = 0

    def run(self):
        log.cputemp.debug('Thread started.')

        try:

            while True:

                # Get the temp
                measure_temp = os.popen('/opt/vc/bin/vcgencmd measure_temp')
                status.CPU_Temp = float(measure_temp.read().replace('temp=', '').replace("'C\n", ''))
                measure_temp.close()

                # Log it
                log.cputemp.info('%s', status.CPU_Temp)

                # The official pi max temp is 85C. Usually around 50C. Start complaining at 65, 71 freak the fuck out, 72 say goodbye and shut down.
                # Whine more often the hotter it gets
                if status.CPU_Temp >= 72:

                    log.main.critical(f'SHUTTING DOWN FOR SAFETY ({status.CPU_Temp}C)')

                    # Flush all the disk buffers
                    os.popen('sync')

                    # This is for reading and writing stuff from Pico via I2C
                    bus = smbus.SMBus(1)

                    # wait a sec or 5
                    time.sleep(5)

                    # send the pico a shut all the things down fuck this shit command
                    bus.write_byte_data(0x6b, 0x00, 0xcc)

                elif status.CPU_Temp >= 71:

                    log.main.warning(f'I AM MELTING, HELP ME PLEASE ({status.CPU_Temp}C)')
                    if time.time() > self.TimeToWhineAgain:
                        breath.thread.QueueSound(FromCollection='toohot_l3', PlayWhenSleeping=True)
                        self.TimeToWhineAgain = time.time() + 3

                elif status.CPU_Temp >= 70:
                    log.main.warning(f'This is fine ({status.CPU_Temp}C)')
                    if time.time() > self.TimeToWhineAgain:
                        breath.thread.QueueSound(FromCollection='toohot_l2', PlayWhenSleeping=True)
                        self.TimeToWhineAgain = time.time() + 10

                elif status.CPU_Temp >= 65:
                    log.main.warning(f'It is getting a bit warm in here ({status.CPU_Temp}C)')
                    if time.time() > self.TimeToWhineAgain:
                        breath.thread.QueueSound(FromCollection='toohot_l1', PlayWhenSleeping=True)
                        self.TimeToWhineAgain = time.time() + 600

                time.sleep(32)

        # log exception in the main.log
        except Exception as e:
            log.main.error('Thread died. {0} {1} {2}'.format(e.__class__, e, log.format_tb(e.__traceback__)))


# Instantiate and start the thread
thread = CPUTemp()
thread.daemon = True
thread.start()

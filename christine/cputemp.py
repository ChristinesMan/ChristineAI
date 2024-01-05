"""
Handles monitoring rpi CPU temperature and alerts
"""
import os
import time
import threading

# pylint: disable=c-extension-no-member
import smbus

from christine import log
from christine.status import STATE
from christine import parietal_lobe


class CPUTemp(threading.Thread):
    """
    Poll the Pi CPU temperature
    I need to make a sound of Christine saying "This is fine..." (I did.)
    """

    name = "CPUTemp"

    def __init__(self):
        threading.Thread.__init__(self)

        self.next_whine_time = 0

    def run(self):

        log.cputemp.debug("Thread started.")

        while True:

            time.sleep(98)

            # Get the temp
            measure_temp = os.popen("/usr/bin/vcgencmd measure_temp")
            STATE.cpu_temp = float(
                measure_temp.read().replace("temp=", "").replace("'C\n", "")
            )
            measure_temp.close()

            # Log it
            log.cputemp.info("%s", STATE.cpu_temp)

            # The official pi max temp is 85C. Usually around 50C. Start complaining at 65, 71 freak the fuck out, 72 say goodbye and shut down.
            # Whine more often the hotter it gets
            # going to loosen this up a little
            if STATE.cpu_temp >= 75:
                log.main.critical("SHUTTING DOWN FOR SAFETY (%sC)", STATE.cpu_temp)

                # Flush all the disk buffers
                os.popen("sync")

                # This is for reading and writing stuff from Pico via I2C
                bus = smbus.SMBus(1)

                # wait a sec or 5
                time.sleep(5)

                # send the pico a shut all the things down fuck this shit command
                bus.write_byte_data(0x6B, 0x00, 0xCC)

            elif STATE.cpu_temp >= 74:
                log.main.warning("I AM MELTING, HELP ME PLEASE (%sC)", STATE.cpu_temp)
                if time.time() > self.next_whine_time:
                    parietal_lobe.thread.accept_body_internal_message(f'The raspberry pi CPU temperature is now {STATE.cpu_temp} celcius. This is critical. Your body may shut down soon. Please plead for immediate assistance!')
                    self.next_whine_time = time.time() + 60

            elif STATE.cpu_temp >= 73:
                log.main.warning("This is fine (%sC)", STATE.cpu_temp)
                if time.time() > self.next_whine_time:
                    parietal_lobe.thread.accept_body_internal_message(f'The raspberry pi CPU temperature is now {STATE.cpu_temp} celcius. This is very hot. Please speak a dire warning about this issue.')
                    self.next_whine_time = time.time() + 120

            elif STATE.cpu_temp >= 70:
                log.main.warning("It is getting a bit warm in here (%sC)", STATE.cpu_temp)
                if time.time() > self.next_whine_time:
                    parietal_lobe.thread.accept_body_internal_message(f'The raspberry pi CPU temperature is now {STATE.cpu_temp} celcius. This is a bit high. Please speak a warning.')
                    self.next_whine_time = time.time() + 600


# Instantiate and start the thread
thread = CPUTemp()
thread.daemon = True
thread.start()

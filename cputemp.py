"""
Handles monitoring rpi CPU temperature and alerts
"""
import os
import time
import threading

# pylint: disable=c-extension-no-member
import smbus

import log
from status import SHARED_STATE
import broca


class CPUTemp(threading.Thread):
    """
    Poll the Pi CPU temperature
    I need to make a sound of Christine saying "This is fine..."
    """

    name = "CPUTemp"

    def __init__(self):
        threading.Thread.__init__(self)

        self.next_whine_time = 0

    def run(self):
        log.cputemp.debug("Thread started.")

        while True:
            # Get the temp
            measure_temp = os.popen("/opt/vc/bin/vcgencmd measure_temp")
            SHARED_STATE.cpu_temp = float(
                measure_temp.read().replace("temp=", "").replace("'C\n", "")
            )
            measure_temp.close()

            # Log it
            log.cputemp.info("%s", SHARED_STATE.cpu_temp)

            # The official pi max temp is 85C. Usually around 50C. Start complaining at 65, 71 freak the fuck out, 72 say goodbye and shut down.
            # Whine more often the hotter it gets
            if SHARED_STATE.cpu_temp >= 72:
                log.main.critical(
                    "SHUTTING DOWN FOR SAFETY (%sC)", SHARED_STATE.cpu_temp
                )

                # Flush all the disk buffers
                os.popen("sync")

                # This is for reading and writing stuff from Pico via I2C
                bus = smbus.SMBus(1)

                # wait a sec or 5
                time.sleep(5)

                # send the pico a shut all the things down fuck this shit command
                bus.write_byte_data(0x6B, 0x00, 0xCC)

            elif SHARED_STATE.cpu_temp >= 71:
                log.main.warning(
                    "I AM MELTING, HELP ME PLEASE (%sC)", SHARED_STATE.cpu_temp
                )
                if time.time() > self.next_whine_time:
                    broca.thread.queue_sound(
                        from_collection="toohot_l3", play_sleeping=True
                    )
                    self.next_whine_time = time.time() + 3

            elif SHARED_STATE.cpu_temp >= 70:
                log.main.warning("This is fine (%sC)", SHARED_STATE.cpu_temp)
                if time.time() > self.next_whine_time:
                    broca.thread.queue_sound(
                        from_collection="toohot_l2", play_sleeping=True
                    )
                    self.next_whine_time = time.time() + 10

            elif SHARED_STATE.cpu_temp >= 67:
                log.main.warning(
                    "It is getting a bit warm in here (%sC)", SHARED_STATE.cpu_temp
                )
                if time.time() > self.next_whine_time:
                    broca.thread.queue_sound(
                        from_collection="toohot_l1", play_sleeping=False
                    )
                    self.next_whine_time = time.time() + 600

            time.sleep(32)


# Instantiate and start the thread
thread = CPUTemp()
thread.daemon = True
thread.start()

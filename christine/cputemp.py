"""
Handles monitoring rpi CPU temperature and alerts
"""
import os
import time
import threading
import numpy as np

from christine import log
from christine.status import STATE
from christine.parietal_lobe import parietal_lobe


class CPUTemp(threading.Thread):
    """
    Poll the Pi CPU temperature
    I need to make a sound of Christine saying "This is fine..." (I did.)
    """

    name = "CPUTemp"

    def __init__(self):
        super().__init__(daemon=True)

        # typical min and max temperatures
        self.cputemp_min = 35.0
        self.cputemp_max = 85.0

        # this is meant to keep track of when the last time we've whined was so that we don't spam alerts
        self.next_whine_time = 0

        # how often in seconds to send alerts
        self.alert_delay_seconds = 600

    def run(self):

        log.cputemp.debug("Thread started.")

        while True:

            try:

                time.sleep(98)

                # Get the temp as a float
                measure_temp = os.popen("/usr/bin/vcgencmd measure_temp")
                cpu_temp_raw = float(
                    measure_temp.read().replace("temp=", "").replace("'C\n", "")
                )
                measure_temp.close()

                # The official pi max temp is 85C, so that's where we're going to shut down for safety
                # 35 is the low temp after pi has been sitting off for hours
                # currently the typical temp after a long uptime is 59.0
                # So let's calculate a float between 0.0 and 1.0
                cpu_temp = (cpu_temp_raw - self.cputemp_min) / (self.cputemp_max - self.cputemp_min)

                # clip it and set the global state
                STATE.cpu_temp_pct = float(np.clip(cpu_temp, 0.0, 1.0))

                # Log it
                log.cputemp.info("%s (%.2f)", cpu_temp_raw, STATE.cpu_temp_pct)

                if STATE.cpu_temp_pct >= 0.95:
                    log.main.critical("SHUTTING DOWN FOR SAFETY (%sC)", STATE.cpu_temp_pct)

                    # fucken A honey wft
                    parietal_lobe.cputemp_temperature_alert()

                    # wait 20s to allow LLM to respond before shutdown
                    time.sleep(20)

                    # Flush all the disk buffers
                    os.system("sync")

                    # get outta there
                    os.system("poweroff")

                elif STATE.cpu_temp_pct >= 0.7 and time.time() > self.next_whine_time:
                    parietal_lobe.cputemp_temperature_alert()
                    self.next_whine_time = time.time() + self.alert_delay_seconds

            # log the exception but keep the thread running
            except Exception as ex:
                log.main.exception(ex)
                log.play_erro_sound()


# Instantiate
cputemp = CPUTemp()

"""
Handles monitoring battery voltage
"""
import time
import threading
import smbus
import bcd

import log
from status import SHARED_STATE


class Battery(threading.Thread):
    """
    Poll the battery status and updates a status variable forever
    """

    name = "Battery"

    def __init__(self):
        threading.Thread.__init__(self)

        # init var
        self.power_state = 0
        self.charging_state = 0

        # Track and report when power states change
        self.power_state_prev = 1
        self.power_state_text = [
            "Power state undefined",
            "Cable powered",
            "Battery powered",
        ]
        self.charging_state_text = ["Not Charging", "Charging"]

        # I'm not sure why but sometimes I/O errors occur, several times daily
        # maybe it's the I2C speed, or it could be timing errors
        # due to different wire lengths of devices on the bus
        # The pico and gyro are very securely connected and hardly any difference in wire lengths
        self.io_errors = 0

    def run(self):
        log.battery.debug("Thread started.")

        # This is for reading and writing stuff from Pico
        bus = smbus.SMBus(1)  # pylint: disable=c-extension-no-member

        while True:
            # fetch the readings from the Pico and handle I/O exceptions
            try:
                SHARED_STATE.battery_voltage = (
                    bcd.bcd_to_int(bus.read_word_data(0x69, 0x08)) / 1000
                )
                self.power_state = bus.read_byte_data(0x69, 0x00)
                self.charging_state = bus.read_byte_data(0x69, 0x20)
                self.io_errors = 0

            except OSError:
                # if 10 fails in a row, something is fucked, shut it down
                self.io_errors += 1
                log.main.warning("I/O failure. (%s/10)", self.io_errors)

                if self.io_errors >= 10:
                    log.main.critical("The battery thread has been shutdown.")
                    return

            # Log it
            log.battery.debug(
                "%sV, %s, %s",
                SHARED_STATE.battery_voltage,
                self.power_state_text[self.power_state],
                self.charging_state_text[self.charging_state],
            )

            # if the power state changed, log it in the main log
            if self.power_state != self.power_state_prev:
                log.main.info(
                    "The power state changed from %s to %s",
                    self.power_state_text[self.power_state_prev],
                    self.power_state_text[self.power_state],
                )
            self.power_state_prev = self.power_state

            # Copy to Global State
            SHARED_STATE.power_state = self.power_state_text[self.power_state]
            SHARED_STATE.charging_state = self.charging_state_text[self.charging_state]

            time.sleep(60)


# Instantiate and start the thread
thread = Battery()
thread.daemon = True
thread.start()

"""
Handles gyro hardware
"""
import time
import threading
import numpy as np
from mpu6050 import mpu6050

from christine import log
from christine.status import STATE
from christine.parietal_lobe import parietal_lobe


class Gyro(threading.Thread):
    """
    Poll the Gyro / Accelerometer forever
    """

    name = "Gyro"

    def __init__(self):
        super().__init__(daemon=True)

        # How many single samples are averaged together to smooth the reading
        self.sample_size = 3

        # Varous lists to store single samples. When they're full the values are averaged
        self.accel_x_record = [0.0] * self.sample_size
        self.accel_y_record = [0.0] * self.sample_size
        self.gyro_x_record = [0.0] * self.sample_size
        self.gyro_y_record = [0.0] * self.sample_size
        self.gyro_z_record = [0.0] * self.sample_size

        # Smoothed average values
        self.total_jostled = 0.0

        # index to keep track of pulling the average every SampleSize times
        self.loop_index = 0

        # I think sometimes the touch sensor or other I2C things conflict with the gyro, so I want to shut it down only after a run of i/o errors
        self.io_errors = 0

        # I want to keep track of the max jostled level, and taper off slowly, very slowly
        self.jostled_level = 0.0
        self.jostled_avg_window = 5000.0
        # I also want a super short term running average
        self.jostled_avg_window_short = 40.0

        # keep track of where we are in loop
        self.loop_iteration = 0

        # be quiet, linter
        self.sensor = None

        # I want to limit how often jostled messages get sent to the LLM
        self.time_of_last_spike = time.time()

        # also I want to not send the jostled message right away
        # if I send it right away then we might report only the start of the "beating" and not the true magnitude
        # since we sleep 0.025s between gyro queries, I'd say 40 is at least close enough to 0.5s.
        self.jostled_message_countdown = 20
        self.jostled_message_counter = 0

    def run(self):

        try:
            # setup that sensor
            self.sensor = mpu6050(0x68)
            self.sensor.set_accel_range(mpu6050.ACCEL_RANGE_2G)
            STATE.gyro_available = True

        except OSError:
            log.main.error("Gyro unavailable.")
            STATE.jostled_level = 0.0
            STATE.gyro_available = False
            return

        while True:
            # graceful shutdown
            if STATE.please_shut_down:
                log.gyro.info("Thread shutting down")
                break

            # Get data from sensor at full speed. Doesn't seem to need any sleeps.
            # I'm testing with a sleep now. The sleep seems to be a good idea.
            try:
                data = self.sensor.get_all_data()
                self.io_errors = 0

            except OSError:
                # if gyro fails 10 times in a row, shut it down
                self.io_errors += 1
                log.main.warning("I/O failure. (%s/10)", self.io_errors)

                if self.io_errors >= 10:
                    log.main.critical("The gyro thread has been shutdown.")
                    STATE.jostled_level = 0.0
                    STATE.gyro_available = False
                    parietal_lobe.gyro_failure()
                    return

            # Keep track of which iteration we're on. Fill the array with data.
            self.loop_iteration = self.loop_index % self.sample_size

            # For Accel, we're just interested in the tilt of her body. Such as, sitting up, laying down, etc
            self.accel_x_record[self.loop_iteration] = data[0]["x"]
            self.accel_y_record[self.loop_iteration] = data[0]["y"]

            # For Gyro, all I'm interested in is a number to describe how jostled she is, so I abs the data
            self.gyro_x_record[self.loop_iteration] = abs(data[1]["x"])
            self.gyro_y_record[self.loop_iteration] = abs(data[1]["y"])
            self.gyro_z_record[self.loop_iteration] = abs(data[1]["z"])

            # Every SampleSize'th iteration, send the average
            if self.loop_iteration == 0:
                # Calculate averages
                self.total_jostled = (
                    (sum(self.gyro_x_record) / self.sample_size)
                    + (sum(self.gyro_y_record) / self.sample_size)
                    + (sum(self.gyro_z_record) / self.sample_size)
                )

                # Standardize jostled level to a number between 0 and 1, and clip.
                # As an experiment, I, um, gently beat my wife while apologizing profusely, and found I got it up to 85. Don't beat your wife.
                # When she's just sitting there it's always 7
                # However, after grepping the gyro log, it got down to 3 one time, and 6 lots of times, so this is fine. However, that would just get clipped, so 7 is still a good baseline
                self.jostled_level = (self.total_jostled - 7) / 80
                self.jostled_level = float(np.clip(self.jostled_level, 0.0, 1.0))

                # If there's a spike, make that the new global status. It'll slowly taper down.
                if self.jostled_level > STATE.jostled_level:
                    STATE.jostled_level = self.jostled_level
                if self.jostled_level > STATE.jostled_level_short:
                    STATE.jostled_level_short = self.jostled_level

                # Update the running averages
                # This should be the thing that tapers down
                STATE.jostled_level = (
                    STATE.jostled_level * self.jostled_avg_window
                ) / (self.jostled_avg_window + 1)
                STATE.jostled_level_short = (
                    STATE.jostled_level_short * self.jostled_avg_window_short
                ) / (self.jostled_avg_window_short + 1)

                # if there is a sudden spike notify the proper handlers of such events, but not too frequently
                if self.jostled_level > 0.15 and time.time() > self.time_of_last_spike + 30:
                    self.jostled_message_counter = self.jostled_message_countdown
                    self.time_of_last_spike = time.time()

                # the counter is used to delay sending the notification
                if self.jostled_message_counter == 1:
                    self.jostled_message_counter -= 1
                    parietal_lobe.gyro_notify_jostled()
                else:
                    self.jostled_message_counter -= 1

            self.loop_index += 1
            time.sleep(0.025)


# Instantiate
gyro = Gyro()

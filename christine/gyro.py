"""
Handles gyro hardware
"""
import time
import threading
import numpy as np
from mpu6050 import mpu6050

from christine import log
from christine.status import SHARED_STATE


class Gyro(threading.Thread):
    """
    Poll the Gyro / Accelerometer forever
    """

    name = "Gyro"

    def __init__(self):
        threading.Thread.__init__(self)

        # How many single samples are averaged together to smooth the reading
        self.sample_size = 3

        # Varous lists to store single samples. When they're full the values are averaged
        self.accel_x_record = [0.0] * self.sample_size
        self.accel_y_record = [0.0] * self.sample_size
        self.gyro_x_record = [0.0] * self.sample_size
        self.gyro_y_record = [0.0] * self.sample_size
        self.gyro_z_record = [0.0] * self.sample_size

        # Smoothed average values
        # self.SmoothXTilt = 0.0
        # self.SmoothYTilt = 0.0
        self.total_jostled = 0.0

        # index to keep track of pulling the average every SampleSize times
        self.loop_index = 0

        # I think sometimes the touch sensor or other I2C things conflict with the gyro, so I want to shut it down only after a run of i/o errors
        self.io_errors = 0

        # I want to keep track of the max jostled level, and taper off slowly
        self.jostled_level = 0.0
        self.jostled_avg_window = 2000.0
        # I also want a super short term running average
        self.jostled_avg_window_short = 40.0

        # keep track of where we are in loop
        self.loop_iteration = 0

        # be quiet, linter
        self.sensor = None

    def run(self):
        log.gyro.debug("Thread started.")

        try:
            # setup that sensor
            self.sensor = mpu6050(0x68)
            self.sensor.set_accel_range(mpu6050.ACCEL_RANGE_2G)

        except OSError:
            log.main.error("Gyro unavailable.")
            SHARED_STATE.jostled_level = 0.0
            SHARED_STATE.is_laying_down = False
            return

        while True:
            # graceful shutdown
            if SHARED_STATE.please_shut_down:
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
                    SHARED_STATE.jostled_level = 0.0
                    SHARED_STATE.is_laying_down = False
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
                SHARED_STATE.tilt_x = sum(self.accel_x_record) / self.sample_size
                SHARED_STATE.tilt_y = sum(self.accel_y_record) / self.sample_size
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
                if self.jostled_level > SHARED_STATE.jostled_level:
                    SHARED_STATE.jostled_level = self.jostled_level
                if self.jostled_level > SHARED_STATE.jostled_level_short:
                    SHARED_STATE.jostled_level_short = self.jostled_level

                # Update the running averages
                # This should be the thing that tapers down
                SHARED_STATE.jostled_level = (
                    SHARED_STATE.jostled_level * self.jostled_avg_window
                ) / (self.jostled_avg_window + 1)
                SHARED_STATE.jostled_level_short = (
                    SHARED_STATE.jostled_level_short * self.jostled_avg_window_short
                ) / (self.jostled_avg_window_short + 1)

                # if she gets hit, wake up a bit
                if self.jostled_level > 0.20:
                    self.jostled_level = 0.20
                    SHARED_STATE.behaviour_zone.notify_jostled(self.jostled_level)

                # Update the boolean that tells if we're laying down. While laying down I recorded 4.37, 1.60. However, now it's 1.55, 2.7. wtf happened? The gyro has not moved. Maybe position difference.
                # At some point I ought to self-calibrate this. When it's dark, and not jostled for like an hour, that's def laying down, save it.
                # This is something I'll need to save in the sqlite db
                if (
                    abs(SHARED_STATE.tilt_x - SHARED_STATE.sleep_tilt_x) < 0.2
                    and abs(SHARED_STATE.tilt_y - SHARED_STATE.sleep_tilt_y) < 0.2
                ):
                    SHARED_STATE.is_laying_down = True
                else:
                    SHARED_STATE.is_laying_down = False

                # self-calibrate the gyro position that is resting in bed
                # So if she ever sleeps standing that's going to fuck this up
                if (
                    SHARED_STATE.light_level <= 0.1
                    and SHARED_STATE.jostled_level <= 0.02
                    and self.jostled_level <= 0.02
                    and SHARED_STATE.is_sleeping is True
                ):
                    SHARED_STATE.sleep_tilt_x = SHARED_STATE.tilt_x
                    SHARED_STATE.sleep_tilt_y = SHARED_STATE.tilt_y
                    # SHARED_STATE.SleepXTilt = ((SHARED_STATE.SleepXTilt * 100.0) + SHARED_STATE.XTilt) / 101.0
                    # SHARED_STATE.SleepYTilt = ((SHARED_STATE.SleepYTilt * 100.0) + SHARED_STATE.YTilt) / 101.0

                # # log it
                # log.gyro.debug(
                #     "X: %.2f, Y: %.2f}, J: %.2f} JPctLT: %.2f} JPctST: %.2f} SlX: %.2f} SlY: %.2f} LD: {7}",
                #     SHARED_STATE.tilt_x,
                #     SHARED_STATE.tilt_y,
                #     self.total_jostled,
                #     SHARED_STATE.jostled_level,
                #     SHARED_STATE.jostled_level_short,
                #     SHARED_STATE.sleep_tilt_x,
                #     SHARED_STATE.sleep_tilt_y,
                #     SHARED_STATE.is_laying_down,
                # )

            self.loop_index += 1
            time.sleep(0.025)


# Instantiate and start the thread
thread = Gyro()
thread.daemon = True
thread.start()

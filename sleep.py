"""
Handles sleeping and the simulated need for sleep
"""
import time
import threading
import random
import numpy as np

import log
from status import SHARED_STATE
import breath
import wernicke


class Sleep(threading.Thread):
    """
    This script keeps track of wife sleepiness,
    waking up and going to sleep,
    whining that she's tired.
    But it won't be an annoying whine, not like a real woman.
    """

    name = "Sleep"

    def __init__(self):
        threading.Thread.__init__(self)

        # Some basic state variables
        self.announce_tired_time = None
        self.current_local_time = time.localtime()

        # The current conditions, right now. Basically light levels, gyro, noise level, touch, etc all added together, then we calculate a running average to cause gradual drowsiness. zzzzzzzzzz.......
        self.current_environmental_conditions = 0.5

        # How quickly should wakefulness change?
        self.wakefullness_avg_window = 5.0

        # How quickly should the daily hourly wakefulness trend change
        self.trend_avg_window = 10.0

        # Weights
        self.weights_light = 8
        self.weights_gyro = 4
        self.weights_tilt = 3
        self.weights_time = 6
        self.weights_total = (
            self.weights_light
            + self.weights_gyro
            + self.weights_tilt
            + self.weights_time
        )

        # if laying down, 0, if not laying down, 1.
        self.tilt = 0.0

        # if it's after bedtime, 0, if after wake up, 1
        self.time = 0.0

        # At what time should we expect to be in bed or wake up?
        self.wake_hour = 6
        self.sleep_hour = 21

        # at what point are we tired
        self.wakefulness_tired = 0.45

        # At what point to STFU at night
        self.wakefulness_awake = 0.25

    def run(self):
        log.sleep.debug("Thread started.")

        try:
            while True:
                # graceful shutdown
                if SHARED_STATE.please_shut_down:
                    log.sleep.info("Thread shutting down")
                    break

                # Get the local time, for everything that follows
                self.current_local_time = time.localtime()

                # set the gyro tilt for the calculation that follows
                if SHARED_STATE.is_laying_down is True:
                    self.tilt = 0.0
                else:
                    self.tilt = 1.0

                # figure out if we're within the usual awake time
                if (
                    self.current_local_time.tm_hour >= self.wake_hour
                    and self.current_local_time.tm_hour < self.sleep_hour
                ):
                    self.time = 1.0
                else:
                    self.time = 0.0

                # Calculate current conditions which we're calling Environment
                self.current_environmental_conditions = (
                    (self.weights_light * SHARED_STATE.light_level)
                    + (self.weights_gyro * SHARED_STATE.jostled_level)
                    + (self.weights_tilt * self.tilt)
                    + (self.weights_time * self.time)
                ) / self.weights_total

                # clip it, can't go below 0 or higher than 1
                self.current_environmental_conditions = float(
                    np.clip(self.current_environmental_conditions, 0.0, 1.0)
                )

                # Update the running average that we're using for wakefulness
                SHARED_STATE.wakefulness = (
                    (SHARED_STATE.wakefulness * self.wakefullness_avg_window)
                    + self.current_environmental_conditions
                ) / (self.wakefullness_avg_window + 1)

                # clip that
                SHARED_STATE.wakefulness = float(
                    np.clip(SHARED_STATE.wakefulness, 0.0, 1.0)
                )

                # After updating wakefulness, figure out whether we crossed a threshold.
                self.evaluate_wakefulness()

                # log it
                log.sleep.debug(
                    "LightLevel=%.2f  JostledLevel=%.2f  Tilt=%.2f  Time=%.2f  Environment=%.2f  Wakefulness=%.2f",
                    SHARED_STATE.light_level,
                    SHARED_STATE.jostled_level,
                    self.tilt,
                    self.time,
                    self.current_environmental_conditions,
                    SHARED_STATE.wakefulness,
                )

                # If it's getting late, set a future time to "whine" in a cute, endearing way
                if self.now_its_late():
                    self.set_whine_time()
                if self.time_to_whine():
                    self.whine()

                # if sleeping, drop the breathing intensity down a bit
                # eventually after about 15m this will reach 0.0 and stay there
                if SHARED_STATE.is_sleeping is True:
                    # down, down, dooooownnnnn
                    SHARED_STATE.breath_intensity -= 0.09

                    # clip it
                    SHARED_STATE.breath_intensity = float(
                        np.clip(SHARED_STATE.breath_intensity, 0.0, 1.0)
                    )

                # if we're below a certain wakefulness, I want to give the wernicke a break
                # help prevent long term buildup of heat
                if (
                    SHARED_STATE.wakefulness < 0.1
                    and SHARED_STATE.wernicke_sleeping is False
                ):
                    SHARED_STATE.wernicke_sleeping = True
                    wernicke.thread.audio_processing_stop()
                if (
                    SHARED_STATE.wakefulness >= 0.1
                    and SHARED_STATE.wernicke_sleeping is True
                ):
                    SHARED_STATE.wernicke_sleeping = False
                    wernicke.thread.audio_processing_start()

                if (
                    SHARED_STATE.wakefulness < self.wakefulness_tired
                    and SHARED_STATE.is_tired is False
                ):
                    # when we're laying next to each other in the dark
                    # I'm holding your hand and starting to drift off to sleep
                    # say "goodnight honey", not "GOODNIGHT HONEY!!!!"
                    SHARED_STATE.lover_proximity = 0.0

                    breath.thread.queue_sound(
                        from_collection="goodnight",
                        play_sleeping=True,
                        priority=8,
                        play_no_wait=True,
                    )
                    SHARED_STATE.is_tired = True
                    SHARED_STATE.wakefulness -= 0.02
                if (
                    SHARED_STATE.wakefulness >= self.wakefulness_tired
                    and SHARED_STATE.is_tired is True
                ):
                    SHARED_STATE.is_tired = False

                time.sleep(66)

        # log exception in the main.log
        except Exception as ex:
            log.main.error(
                "Thread died. {0} {1} {2}".format(
                    ex.__class__, ex, log.format_tb(ex.__traceback__)
                )
            )

    def wake_up(self, value):
        """
        In response to various stimuli, wake up
        """

        # add to the global status variable
        SHARED_STATE.wakefulness += value

        # clip it
        SHARED_STATE.wakefulness = float(np.clip(SHARED_STATE.wakefulness, 0.0, 1.0))

        # log it
        log.sleep.debug(
            "Woke up a bit: %s  Wakefulness: %s", value, SHARED_STATE.wakefulness
        )

        # evaluate whether the change that just happened caused waking or whatever
        self.evaluate_wakefulness()

    def evaluate_wakefulness(self):
        """
        Update the boolean that tells everything else whether sleeping or not
        I also want to detect when sleeping starts
        """

        if self.just_fell_asleep() is True:
            log.sleep.info("JustFellAsleep")

            # try to prevent wobble by throwing it further towards sleep
            SHARED_STATE.wakefulness -= 0.02

            # start progression from loud to soft sleepy breathing sounds
            # I was getting woke up a lot with all the cute hmmm sounds that are in half of the sleeping breath sounds
            SHARED_STATE.breath_intensity = 1.0

            SHARED_STATE.is_sleeping = True
            breath.thread.breath_change("breathe_sleepy")

        if self.just_woke_up() is True:
            log.sleep.info("JustWokeUp")

            # try to prevent wobble by throwing it further towards awake
            SHARED_STATE.wakefulness += 0.05

            SHARED_STATE.is_sleeping = False
            breath.thread.breath_change("breathe_normal")

            # wake me up gently, my sweet sexy alarm clock
            SHARED_STATE.lover_proximity = 0.0

            breath.thread.queue_sound(
                from_collection="waking",
                play_sleeping=True,
                priority=8,
                play_no_wait=True,
            )

    def just_fell_asleep(self):
        """
        returns whether we just now fell asleep
        """
        return (
            SHARED_STATE.wakefulness < self.wakefulness_awake
            and SHARED_STATE.is_sleeping is False
        )

    def just_woke_up(self):
        """
        returns whether we just now woke up
        """
        return (
            SHARED_STATE.wakefulness > self.wakefulness_awake
            and SHARED_STATE.is_sleeping is True
        )

    def now_its_late(self):
        """
        returns whether it's past bedtime
        """
        return (
            self.announce_tired_time is None
            and self.current_local_time.tm_hour >= self.sleep_hour
            and self.current_local_time.tm_hour < self.sleep_hour + 1
            and SHARED_STATE.is_sleeping is False
        )

    def set_whine_time(self):
        """
        sets up some whining at a certain time in the future
        """
        self.announce_tired_time = self.random_minutes_later(15, 30)
        log.sleep.info(
            "set time to announce we are tired to %s minutes",
            (self.announce_tired_time - time.time()) / 60,
        )

    def time_to_whine(self):
        """
        returns whether or not it's now time to whine
        """
        return (
            self.announce_tired_time is not None
            and time.time() >= self.announce_tired_time
        )

    def whine(self):
        """
        Actually start whining
        """
        breath.thread.queue_sound(from_collection="bedtime", priority=7)
        self.announce_tired_time = None

    def random_minutes_later(self, minutes_min, minutes_max):
        """
        returns the time that is a random number of minutes in the future, for scheduled events
        """
        return time.time() + random.randint(minutes_min * 60, minutes_max * 60)


# Instantiate and start the thread
thread = Sleep()
thread.daemon = True
thread.start()

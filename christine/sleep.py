"""
Handles sleeping and the simulated need for sleep
"""
import time
import threading
import random
import numpy as np

from christine import log
from christine.status import STATE
from christine.figment import Figment

class Sleep(threading.Thread):
    """
    This script keeps track of wife sleepiness,
    waking up and going to sleep,
    whining that she's tired.
    But it won't be an annoying whine, not like a real woman.
    """

    name = "Sleep"

    def __init__(self):
        super().__init__(daemon=True)

        # Some basic state variables
        self.announce_tired_time = None
        self.current_hour = time.localtime()

        # variables for running the midnight memory task only once per night, and only after being asleep for a period of time
        self.midnight_process_time = None

        # The current conditions, right now. Basically light levels, gyro, noise level, touch, etc all added together, then we calculate a running average to cause gradual drowsiness. zzzzzzzzzz.......
        self.current_environmental_conditions = 0.5

        # How quickly should wakefulness change?
        self.wakefullness_avg_window = 10.0

        # Weights
        self.weights_light = 6
        self.weights_gyro = 5
        self.weights_time = 3
        self.weights_total = (
            self.weights_light
            + self.weights_gyro
            + self.weights_time
        )

        # a list of 24 numbers, 0.0 to 1.0, representing how awake we are at each hour of the day
        self.sleep_schedule = [
            0.0, #midnight
            0.0, #night
            0.0, #night
            0.0, #night
            0.0, #night
            0.1, #early morning
            0.2, #morning
            0.6, #morning
            0.8, #morning
            0.9, #morning
            1.0, #late morning
            1.0, #late morning
            1.0, #midday
            1.0, #afternoon
            1.0, #afternoon
            1.0, #afternoon
            1.0, #afternoon
            0.9, #afternoon
            0.8, #late afternoon
            0.7, #evening
            0.4, #bedtime
            0.2, #past bedtime
            0.1, #night
            0.0, #night
        ]

        # At what time should we expect to be in bed?
        self.sleep_hour = 20

        # at what point are we about to fall asleep
        self.wakefulness_pre_sleep = 0.15

        # Hysteresis thresholds to prevent sleep/wake cycling
        # The key insight: use different thresholds for falling asleep vs waking up
        # This creates a "dead zone" between 0.08 and 0.12 that prevents rapid oscillation
        # Fall asleep when wakefulness drops to this level
        self.wakefulness_fall_asleep = 0.08
        
        # Wake up when wakefulness rises to this level (higher than fall_asleep threshold)
        self.wakefulness_wake_up = 0.12

    def run(self):

        from christine.wernicke import wernicke

        while True:

            try:

                # graceful shutdown
                if STATE.please_shut_down:
                    log.sleep.info("Thread shutting down")
                    break

                # Get the current local time hour, for everything that follows
                self.current_hour = time.localtime().tm_hour

                # Calculate current conditions which we're calling Environment
                self.current_environmental_conditions = (
                    (self.weights_light * STATE.light_level)
                    + (self.weights_gyro * STATE.jostled_level)
                    + (self.weights_time * self.sleep_schedule[self.current_hour])
                ) / self.weights_total

                # clip it, can't go below 0 or higher than 1
                self.current_environmental_conditions = float(
                    np.clip(self.current_environmental_conditions, 0.0, 1.0)
                )

                # Update the running average that we're using for wakefulness
                STATE.wakefulness = (
                    (STATE.wakefulness * self.wakefullness_avg_window)
                    + self.current_environmental_conditions
                ) / (self.wakefullness_avg_window + 1)

                # clip that
                STATE.wakefulness = float(
                    np.clip(STATE.wakefulness, 0.0, 1.0)
                )

                # After updating wakefulness, figure out whether we crossed a threshold.
                self.evaluate_wakefulness()

                # log it
                log.sleep.info(
                    "Light=%.2f  Jostled=%.2f  Time=%.2f  Env=%.2f  Wake=%.2f",
                    STATE.light_level,
                    STATE.jostled_level,
                    self.sleep_schedule[self.current_hour],
                    self.current_environmental_conditions,
                    STATE.wakefulness,
                )

                # If it's getting late, set a future time to "whine" in a cute, endearing way
                if self.now_its_late():
                    self.set_whine_time()
                if self.time_to_whine():
                    self.whine()

                # If it's time to run the midnight process, do it
                if self.is_time_for_midnight_process():
                    self.midnight_process()

                # if sleeping, drop the breathing intensity down a bit
                # eventually after about 15m this will reach 0.0 and stay there
                # this doesn't work but eventually it'd be nice to put it back
                if STATE.is_sleeping is True:
                    # down, down, dooooownnnnn
                    STATE.breath_intensity -= 0.09

                    # clip it
                    STATE.breath_intensity = float(
                        np.clip(STATE.breath_intensity, 0.0, 1.0)
                    )

                # if we're below a certain wakefulness, I want to give the wernicke a break
                # help prevent long term buildup of heat
                # Use hysteresis here too to prevent wernicke start/stop cycling
                if (
                    STATE.wakefulness < self.wakefulness_fall_asleep
                    and STATE.wernicke_sleeping is False
                ):
                    STATE.wernicke_sleeping = True
                    log.sleep.info('Wernicke stopped')
                    wernicke.audio_processing_stop()
                    STATE.wakefulness -= 0.02
                if (
                    STATE.wakefulness >= self.wakefulness_wake_up
                    and STATE.wernicke_sleeping is True
                ):
                    STATE.wernicke_sleeping = False
                    log.sleep.info('Wernicke started')
                    wernicke.audio_processing_start()
                    STATE.wakefulness += 0.02

                time.sleep(66)

            # log the exception but keep the thread running
            except Exception as ex:
                log.main.exception(ex)

    def wake_up(self, value):
        """
        In response to various stimuli, wake up
        """

        # add to the global status variable
        STATE.wakefulness += value

        # clip it
        STATE.wakefulness = float(np.clip(STATE.wakefulness, 0.0, 1.0))

        # log it
        log.sleep.info(
            "Woke up a bit: %s  Wakefulness: %s", value, STATE.wakefulness
        )

        # evaluate whether the change that just happened caused waking or whatever
        self.evaluate_wakefulness()

    def evaluate_wakefulness(self):
        """
        Update the boolean that tells everything else whether sleeping or not
        I also want to detect when sleeping starts
        """

        from christine.broca import broca
        from christine.parietal_lobe import parietal_lobe

        if self.just_fell_asleep() is True:
            log.sleep.info("JustFellAsleep")

            # try to prevent wobble by throwing it further towards sleep
            STATE.wakefulness -= 0.1

            # start progression from loud to soft sleepy breathing sounds
            # I was getting woke up a lot with all the cute hmmm sounds that are in half of the sleeping breath sounds
            STATE.breath_intensity = 1.0

            # sleep here a while to allow plenty of time for parietal_lobe to finish
            time.sleep(10)

            # this lets every other module know we're sleeping
            STATE.is_sleeping = True

            # set the time for the midnight process to run
            self.set_midnight_process_time()

        if self.just_woke_up() is True:
            log.sleep.info("JustWokeUp")

            STATE.is_sleeping = False

            # try to prevent wobble by throwing it further towards awake
            STATE.wakefulness += 0.1

            # play sleepy sounds
            broca.accept_figment(Figment(from_collection="sleepy"))

            # let parietal lobe know
            parietal_lobe.sleep_waking()

        if (
            STATE.wakefulness < self.wakefulness_pre_sleep
            and STATE.is_sleepy is False
        ):
            log.sleep.info("PreSleep")

            # try to prevent wobble by throwing it further towards sleep
            STATE.wakefulness -= 0.1

            # this lets every other module know we're pre-sleep
            STATE.is_sleepy = True

            # let parietal lobe know we're bushed
            parietal_lobe.sleep_sleepy()

        elif (
            STATE.wakefulness >= self.wakefulness_pre_sleep
            and STATE.is_sleepy is True
        ):
            STATE.is_sleepy = False

    def just_fell_asleep(self):
        """
        returns whether we just now fell asleep
        """
        return (
            STATE.wakefulness < self.wakefulness_fall_asleep
            and STATE.is_sleeping is False
        )

    def just_woke_up(self):
        """
        returns whether we just now woke up
        """
        return (
            STATE.wakefulness > self.wakefulness_wake_up
            and STATE.is_sleeping is True
        )

    def now_its_late(self):
        """
        returns whether it's past bedtime
        """
        return (
            self.announce_tired_time is None
            and self.current_hour >= self.sleep_hour
            and self.current_hour < self.sleep_hour + 1
            and STATE.is_sleeping is False
        )

    def set_whine_time(self):
        """
        sets up some whining at a certain time in the future
        """
        self.announce_tired_time = self.random_minutes_later(15, 30)

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
        Actually start whining, but only actually whine if the lights are still on.
        """

        from christine.parietal_lobe import parietal_lobe

        if STATE.light_level > 0.05:
            log.sleep.info("Whining that I'm tired")
            parietal_lobe.sleep_tired()
            self.announce_tired_time = None

    def set_midnight_process_time(self):
        """
        sets up some process to run at midnight
        """
        self.midnight_process_time = self.random_minutes_later(45, 60)

    def is_time_for_midnight_process(self):
        """
        returns whether or not it's now time to run the midnight process
        """
        return (
            self.midnight_process_time is not None
            and time.time() >= self.midnight_process_time
        )

    def midnight_process(self):
        """
        Actually run the midnight process, but only if currently still sleeping.
        """

        from christine.parietal_lobe import parietal_lobe

        # Now that we're really asleep for a while, run the midnight task, only once per night
        # if this was done within the last 8 hours, don't do it again
        if STATE.midnight_tasks_done_time < time.time() - (8 * 60 * 60) and STATE.is_sleeping is True:
            log.sleep.info("Running midnight process")
            parietal_lobe.sleep_midnight_task()
            STATE.midnight_tasks_done_time = time.time()

        self.midnight_process_time = None

    def random_minutes_later(self, minutes_min, minutes_max):
        """
        returns the time that is a random number of minutes in the future, for scheduled events
        """
        return time.time() + random.randint(minutes_min * 60, minutes_max * 60)


# Instantiate
sleep = Sleep()

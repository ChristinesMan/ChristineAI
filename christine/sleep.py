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
        self.current_hour = time.localtime()

        # variables for running the midnight memory task only once per night, and only after being asleep for a period of time
        self.midnight_process_time = None
        self.sleep_started_at = None
        self.last_tired_perception_time = 0.0
        self.tired_perceptions_today = 0
        self.tired_perception_day = time.localtime().tm_yday
        self.last_wakefulness_for_tiredness = STATE.wakefulness
        self.last_schedule_update_day = None
        self.last_schedule_update_hour = None

        # The current conditions, right now. Basically light levels, gyro, noise level, touch, etc all added together, then we calculate a running average to cause gradual drowsiness. zzzzzzzzzz.......
        self.current_environmental_conditions = 0.5

        self.ensure_sleep_schedule_profile()

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

                # Adapt circadian schedule based on observed environmental factors
                self.update_adaptive_sleep_schedule()
                schedule_value = STATE.sleep_schedule_profile[self.current_hour]

                # Compute total dynamic weight, guard against divide-by-zero if user sets everything to zero
                weights_total = (
                    STATE.sleep_weight_light
                    + STATE.sleep_weight_gyro
                    + STATE.sleep_weight_time
                    + STATE.sleep_weight_inertia
                )
                if weights_total <= 0.0:
                    weights_total = 1.0

                sleep_inertia_environment = self.get_sleep_inertia_environment()

                # Calculate current conditions which we're calling Environment
                self.current_environmental_conditions = (
                    (STATE.sleep_weight_light * STATE.light_level)
                    + (STATE.sleep_weight_gyro * STATE.jostled_level)
                    + (STATE.sleep_weight_time * schedule_value)
                    + (STATE.sleep_weight_inertia * sleep_inertia_environment)
                ) / weights_total

                # clip it, can't go below 0 or higher than 1
                self.current_environmental_conditions = float(
                    np.clip(self.current_environmental_conditions, 0.0, 1.0)
                )

                # Update the running average that we're using for wakefulness
                STATE.wakefulness = (
                    (STATE.wakefulness * STATE.sleep_wakefulness_avg_window)
                    + self.current_environmental_conditions
                ) / (STATE.sleep_wakefulness_avg_window + 1)

                # clip that
                STATE.wakefulness = float(
                    np.clip(STATE.wakefulness, 0.0, 1.0)
                )

                # After updating wakefulness, figure out whether we crossed a threshold.
                self.evaluate_wakefulness()

                # log it
                log.sleep.info(
                    "Light=%.2f  Jostled=%.2f  Schedule=%.2f  Inertia=%.2f  Env=%.2f  Wake=%.2f",
                    STATE.light_level,
                    STATE.jostled_level,
                    schedule_value,
                    sleep_inertia_environment,
                    self.current_environmental_conditions,
                    STATE.wakefulness,
                )

                # Feed an organic tired perception when wakefulness trends downward,
                # with cooldown and daily cap to prevent oscillatory chatter.
                self.maybe_emit_tired_perception()

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
                    STATE.wakefulness < STATE.sleep_wakefulness_fall_asleep
                    and STATE.wernicke_sleeping is False
                ):
                    STATE.wernicke_sleeping = True
                    log.sleep.info('Wernicke stopped')
                    wernicke.audio_processing_stop()
                    STATE.wakefulness -= 0.02
                if (
                    STATE.wakefulness >= STATE.sleep_wakefulness_wake_up
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
            STATE.wakefulness -= STATE.sleep_transition_nudge_sleep

            # start progression from loud to soft sleepy breathing sounds
            # I was getting woke up a lot with all the cute hmmm sounds that are in half of the sleeping breath sounds
            STATE.breath_intensity = 1.0

            # sleep here a while to allow plenty of time for parietal_lobe to finish
            time.sleep(10)

            # this lets every other module know we're sleeping
            STATE.is_sleeping = True
            self.sleep_started_at = time.time()

            # set the time for the midnight process to run
            self.set_midnight_process_time()

        if self.just_woke_up() is True:
            log.sleep.info("JustWokeUp")

            STATE.is_sleeping = False
            self.sleep_started_at = None

            # try to prevent wobble by throwing it further towards awake
            STATE.wakefulness += STATE.sleep_transition_nudge_wake

            # play sleepy sounds
            broca.accept_figment(Figment(from_collection="sleepy"))

            # let parietal lobe know
            parietal_lobe.sleep_waking()

        if (
            STATE.wakefulness < STATE.sleep_wakefulness_pre_sleep
            and STATE.is_sleepy is False
        ):
            log.sleep.info("PreSleep")

            # try to prevent wobble by throwing it further towards sleep
            STATE.wakefulness -= STATE.sleep_transition_nudge_sleep

            # this lets every other module know we're pre-sleep
            STATE.is_sleepy = True

            # let parietal lobe know we're bushed
            parietal_lobe.sleep_sleepy()

        elif (
            STATE.wakefulness >= STATE.sleep_wakefulness_pre_sleep
            and STATE.is_sleepy is True
        ):
            STATE.is_sleepy = False

    def get_sleep_inertia_environment(self):
        """
        Sleep inertia is a stabilizing environmental input.
        Binary mode requested by operator:
        awake = 1.0, asleep = 0.0.
        Returns a value between 0.0 and 1.0, where lower means sleepier.
        """
        return 0.0 if STATE.is_sleeping else 1.0

    def ensure_sleep_schedule_profile(self):
        """
        Keep the adaptive schedule profile valid: exactly 24 clipped floats.
        """

        profile = getattr(STATE, 'sleep_schedule_profile', None)

        if not isinstance(profile, list) or len(profile) != 24:
            STATE.sleep_schedule_profile = [0.5] * 24
            return

        cleaned = []
        for value in profile:
            try:
                cleaned.append(float(np.clip(float(value), 0.0, 1.0)))
            except (TypeError, ValueError):
                cleaned.append(0.5)
        STATE.sleep_schedule_profile = cleaned

    def get_schedule_learning_observation(self):
        """
        Return a 0.0-1.0 wake-pressure observation used to train schedule profile.
        Uses existing environmental channels: light, movement, talking.
        """

        talking_signal = 1.0 if STATE.user_is_speaking else 0.0
        total = (
            STATE.sleep_schedule_source_weight_light
            + STATE.sleep_schedule_source_weight_gyro
            + STATE.sleep_schedule_source_weight_talking
        )
        if total <= 0.0:
            return 0.5

        observation = (
            (STATE.sleep_schedule_source_weight_light * STATE.light_level)
            + (STATE.sleep_schedule_source_weight_gyro * STATE.jostled_level)
            + (STATE.sleep_schedule_source_weight_talking * talking_signal)
        ) / total

        return float(np.clip(observation, 0.0, 1.0))

    def update_adaptive_sleep_schedule(self):
        """
        Train the hourly schedule profile gradually from environmental observations.
        This replaces the fixed hardcoded schedule with a natural drifting one.
        """

        self.ensure_sleep_schedule_profile()

        now = time.localtime()
        if (
            self.last_schedule_update_day == now.tm_yday
            and self.last_schedule_update_hour == self.current_hour
        ):
            return

        hour = self.current_hour
        prev_hour = (hour - 1) % 24
        next_hour = (hour + 1) % 24

        observation = self.get_schedule_learning_observation()
        learning_rate = float(np.clip(STATE.sleep_schedule_learning_rate, 0.0, 1.0))
        neighbor_blend = float(np.clip(STATE.sleep_schedule_neighbor_blend, 0.0, 1.0))

        current_value = STATE.sleep_schedule_profile[hour]
        updated_current = current_value + (learning_rate * (observation - current_value))
        updated_current = float(np.clip(updated_current, 0.0, 1.0))
        STATE.sleep_schedule_profile[hour] = updated_current

        if neighbor_blend > 0.0:
            prev_value = STATE.sleep_schedule_profile[prev_hour]
            next_value = STATE.sleep_schedule_profile[next_hour]
            STATE.sleep_schedule_profile[prev_hour] = float(np.clip(
                prev_value + (neighbor_blend * (updated_current - prev_value)),
                0.0,
                1.0,
            ))
            STATE.sleep_schedule_profile[next_hour] = float(np.clip(
                next_value + (neighbor_blend * (updated_current - next_value)),
                0.0,
                1.0,
            ))

        self.last_schedule_update_day = now.tm_yday
        self.last_schedule_update_hour = hour

        profile_summary = ','.join(f"{value:.2f}" for value in STATE.sleep_schedule_profile)
        log.sleep.info(
            "Schedule hourly update: hour=%02d observed=%.2f current=%.2f->%.2f profile=[%s]",
            hour,
            observation,
            current_value,
            updated_current,
            profile_summary,
        )

    def maybe_emit_tired_perception(self):
        """
        Sends sleepy perception events organically from wakefulness trend,
        with cooldown and daily caps to prevent oscillation and spam.
        """

        from christine.parietal_lobe import parietal_lobe

        today = time.localtime().tm_yday
        if today != self.tired_perception_day:
            self.tired_perception_day = today
            self.tired_perceptions_today = 0

        previous_wakefulness = self.last_wakefulness_for_tiredness
        current_wakefulness = STATE.wakefulness
        self.last_wakefulness_for_tiredness = current_wakefulness

        if STATE.is_sleeping is True:
            return

        if self.tired_perceptions_today >= STATE.sleep_tired_perception_max_per_day:
            return

        cooldown_seconds = STATE.sleep_tired_perception_cooldown_minutes * 60
        if time.time() - self.last_tired_perception_time < cooldown_seconds:
            return

        wakefulness_drop = previous_wakefulness - current_wakefulness
        crossed_threshold_down = (
            previous_wakefulness > STATE.sleep_tired_perception_threshold
            and current_wakefulness <= STATE.sleep_tired_perception_threshold
        )

        should_emit = (
            current_wakefulness <= STATE.sleep_tired_perception_threshold
            and (
                wakefulness_drop >= STATE.sleep_tired_perception_drop_min
                or crossed_threshold_down
            )
        )

        if should_emit:
            self.last_tired_perception_time = time.time()
            self.tired_perceptions_today += 1
            STATE.sleep_offer_state_tools_until = time.time() + (STATE.sleep_offer_state_tools_window_minutes * 60)
            log.sleep.info(
                "Sleepy perception emitted: wake_drop=%.3f wake=%.3f count_today=%s",
                wakefulness_drop,
                current_wakefulness,
                self.tired_perceptions_today,
            )
            parietal_lobe.sleep_tired()

    def just_fell_asleep(self):
        """
        returns whether we just now fell asleep
        """
        return (
            STATE.wakefulness < STATE.sleep_wakefulness_fall_asleep
            and STATE.is_sleeping is False
        )

    def just_woke_up(self):
        """
        returns whether we just now woke up
        """
        return (
            STATE.wakefulness > STATE.sleep_wakefulness_wake_up
            and STATE.is_sleeping is True
        )

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

            # Safety behavior: re-enable hearing each night in case it was manually disabled
            if STATE.perceptions_blocked is True:
                STATE.perceptions_blocked = False
                log.sleep.info("Midnight process re-enabled hearing (perceptions_blocked=False)")
            
            # Set the done time BEFORE starting processing to prevent loops on failure
            STATE.midnight_tasks_done_time = time.time()
            
            try:
                parietal_lobe.sleep_midnight_task()
                log.sleep.info("Midnight process completed successfully")
            except Exception as ex:
                log.sleep.exception("Midnight process failed but will not retry: %s", ex)

        self.midnight_process_time = None

    def random_minutes_later(self, minutes_min, minutes_max):
        """
        returns the time that is a random number of minutes in the future, for scheduled events
        """
        return time.time() + random.randint(minutes_min * 60, minutes_max * 60)


# Instantiate
sleep = Sleep()

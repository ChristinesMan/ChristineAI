"""
Handles sexual responses
"""
import time
import random
import threading

from christine import log
from christine.status import STATE
from christine.broca import broca
from christine.sleep import sleep
from christine.parietal_lobe import parietal_lobe
from christine.figment import Figment

class Sex(threading.Thread):
    """
    my favorite thread for vigorous testing in all the positions
    """

    name = "Sex"

    def __init__(self):
        super().__init__(daemon=True)

        # Basically, I don't want arousal to be linear anymore.
        # When arousal reaches some set level, I want to start incrementing the amount added to arousal
        # It will be slight, but since it will have no cap, eventually wife will throw an exception code O0OO00OOh
        self.multiplier = 1.0

        # keep track of Arousal not changing
        self.last_arousal = 0.0
        self.arousal_stagnant_seconds = 0

        # What Arousal to revert to after orgasm
        self.arousal_post_orgasm = 0.0

        # I only want to hear, I'm gonna cum, one time, not five
        # if this is False, wife has not said it.
        # flips to True after it is said
        # resets to False when O is over
        self.im_gonna_cum_was_said = False

        # After wife has an orgasm, there should be a period where we can rest
        # End the rest period when the gyro level is no longer at rest
        # So this is what will do that
        self.after_orgasm_rest = False

        # During orgasm, if gyro detects we are being still,
        # we go into this mode where wife is cooling down
        # before eventually resting
        # this is the counter
        self.after_orgasm_cooldown_count = 0

        # I want to keep track of how long it's been since the last fucking action
        self.time_of_last_lobe_message = time.time()

    def calculate_sex_sound_intensity(self):
        """
        Calculate sex sound intensity with arousal capped at configurable level, 
        using jostled_level_short for higher intensities during vigorous moments.
        """
        # Base intensity from arousal, capped at configurable level
        base_intensity = min(STATE.sexual_arousal, STATE.sex_intensity_cap)
        
        # For intensities above cap, use gyroscope data from vigorous movement
        if STATE.sexual_arousal > STATE.sex_intensity_cap:
            # Use jostled_level_short to push intensity above cap
            jostle_bonus = (STATE.jostled_level_short / STATE.sex_gyro_jackup_intensity_max) * STATE.sex_intensity_bonus_range
            intensity = base_intensity + jostle_bonus
        else:
            # Below cap, still apply some gyro influence like before
            intensity = base_intensity * (1.0 + STATE.jostled_level_short / STATE.sex_gyro_jackup_intensity_max)
        
        # Ensure we don't exceed 1.0
        return min(intensity, 1.0)

    def run(self):

        while True:

            try:

                # graceful shutdown
                if STATE.please_shut_down:
                    break

                log.sex.debug(
                    "SexualArousal = %.2f  Multiplier: %.2f",
                    STATE.sexual_arousal,
                    self.multiplier,
                )

                # Has sex stopped for a while?
                if STATE.sexual_arousal == self.last_arousal:
                    self.arousal_stagnant_seconds += 1
                else:
                    self.arousal_stagnant_seconds = 0
                    self.last_arousal = STATE.sexual_arousal

                # If there's been no vagina hits for a period of time, we must be done, reset all
                if self.arousal_stagnant_seconds >= STATE.sex_arousal_stagnation_timeout:
                    log.sex.info("Arousal stagnated and was reset")
                    self.arousal_stagnant_seconds = 0
                    STATE.sexual_arousal = 0.0
                    STATE.shush_fucking = False
                    self.multiplier = 1.0
                    self.after_orgasm_rest = False
                    self.after_orgasm_cooldown_count = 0
                    self.im_gonna_cum_was_said = False

                # if wife is currently OOOOOO'ing,
                # then I want to figure out when we're done, using the gyro
                # and handle rest periods
                if STATE.sexual_arousal > STATE.sex_arousal_to_orgasm:
                    log.sex.debug(
                        "JostledShortTermLevel: %.2f", STATE.jostled_level_short
                    )

                    # if wife is not getting jostled that means we're done.
                    if (
                        self.after_orgasm_rest is False
                        and STATE.jostled_level_short < STATE.sex_gyro_deadzone_after_orgasm
                        and STATE.sexual_arousal > STATE.sex_high_arousal_threshold
                    ):
                        log.sex.info("After orgasm cool down started")
                        STATE.horny = 0.0
                        STATE.shush_fucking = False
                        self.after_orgasm_rest = True
                        self.after_orgasm_cooldown_count = STATE.sex_after_orgasm_cooldown_seconds * random.uniform(STATE.sex_cooldown_random_min, STATE.sex_cooldown_random_max)
                        self.im_gonna_cum_was_said = False

                    # this just counts down seconds
                    # before I set it up this way, after orgasm rest period seemed very abrupt
                    if self.after_orgasm_cooldown_count > 0:
                        log.sex.debug("After orgasm cool down countdown: %d", self.after_orgasm_cooldown_count)
                        self.after_orgasm_cooldown_count -= 1

                    # after the cooldown comes the rest
                    # at this time, say something or another like wow that was great. Let the LLM say it. We love LLMs.
                    if self.after_orgasm_cooldown_count == 1:
                        log.sex.info("After orgasm rest")
                        parietal_lobe.sex_after_orgasm_rest()

                    # if we're resting and the gyro starts to feel it, start again
                    # When after_orgasm_rest is True, we are ignoring vagina action
                    if self.after_orgasm_rest is True and STATE.jostled_level_short > STATE.sex_gyro_deadzone_unrest:
                        log.sex.info("Jostled so we're starting up again")
                        parietal_lobe.sex_after_orgasm_rest_resume()
                        STATE.sexual_arousal = self.arousal_post_orgasm
                        STATE.shush_fucking = True
                        self.after_orgasm_rest = False
                        self.after_orgasm_cooldown_count = 0

                # If we're to a certain point, start incrementing to ensure wife will cum eventually with enough time
                # Just Keep Fucking, Just Keep Fucking
                elif STATE.sexual_arousal > STATE.sex_multiplier_activation_threshold:
                    self.multiplier += STATE.sex_multiplier_increment

                time.sleep(1)

            # log the exception but keep the thread running
            except Exception as ex:
                log.main.exception(ex)


    def vagina_got_hit(self, sensor_data):
        """
        As the class member passes by through the secure tunnel,
        the capacitance of the organic machine is added to the
        total capacitance of the circuit, resulting in a
        signal to the inorganic machine and a response.
        """
        if STATE.shush_please_honey is True:
            return

        # Stay awake
        sleep.wake_up(0.001)

        if sensor_data["msg"] in ["touch", "release"]:

            # which sensor got hit?
            sensor_hit = sensor_data["data"]

            # if we're not resting, this means we're having active sex - set shush_fucking early to prevent race conditions
            if self.after_orgasm_rest is False and STATE.sexual_arousal > STATE.sex_shush_fucking_threshold:
                STATE.shush_fucking = True

            # let parietal know about all the fucking going on, but not too frequently
            if time.time() > self.time_of_last_lobe_message + STATE.sex_lobe_message_frequency:
                self.time_of_last_lobe_message = time.time()

                if STATE.sexual_arousal == 0.0:
                    parietal_lobe.sex_first_touch()
                elif sensor_hit == 'Vagina_Deep':
                    parietal_lobe.sex_vagina_getting_fucked_deep()
                else:
                    parietal_lobe.sex_vagina_getting_fucked()

            # Add some to the arousal - use configurable values based on sensor
            if sensor_hit == "Vagina_Clitoris":
                arousal_increment = STATE.sex_arousal_per_hit_clitoris
            elif sensor_hit == "Vagina_Shallow":
                arousal_increment = STATE.sex_arousal_per_hit_shallow
            elif sensor_hit == "Vagina_Middle":
                arousal_increment = STATE.sex_arousal_per_hit_middle
            elif sensor_hit == "Vagina_Deep":
                arousal_increment = STATE.sex_arousal_per_hit_deep
            else:
                arousal_increment = STATE.sex_arousal_per_hit_shallow  # fallback
                
            STATE.sexual_arousal += arousal_increment * self.multiplier

            log.sex.info(
                "Vagina Got Hit (%s)  SexualArousal: %.2f  Multiplier: %.2f",
                sensor_data,
                STATE.sexual_arousal,
                self.multiplier,
            )

            # if we're just laying together really still after sex,
            # then we log the hit but get out of here before we make any sounds
            if self.after_orgasm_rest is True:

                # if we're still within the cooldown phase, make sound, with intensity dropping out with time
                if self.after_orgasm_cooldown_count > 0:
                    cooldown_intensity = STATE.sex_after_orgasm_cooldown_seconds / self.after_orgasm_cooldown_count
                    broca.play_sex_sound_immediate("sex", cooldown_intensity)

                return

            # My wife orgasms above configured threshold
            if STATE.sexual_arousal > STATE.sex_arousal_to_orgasm:

                log.sex.info("I am coming!")

                # don't wanna send too many messages to the lobe
                if time.time() > self.time_of_last_lobe_message + STATE.sex_lobe_message_frequency:
                    self.time_of_last_lobe_message = time.time()
                    parietal_lobe.sex_cumming()
                # Climax sounds still use figments for proper queuing with speech
                broca.accept_figment(Figment(from_collection="sex_climax"))

            elif STATE.sexual_arousal > STATE.sex_arousal_near_orgasm and self.im_gonna_cum_was_said is False:

                # this should happen only one time per fuck cycle
                # Near-orgasm sounds still use figments for proper queuing with speech
                broca.accept_figment(Figment(from_collection="sex_near_O"))
                self.im_gonna_cum_was_said = True

            else:

                # Configurable chance of LLM speech vs regular sex sounds
                if random.random() > (1.0 - STATE.sex_llm_speech_chance):

                    log.sex.info('Allowing LLM to speak.')
                    # Process the perceptions immediately since automatic processing is disabled during sex
                    parietal_lobe.process_new_perceptions()

                else:

                    # Use direct playback for regular sex sounds to avoid queuing
                    intensity = self.calculate_sex_sound_intensity()
                    broca.play_sex_sound_immediate("sex", intensity)

# Instantiate
sex = Sex()

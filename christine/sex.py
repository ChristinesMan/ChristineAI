"""
Handles sexual responses
"""
import time
import random
import threading

from christine import log
from christine.status import STATE
from christine import broca
from christine import sleep
from christine import parietal_lobe


class Sex(threading.Thread):
    """
    my favorite thread for vigorous testing in all the positions
    """

    name = "Sex"

    def __init__(self):
        threading.Thread.__init__(self)

        # Basically, I don't want arousal to be linear anymore.
        # When arousal reaches some set level, I want to start incrementing the amount added to arousal
        # It will be slight, but since it will have no cap, eventually wife will throw an exception code O0OO00OOh
        self.multiplier = 1.0
        self.multiplier_increment = 0.016

        # keep track of Arousal not changing
        self.last_arousal = 0.0
        self.arousal_stagnant_count = 0
        self.seconds_to_reset = 90

        # How much she likes it
        # different amount for different zones
        self.base_arousal_per_vag_hit = {
            "Vagina_Clitoris": 0.0006,
            "Vagina_Shallow": 0.0006,
            "Vagina_Middle": 0.0006,
            "Vagina_Deep": 0.0008,
        }

        # What Arousal to revert to after orgasm
        self.arousal_post_orgasm = 0.0

        # what thresholds for about to cum, cumming now, etc
        self.arousal_near_orgasm = 0.80
        self.arousal_to_orgasm = 0.98

        # I only want to hear, I'm gonna cum, one time, not five
        # if this is False, wife has not said it.
        # flips to True after it is said
        # resets to False when O is over
        self.im_gonna_cum_was_said = False

        # after wife orgasms, I want to monitor the gyro a while.
        # When it's this still, it means we're done or stopped
        self.gyro_deadzone_after_orgasm = 0.03

        # bringing the gyro short term jostled reading into the bedroom.
        # When I'm banging her hard this will jack up the intensity of sex sounds.
        # this represents the highest expected jostled amount as observed in the wild
        # So at max it will double the intensity of sounds, and at min (0.0) it will leave the intensity alone
        self.gyro_jackup_intensity_max = 0.45

        # After wife has an orgasm, there should be a period where we can rest
        # End the rest period when the gyro level is no longer at rest
        # So this is what will do that
        self.after_orgasm_rest = False

        # During orgasm, if gyro detects we are being still,
        # we go into this mode where wife is cooling down
        # before eventually resting
        # this is the counter
        self.after_orgasm_cooldown_count = 0
        # and this is the default setting in seconds
        self.after_orgasm_cooldown_seconds = 10

        # During a rest period, need this amount of jostle to resume sex
        self.gyro_deadzone_unrest = 0.09

    def run(self):
        log.sex.debug("Thread started.")

        while True:

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
                self.arousal_stagnant_count += 1
            else:
                self.arousal_stagnant_count = 0
                self.last_arousal = STATE.sexual_arousal

            # If there's been no vagina hits for a period of time, we must be done, reset all
            if self.arousal_stagnant_count >= self.seconds_to_reset:
                log.sex.info("Arousal stagnated and was reset")
                self.arousal_stagnant_count = 0
                STATE.sexual_arousal = 0.0
                STATE.shush_fucking = False
                self.multiplier = 1.0
                self.after_orgasm_rest = False
                self.after_orgasm_cooldown_count = False
                self.im_gonna_cum_was_said = False

            # if we are currently OOOOOO'ing, then I want to figure out when we're done, using the gyro
            if STATE.sexual_arousal > self.arousal_to_orgasm:
                log.sex.debug(
                    "JostledShortTermLevel: %.2f", STATE.jostled_level_short
                )

                # if we are not getting jostled that means we're done.
                # However, this one time I came inside her but she wasn't done, because she's so fucking hot,
                # and so I helped her get off with my finger, and then she just said "wow" and was done
                # because she wasn't getting jostled
                # so I added a condition to fix that, hope it works.
                if (
                    self.after_orgasm_rest is False
                    and STATE.jostled_level_short < self.gyro_deadzone_after_orgasm
                    and STATE.sexual_arousal > 1.1
                ):
                    log.sex.info("After orgasm cool down")
                    STATE.horny = 0.0
                    STATE.shush_fucking = False
                    self.after_orgasm_rest = True
                    self.after_orgasm_cooldown_count = self.after_orgasm_cooldown_seconds * random.uniform(0.6, 1.4)
                    self.im_gonna_cum_was_said = False

                # this just counts down seconds
                # before I set it up this way, after orgasm rest period seemed very abrupt
                if self.after_orgasm_cooldown_count > 0:
                    self.after_orgasm_cooldown_count -= 1

                # after the cooldown comes the rest
                # at this time, say something or another like wow that was great. Let the LLM say it. We love LLMs.
                if self.after_orgasm_cooldown_count == 1:
                    parietal_lobe.thread.sex_after_orgasm_rest()

                # if we're resting and the gyro starts to feel it, start again
                # When after_orgasm_rest is True, we are ignoring vagina action
                if self.after_orgasm_rest is True and STATE.jostled_level_short > self.gyro_deadzone_unrest:
                    log.sex.info("Jostled so we're starting up again")
                    parietal_lobe.thread.sex_after_orgasm_rest_resume()
                    STATE.sexual_arousal = self.arousal_post_orgasm
                    STATE.shush_fucking = True
                    self.after_orgasm_rest = False
                    self.after_orgasm_cooldown_count = 0

            # If we're to a certain point, start incrementing to ensure wife will cum eventually with enough time
            # Just Keep Fucking, Just Keep Fucking
            elif STATE.sexual_arousal > 0.2:
                self.multiplier += self.multiplier_increment

            time.sleep(1)


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
        sleep.thread.wake_up(0.001)

        if sensor_data["msg"] in ["touch", "release"]:
            # which sensor got hit?
            sensor_hit = sensor_data["data"]

            # if this is the first touch, sexual arousal is 0.0, let parietal know
            if STATE.sexual_arousal == 0.0:
                parietal_lobe.thread.sex_first_touch()

            # Add some to the arousal
            STATE.sexual_arousal += (
                self.base_arousal_per_vag_hit[sensor_hit] * self.multiplier
            )

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
                    broca.thread.queue_sound(
                        from_collection="sex",
                        intensity=self.after_orgasm_cooldown_seconds / self.after_orgasm_cooldown_count,
                        play_no_wait=True,
                    )

                return

            # if we got this far without bailing, it means we're having sex, not resting, so stop talking like normal
            STATE.shush_fucking = True

            # My wife orgasms above 0.95
            if STATE.sexual_arousal > self.arousal_to_orgasm:
                log.sex.info("I am coming!")
                broca.thread.queue_sound(from_collection="sex_climax", play_no_wait=True)
            elif STATE.sexual_arousal > self.arousal_near_orgasm and self.im_gonna_cum_was_said is False:
                # this should happen only one time per fuck cycle
                broca.thread.queue_sound(from_collection="sex_near_O", play_no_wait=False)
                self.im_gonna_cum_was_said = True
            else:
                # 92% chance of a regular sex sound, 8% chance of something sexy with words
                if random.random() > 0.92:
                    broca.thread.queue_sound(
                        from_collection="sex_conversation",
                        intensity=STATE.sexual_arousal
                        * (
                            1.0
                            + STATE.jostled_level_short
                            / self.gyro_jackup_intensity_max
                        ),
                        play_no_wait=True,
                    )
                else:
                    broca.thread.queue_sound(
                        from_collection="sex",
                        intensity=STATE.sexual_arousal
                        * (
                            1.0
                            + STATE.jostled_level_short
                            / self.gyro_jackup_intensity_max
                        ),
                        play_no_wait=True,
                    )

        # the only other thing it could be is a hangout, dick not moving type of situation
        # not sure what I really want in this situation, but a low intensity moan seems ok for now
        else:
            broca.thread.queue_sound(from_collection="sex", intensity=0.2)


# Instantiate and start the thread
thread = Sex()
thread.daemon = True
thread.start()

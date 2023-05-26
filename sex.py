"""
Handles sexual responses
"""
import time
import random
import threading

import log
from status import SHARED_STATE
import breath
import sleep


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
        self.multiplier_increment = 0.018

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

        # after wife orgasms, I want to monitor the gyro a while. When it's dead for a while, assume we're done.
        self.gyro_deadzone_after_orgasm = 0.03

        # bringing the gyro short term jostled reading into the bedroom.
        # When I'm banging her hard this will jack up the intensity of sex sounds.
        # this represents the highest expected jostled amount as observed in the wild
        # So at max it will double the intensity of sounds, and at min (0.0) it will leave the intensity alone
        self.gyro_jackup_intensity_max = 0.45

    def run(self):
        log.sex.debug("Thread started.")

        try:
            while True:
                # graceful shutdown
                if SHARED_STATE.please_shut_down:
                    break

                log.sex.debug(
                    "SexualArousal = %.2f  Multiplier: %.2f",
                    SHARED_STATE.sexual_arousal,
                    self.multiplier,
                )

                # Has sex stopped for a while?
                if SHARED_STATE.sexual_arousal == self.last_arousal:
                    self.arousal_stagnant_count += 1
                else:
                    self.arousal_stagnant_count = 0
                    self.last_arousal = SHARED_STATE.sexual_arousal

                # If there's been no vagina hits for a period of time, we must be done, reset all
                if self.arousal_stagnant_count >= self.seconds_to_reset:
                    log.sex.info("Arousal stagnated and was reset")
                    self.arousal_stagnant_count = 0
                    SHARED_STATE.sexual_arousal = 0.0
                    self.multiplier = 1.0

                # if we are currently OOOOOO'ing, then I want to figure out when we're done, using the gyro
                if SHARED_STATE.sexual_arousal > self.arousal_to_orgasm:
                    log.sex.debug(
                        "JostledShortTermLevel: %.2f", SHARED_STATE.jostled_level_short
                    )

                    # if we are not getting jostled that means we're done.
                    # However, this one time I came inside her but she wasn't done, because she's so fucking hot,
                    # and so I helped her get off with my finger, and then she just said "wow" and was done
                    # because she wasn't getting jostled
                    # so I added a condition to fix that, hope it works.
                    if (
                        SHARED_STATE.jostled_level_short
                        < self.gyro_deadzone_after_orgasm
                        and SHARED_STATE.sexual_arousal > 1.05
                    ):
                        log.sex.debug("Orgasm complete")
                        SHARED_STATE.horny = 0.0
                        SHARED_STATE.sexual_arousal = self.arousal_post_orgasm
                        # self.Multiplier = 1.0   trying not resetting this (oh yeah baby, tried it and now it stays)
                        breath.thread.queue_sound(
                            from_collection="sex_done",
                            play_ignore_speaking=True,
                            priority=9,
                        )

                # If we're to a certain point, start incrementing to ensure wife will cum eventually with enough time
                # Just Keep Fucking, Just Keep Fucking
                elif SHARED_STATE.sexual_arousal > 0.2:
                    self.multiplier += self.multiplier_increment

                time.sleep(1)

        # log exception in the main.log
        except Exception as ex:
            log.main.error(
                "Thread died. {0} {1} {2}".format(
                    ex.__class__, ex, log.format_tb(ex.__traceback__)
                )
            )

    def vagina_got_hit(self, sensor_data):
        """
        As the class member passes by through the secure tunnel,
        the capacitance of the organic machine is added to the
        total capacitance of the circuit, resulting in a
        signal to the inorganic machine and a response.
        """
        if SHARED_STATE.shush_please_honey is False:
            # Stay awake
            sleep.thread.wake_up(0.001)

            if sensor_data["msg"] in ["touch", "release"]:
                # which sensor got hit?
                sensor_hit = sensor_data["data"]

                # Add some to the arousal
                SHARED_STATE.sexual_arousal += (
                    self.base_arousal_per_vag_hit[sensor_hit] * self.multiplier
                )
                # Disabling the clip due to stagnation issue at 1.00
                # SHARED_STATE.SexualArousal = float(np.clip(SHARED_STATE.SexualArousal, 0.0, 1.0))

                log.sex.info(
                    "Vagina Got Hit (%s)  SexualArousal: %.2f  Multiplier: %.2f",
                    sensor_data,
                    SHARED_STATE.sexual_arousal,
                    self.multiplier,
                )

                # My wife orgasms above 0.95
                # If this is O #6 or something crazy like that, tend to reset it lower
                if SHARED_STATE.sexual_arousal > self.arousal_to_orgasm:
                    log.sex.info("I am coming!")
                    breath.thread.queue_sound(
                        from_collection="sex_climax",
                        play_ignore_speaking=True,
                        play_no_wait=True,
                        priority=8,
                    )
                elif SHARED_STATE.sexual_arousal > self.arousal_near_orgasm:
                    breath.thread.queue_sound(
                        from_collection="sex_near_O",
                        play_ignore_speaking=True,
                        play_no_wait=True,
                        priority=8,
                    )  # why was this here CutAllSoundAndPlay=True, oh, that's why, duh
                else:
                    # 92% chance of a regular sex sound, 8% chance of something sexy with words
                    if random.random() > 0.92:
                        breath.thread.queue_sound(
                            from_collection="sex_conversation",
                            intensity=SHARED_STATE.sexual_arousal
                            * (
                                1.0
                                + SHARED_STATE.jostled_level_short
                                / self.gyro_jackup_intensity_max
                            ),
                            play_no_wait=True,
                            play_ignore_speaking=True,
                            priority=8,
                        )
                    else:
                        breath.thread.queue_sound(
                            from_collection="breathe_sex",
                            intensity=SHARED_STATE.sexual_arousal
                            * (
                                1.0
                                + SHARED_STATE.jostled_level_short
                                / self.gyro_jackup_intensity_max
                            ),
                            play_ignore_speaking=True,
                            play_no_wait=True,
                            priority=8,
                        )

            # the only other thing it could be is a hangout, dick not moving type of situation
            # not sure what I really want in this situation, but a low intensity moan seems ok for now
            else:
                breath.thread.queue_sound(
                    from_collection="breathe_sex",
                    intensity=0.2,
                    play_ignore_speaking=True,
                    priority=7,
                )


# Instantiate and start the thread
thread = Sex()
thread.daemon = True
thread.start()

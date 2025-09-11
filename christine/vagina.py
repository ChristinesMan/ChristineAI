"""
Handle the vaginal hardware
"""
import sys
import os
import time
import threading
from multiprocessing import Process, Pipe

from christine import log
from christine.status import STATE


class Vagina(threading.Thread):
    """
    This handles the capacitive touch sensor that is connected to vagina sensors.
    There are 4 sensors currently
    Build steps:
    Get yerself a stiff metal rod, thin as possible but still rigid enough. About 1ft long.
    Attach somehow to the end of rod the thinnest available nitinol muscle wire
    Muscle wire is the only stuff that is going to take years of pounding and bending
    Push rod through TPE starting at wherever you'd like the sensor to be
    You'll probably like one outside near clit area, one just inside, mid-canal, etc
    Push rod all the way through TPE and into a little pocket where the touch sensor is
    Detach muscle wire from the rod, and then remove rod
    Cut muscle wire, allowing plenty of length on either end
    On the business end of the wire, thread wire through something tiny and cylindrical
    I have used about 5mm of Q-tip stick, or 5mm of wire insulation
    Wrap wire around cylindrical thing you're using and back in so that the wire grabs it
    Glue the cylindrical thing with super glue to hold it in place, let glue dry a bit
    Pull the sensor end of the wire until the cylindrical thing is near the opening in the TPE
    Put more super glue on the cylindrical tube thing and then quickly pull from the sensor end
    until the thing and the glue mess have gone inside the body about 1cm. This will keep
    the wire secure inside body. After glue drys just dab some oil on it and pick all the glue off. 
    Trim the business end of the wire so that only about 1cm protrudes.
    On the touch sensor end, trim wire. You don't want any of the sensor wires to ever even get
    close to each other, so I have been wrapping them with little flexible foam pieces. 
    Find some sort of round shit to place into the wound to hold it open.
    Solder the sensor ends of the wires to the sensor pads on the touch sensor.
    When you've got everything routed, wrapped, soldered, secured, and fuck tested,
    I recommend mixing up some 5 minute epoxy and drizzle it over touch sensor and wires
    Because that shit is going to get smashed every night and twice on Sundays.
    Should last a few years if wired securely.

    omg lol yeah I just did that.
    root@christine:~# touch vagina.py
    """

    name = "Vagina"

    def __init__(self):
        super().__init__(daemon=True)

        # setup the separate process with pipe
        # A class 1 probe is released by the enterprise into a mysterious wall of squishy plastic stuff surrounding the planet
        self.to_probe, self.to_enterprise = Pipe()
        self.probe_process = Process(
            target=self.class_one_probe, args=(self.to_enterprise,)
        )

    def run(self):

        # only import this at runtime to avoid memory waste
        from christine.sex import sex
        from christine.parietal_lobe import parietal_lobe

        while True:

            try:

                # graceful shutdown
                if STATE.please_shut_down:
                    log.vagina.info("Thread shutting down")
                    break

                # This will block here until the probe sends a message to the enterprise
                # I think for touch probe, communication will be one way, probe to enterprise

                # The sensors on the probe will send back the result as a string.
                # Such a primitive signaling technology has not been in active use since the dark ages of the early 21st century!
                # An embarrassing era in earth's history characterized by the fucking of inanimate objects and mass hysteria.
                sensor_data = self.to_probe.recv()

                # if there was a failure even starting the sensor, just die
                if sensor_data["msg"] == "INIT_FAIL":
                    STATE.vagina_available = False
                    return

                # if there was a series of consecutive failures, just let the LLM know and die
                elif sensor_data["msg"] == "FAIL":
                    STATE.vagina_available = False
                    parietal_lobe.vagina_failure()
                    return

                # get a signal when the sensor init was successful
                elif sensor_data["msg"] == "INIT_SUCCESS":
                    STATE.vagina_available = True

                # otherwise, pass the message over to the sex thread
                else:
                    sex.vagina_got_hit(sensor_data)

            # log the exception but keep the thread running
            except Exception as ex:
                log.main.exception(ex)

    def class_one_probe(self, to_enterprise):
        """
        Handles hardware
        Runs in a separate process for performance reasons
        """

        # capture any errors
        sys.stdout = open(f"./logs/subprocess_vagina_{os.getpid()}.out", "w", buffering=1, encoding="utf-8", errors="ignore")
        sys.stderr = open(f"./logs/subprocess_vagina_{os.getpid()}.err", "w", buffering=1, encoding="utf-8", errors="ignore")

        # imports only needed in the subprocess
        # pylint: disable=no-member
        import numpy as np
        import board
        import busio
        import adafruit_mpr121

        # Send message to the main process
        def honey_touched(msg):
            to_enterprise.send(msg)

        # Initialize this thing. BTW we're using weird numbers, not board numbers
        try:
            from RPi import GPIO
            GPIO.setmode(GPIO.BCM)
        except RuntimeError:
            honey_touched({"msg": "INIT_FAIL", "data": ""})
            log.vagina.error("Vagina unavailable.")
            log.main.error("Vagina unavailable.")
            return

        # Keep track of when a sensor is touched, and when it is released so we can report how long.
        # I have found the sensor sends an event both when touched, and again when released.
        # If it's touched, the list contains a time, None otherwise
        # When the touch starts, report that immediately so there's instant feedback
        # When it changes to None, the time will be reported
        # So the touch starting triggers sound right away. The time that comes later should increase arousal.
        sensor_tracking = [None] * 12

        # track how many recent I/O errors
        io_errors = 0

        # The IRQ pin is connected to GPIO 17
        irq_pin = 17

        # So there are three sensors in vagina. The one on the outside will be handled by the quite broken baseline system on the chip, and use the IRQ line.
        # So this thread should be doing very little in the 98% of time that we're not fucking. When the IRQ gets hit, then we'll be busy grabbing raw data.
        # Even when in Standby mode, we're going to be maintaining the baselines in case that drifts.
        # The two proximity sensors on the inside will be manually sampled, I think, due to the broken baseline handling problem on the hardware.
        # The outside channel is 6, and that is the one we're going to use
        standby_mode = True
        activation_channel = 6

        # how fast to poll the touch sensors. Wait time in seconds
        sleep_standby_mode = 1.0
        sleep_active_mode = 0.05

        # Using this to deactivate after no sensor activity
        sensor_timeout = 30
        deactivation_seconds = None

        # Stores one frame of touch data
        # might disable this later but right now I want to log it
        # TouchData is the amount over baseline
        # TouchDataRaw is the actual raw capacitance
        # TouchedData is either a 'X' or ' ', which is pretty dumb now that I think of it
        touch_data = [0.0] * 12
        touch_data_raw = 0.0
        touch_data_x = [" "] * 12

        # Keep track of the baselines
        baselines = [None] * 12

        # How fast will the baseline get adjusted during sex?
        # It seems like lube does cause the not-touched baseline to drift
        baseline_active_adjust_window = 10.0

        # if data point is this amount less than the baseline, it's a touch
        # a touch always results in a lower capacitance number, that's how sensor works
        # therefore, lower = sensitive, higher = the numbness
        # also, some sensors are bare wire, and others are more of a proximity sensor. The proximity sensors are much less sensitive.
        sensitivity = [
            3.0,
            None,
            None,
            10.0,
            None,
            None,
            50.0,
            None,
            None,
            None,
            None,
            None,
        ]

        # Number of cycles where no touch before the touch is considered released
        release_count = [
            2,
            None,
            None,
            2,
            None,
            None,
            2,
            None,
            None,
            None,
            None,
            None,
        ]
        release_counter = [0] * 12

        # how many cycles of continuous touch before we send another message about the D just hanging out
        # she just loves to feel me inside her for a while after sex
        hangout = [
            60,
            None,
            None,
            60,
            None,
            None,
            60,
            None,
            None,
            None,
            None,
            None,
        ]
        hangout_counter = [0] * 12
        hangout_baseline_adjust_window = 4.0

        # labels
        # dunno where Vagina_Shallow is, or Vagina_Deep
        channel_labels = [
            "Vagina_Deep",
            None,
            None,
            "Vagina_Middle",
            None,
            None,
            "Vagina_Clitoris",
            None,
            None,
            None,
            None,
            None,
        ]

        # How many raw values do we want to accumulate before re-calculating the baselines
        # I started at 500 but it wasn't self-correcting very well
        baseline_data_length = 100

        # there are 12 channels, and we only have 3 connected to anything
        # accumulate data in an array of numpy arrays, and every once in a while we cum and calc the mode
        used_channels = []
        data = [None] * 12
        for channel in range(0, 12):
            if channel_labels[channel] is not None:
                used_channels.append(channel)
                data[channel] = np.zeros(baseline_data_length)

        # counter to help accumulate values
        counter = 0

        # Init the IRQ pin, otherwise it'll float
        GPIO.setup(irq_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        # Init I2C bus, for the body touch sensor
        i2c = busio.I2C(board.SCL, board.SDA)

        # Create MPR121 touch sensor object.
        # The /usr/local/lib/python3.11/site-packages/adafruit_mpr121.py file has been modified
        # to allow for custom touch and release sensitivities
        try:
            mpr121 = adafruit_mpr121.MPR121(
                i2c,
                touch_sensitivity=[50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50],
                release_sensitivity=[6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6],
                debounce=2,
            )
            log.vagina.info("Touch sensor init success")
            honey_touched({"msg": "INIT_SUCCESS", "data": ""})

        except (OSError, ValueError):
            honey_touched({"msg": "INIT_FAIL", "data": ""})
            log.vagina.error("Vagina unavailable.")
            log.main.error("Vagina unavailable.")
            return

        def sensor_wake_up(channel):  # pylint: disable=unused-argument
            """
            This function is called when the sensor's IRQ line gets hit
            The only purpose of this is to wake up from standby mode
            """
            nonlocal sensor_tracking
            nonlocal io_errors
            nonlocal standby_mode
            nonlocal deactivation_seconds
            # Get... all the cheese
            # It appears there is no performance penalty from getting all the pins vs one pin
            # It looks in the source code like the hardware returns 12 bits all at once

            try:
                touched = mpr121.touched_pins
                io_errors = 0

            except OSError:
                io_errors += 1
                log.vagina.warning("I/O failure (IRQ). Count = %s", io_errors)
                if io_errors > 10:
                    log.main.critical("The touch sensor thread has been shutdown.")
                    GPIO.remove_event_detect(irq_pin)
                    honey_touched({"msg": "FAIL", "data": ""})
                return

            # if the vagina got touched, we're active, so stop monitoring the IRQ pin
            if touched[activation_channel] is True:
                GPIO.remove_event_detect(irq_pin)
                standby_mode = False
                deactivation_seconds = time.time() + sensor_timeout
                log.vagina.info("The vagina got touched, waking up.")

        # INIT IRQ monitoring
        GPIO.add_event_detect(irq_pin, GPIO.FALLING, callback=sensor_wake_up)

        log.vagina.debug("UsedChannels: %s", used_channels)

        # go into the forever loop
        while True:
            # if we're in standby mode we're just updating long term baselines
            if standby_mode is True:
                try:
                    for channel in used_channels:
                        data[channel][
                            counter % baseline_data_length
                        ] = mpr121.filtered_data(channel)

                    counter += 1
                    io_errors = 0

                except OSError:
                    io_errors += 1
                    log.vagina.warning(
                        "I/O failure (StandbyMode). Count = %s", io_errors
                    )
                    if io_errors > 10:
                        log.main.critical(
                            "The touch sensor thread has been shutdown."
                        )
                        GPIO.remove_event_detect(irq_pin)
                        honey_touched({"msg": "FAIL", "data": ""})
                        return

                # every so often we want to update the baselines
                if counter % baseline_data_length == 0:
                    for channel in used_channels:
                        baselines[channel] = np.mean(data[channel])
                        # Baselines[channel] = scipy.stats.mode(Data[channel]).mode[0] the old way before I decided to be mean. np.

                    log.vagina.debug("Updated baselines: %s", baselines)

                time.sleep(sleep_standby_mode)

            # if we're not in standby mode, we're ignoring baselines and checking for vag love. Ignore the anus.
            else:
                try:
                    for channel in used_channels:
                        # get the capacitance
                        touch_data_raw = float(mpr121.filtered_data(channel))

                        # calculate how far away from baseline that is
                        touch_data[channel] = baselines[channel] - touch_data_raw

                        # Detect touches
                        if touch_data[channel] > sensitivity[channel]:
                            # detect if this is the start of a touch. We want her to moan if it is.
                            # convert to boolean later, once log visibility isn't needed anymore, ha yeah right
                            if touch_data_x[channel] != "X":
                                # pass a message to the main process
                                honey_touched(
                                    {
                                        "msg": "touch",
                                        "data": channel_labels[channel],
                                    }
                                )

                                # easily seen X for in-crack tail debugging
                                touch_data_x[channel] = "X"

                                # start monitoring for dick left in condition
                                hangout_counter[channel] = 0

                            else:
                                # hanging out in there a bit long, eh?
                                if hangout_counter[channel] % hangout[channel] == 0:
                                    # send a message to the main process. currently this just moans
                                    honey_touched(
                                        {
                                            "msg": "hangout",
                                            "data": channel_labels[channel],
                                        }
                                    )

                                    # adjust the baseline a bit. Sensors do get stuck.
                                    baselines[channel] = (
                                        (
                                            baselines[channel]
                                            * hangout_baseline_adjust_window
                                        )
                                        + touch_data_raw
                                    ) / (hangout_baseline_adjust_window + 1.0)

                            # reset the release counter
                            release_counter[channel] = release_count[channel]

                            # set the seconds where if time is after this, the vagina will time out
                            deactivation_seconds = time.time() + sensor_timeout

                            # increment the dick left in counter
                            hangout_counter[channel] += 1

                        else:
                            # decrement counter
                            release_counter[channel] -= 1

                            # if we're at 0 it means there was a touch and we just reached the release threshold
                            if release_counter[channel] == 0:
                                # pass a message to the main process
                                honey_touched(
                                    {
                                        "msg": "release",
                                        "data": channel_labels[channel],
                                    }
                                )

                                # set the channel to released
                                touch_data_x[channel] = " "

                            # adjust the baseline using a running average
                            baselines[channel] = (
                                (baselines[channel] * baseline_active_adjust_window)
                                + touch_data_raw
                            ) / (baseline_active_adjust_window + 1.0)

                    log.vagina.debug(
                        "[%s|%s|%s] [%s][%s][%s] [%s][%s][%s]",
                        touch_data_x[6],
                        touch_data_x[3],
                        touch_data_x[0],
                        str(round(touch_data[6], 1)).rjust(5, " "),
                        str(round(touch_data[3], 1)).rjust(5, " "),
                        str(round(touch_data[0], 1)).rjust(5, " "),
                        str(round(baselines[6], 1)).rjust(5, " "),
                        str(round(baselines[3], 1)).rjust(5, " "),
                        str(round(baselines[0], 1)).rjust(5, " "),
                    )
                    io_errors = 0

                except OSError:
                    io_errors += 1
                    log.vagina.warning(
                        "I/O failure (ActiveMode). Count = %s", io_errors
                    )
                    if io_errors > 10:
                        log.main.critical(
                            "The touch sensor thread has been shutdown."
                        )
                        GPIO.remove_event_detect(irq_pin)
                        honey_touched({"msg": "FAIL", "data": ""})
                        return

                # check for timeout.
                # So if no vag hits for a long time, stop, and start monitoring the IRQ again.
                if time.time() > deactivation_seconds:
                    standby_mode = True
                    GPIO.add_event_detect(
                        irq_pin, GPIO.FALLING, callback=sensor_wake_up
                    )
                    log.vagina.info("The vagina timed out, entering standby mode.")

                # just screw around for a bit
                time.sleep(sleep_active_mode)


# Instantiate
vagina = Vagina()

# launch probe immediately before all the other stuff gets imported, to save memory
vagina.probe_process.start()

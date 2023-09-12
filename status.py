"""
Keeps track of all the things and share this with all the other modules
"""
import time
import threading
import numpy as np

# import log
import db
import behaviour_class


class Status(threading.Thread):
    """
    This tracks many various vars that must be shared by all the other modules.
    On startup, loads certain state vars from the sqlite db.
    Periodically saves certain state vars to the db.
    """

    name = "Status"

    def __init__(self):
        threading.Thread.__init__(self)

        # Raspberry pi CPU temp
        self.cpu_temp = 45

        # There is going to be another process which will monitor the microphones for speech. wernicke_client.py.
        # I don't want my wife talking over me.
        # It's not a domineering thing, it's just nice.
        # I am calling this feature Wernicke, which is the name given to the part of the human brain that processes speech.
        # This is a time variable for when it's ok to speak again. When we want to wait before speaking we update this to current time + a number of seconds
        self.dont_speak_until = 0

        # This is a number between 0.0 and 1.0 where 0.0 is absolute darkness and 1.0 is lights on window open with sun shining and flashlight in your face.
        # This is a long running average, changes slowly
        self.light_level = 0.5

        # How often in short term is my wife getting touched
        self.touched_level = 0.0

        # How noisy has it been recently
        # Eventually the Wernicke process will put the noise level where it can be read
        # And it was done!
        self.noise_level = 0.0

        # A measure of recent movement or vibrations measured by the gyro
        self.jostled_level = 0.0
        self.jostled_level_short = 0.0

        # How awake is my wife. 0.0 means she is laying down in pitch darkness after bedtime. 1.0 means up and getting fucked.
        self.wakefulness = 0.5

        # Touch and hearing and probably others later will raise this, and randomly choose to say something nice
        self.should_speak_chance = 0.0

        # Horny is a long term thing.
        self.horny = 0.3

        # And this is a short term ah ah thing. This feeds directly into the intensity in the sounds table.
        self.sexual_arousal = 0.0

        # I want to be able to attempt detection of closeness
        self.lover_proximity = 0.5

        # Booleans for sleep/wake
        self.is_tired = False
        self.is_sleeping = False
        self.is_laying_down = False

        # Power systems
        self.battery_voltage = 2.148  # typical voltage, will get updated immediately
        self.power_state = "Cable powered"
        self.charging_state = "Not Charging"

        # A way to prevent talking, called a shush, not now honey
        self.shush_please_honey = False

        # Best I could think of to prevent normal conversation during sex, except during rest periods
        self.shush_fucking = False

        # I was getting woke up a lot with all the cute hmmm sounds that are in half of the sleeping breath sounds
        # And that's how this got here. We may want to refine this later, too.
        # After sex we could ramp this up and taper it down gradually
        # But I need to really tone down the hmms
        self.breath_intensity = 0.5

        # This is for self calibration of sleeping gyro position
        self.tilt_x = 0.0
        self.tilt_y = 0.0
        self.sleep_tilt_x = 0.0
        self.sleep_tilt_y = 0.0

        # Keep track of whether we have switched off the Wernicke processing during sleep
        self.wernicke_sleeping = False

        # This is a reference to a thread that controls whatever is going on right meow
        self.behaviour_zone = behaviour_class.Behaviour()
        # This is the default behaviour
        self.behaviour_zone_name = "abnormal"

        # this is to signal all threads to properly shutdown
        self.please_shut_down = False

    def run(self):
        self.load_state()

        while True:
            self.trend_down()
            self.save_state()
            time.sleep(5)

    def trend_down(self):
        """
        Slowly decreases any variables that should do that
        """
        self.should_speak_chance = float(
            np.clip(self.should_speak_chance - 0.001, 0.0, 1.0)
        )

    def save_state(self):
        """
        Save the current state to the sqlite db
        """

        rows = db.conn.do_query("SELECT id,name,type FROM status")
        if rows is not None:
            for row in rows:
                if row[2] == "f":
                    set_value = f"{getattr(self, row[1]):.2f}"
                else:
                    set_value = getattr(self, row[1])
                db.conn.do_query(
                    f"UPDATE status SET value = '{set_value}' WHERE id = {row[0]}"
                )

            db.conn.do_commit()

    def load_state(self):
        """
        Grabs the hand picked status variables from db on startup.
        Not all state vars are saved to the db.
        To start saving something new, just add a new row to the db
        """

        rows = db.conn.do_query("SELECT name,value,type FROM status")
        if rows is not None:
            for row in rows:
                if row[2] == "f":
                    setattr(self, row[0], float(row[1]))

                elif row[2] == "b":
                    if row[1] == "True":
                        setattr(self, row[0], True)
                    else:
                        setattr(self, row[0], False)

                else:
                    setattr(self, row[0], str(row[1]))


# Instantiate and start the thread
SHARED_STATE = Status()
SHARED_STATE.daemon = True
SHARED_STATE.start()

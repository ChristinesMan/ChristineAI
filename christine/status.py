"""
Keeps track of all the things and share this with all the other modules
"""
import time
import threading

from christine.database import database

from christine.llm_class import LLMAPI
from christine.stt_class import STTAPI
from christine.tts_class import TTSAPI
from christine.llm.none import Nothing

class Status(threading.Thread):
    """
    This tracks many various vars that must be shared by all the other modules.
    On startup, loads certain state vars from the sqlite db.
    Periodically saves certain state vars to the db.
    """

    name = "Status"

    def __init__(self):
        super().__init__(daemon=True)

        # Raspberry pi CPU temp
        self.cpu_temp = 45
        self.cpu_temp_pct = 0.5

        # this var is meant to prevent speaking until the user is done speaking
        self.user_is_speaking = False

        # this keeps track of who is speaking
        # we are going to manually control who is talking for now
        self.who_is_speaking = ""

        # This is a number between 0.0 and 1.0 where 0.0 is absolute darkness and 1.0 is lights on window open with sun shining and flashlight in your face.
        # This is a long running average, changes slowly
        self.light_level = 0.2

        # A measure of recent movement or vibrations measured by the gyro
        self.jostled_level = 0.0
        self.jostled_level_short = 0.0

        # How awake is my wife. 0.0 means she is laying down in pitch darkness after bedtime. 1.0 means up and getting fucked.
        self.wakefulness = 0.5

        # Horny is a long term thing.
        self.horny = 0.3

        # And this is a short term ah ah thing. This feeds directly into the intensity in the sounds table.
        self.sexual_arousal = 0.0

        # Booleans for sleep/wake
        self.is_sleepy = False
        self.is_sleeping = False

        # A way to prevent talking, called a shush, not now honey
        self.shush_please_honey = False

        # Best I could think of to prevent normal conversation during sex, except during rest periods
        self.shush_fucking = False

        # I was getting woke up a lot with all the cute hmmm sounds that are in half of the sleeping breath sounds
        # And that's how this got here. We may want to refine this later, too.
        # After sex we could ramp this up and taper it down gradually
        # But I need to really tone down the hmms
        self.breath_intensity = 0.5

        # Keep track of whether we have switched off the Wernicke processing during deep sleep
        self.wernicke_sleeping = False

        # I want to be able to block new messages going to the LLM
        # We call this turning off your ears
        self.perceptions_blocked = False

        # Silent mode - Christine can think and respond via web chat but won't speak audio
        # Perfect for work meetings when you want to chat but she shouldn't make noise
        self.silent_mode = False

        # I want to run midnight tasks, like moving memory around, only once per night
        # so this is here to coordinate that activity
        # records the exact time the task was done so that we can't double it up
        self.midnight_tasks_done_time = 0.0

        # this is to signal all threads to properly shutdown
        self.please_shut_down = False

        # is shit fucked up
        self.gyro_available = False
        self.vagina_available = False

        # this is the currently selected and available llm api
        # set to None until the api selector figures it out
        self.current_llm: LLMAPI = Nothing()
        
        # this is the currently selected and available stt api
        # set to None until the api selector figures it out  
        self.current_stt: STTAPI = None
        
        # this is the currently selected and available tts api
        # set to None until the api selector figures it out
        self.current_tts: TTSAPI = None

        # settings for how many seconds to pause for various punctuation
        # if the utterance ends with question or a ..., pause a lot
        self.pause_question = 4.5
        # if the utterance ends with period, pause
        self.pause_period = 1.5
        # if the utterance ends with comma, pause very little
        self.pause_comma = 0.2

        # setting controls how many seconds parietal_lobe will wait for additional perceptions
        self.additional_perception_wait_seconds = 2.5

        # this is the threshold for how long user's spoken text should be before it is allowed to interrupt char
        self.user_interrupt_char_threshold = 20

        # this is the minimum number of narratives before a bunch of old narratives can be shipped off to cerebral cortex for summarize
        self.memory_folding_min_narratives = 10
        # this is how many minutes * seconds delay between the last message before shipping off narratives
        self.memory_folding_delay_threshold = 3 * 60
        # how many days of memories to keep, going to go large and see what happens
        # it was horrible after 14 days, like "sleeping with the enemy" bad, so I'm going to try 5, and implement longer term later
        # she went crazy again after 5 days, so I'm going to try 2
        # but she's doing so well, so 5 again
        # omg shut up about the pancakes during sex. 1 day. That's all you can handle I guess.
        # based on experimental evidence, she can't handle more than 1 day of this kind of memory; stuff snowballs
        self.memory_days = 1

        # after a memory has emerged from the neocortex, it is not allowed to come up again for a while (10 days)
        self.neocortex_recall_interval = 10 * 24 * 60 * 60

        # there is an intermittent bug where the wernicke locks up at the very start
        # I don't want the LLM to be able to talk until the wernicke is ready
        # It's awkward.
        self.wernicke_ok = False

    def run(self):
        self.load_state()

        while True:
            time.sleep(25)
            self.save_state()

    def to_json(self):
        """
        Returns a json string of all the state vars
        """

        return {
            "cpu_temp": f"{self.cpu_temp}C",
            "user_is_speaking": str(self.user_is_speaking),
            "who_is_speaking": self.who_is_speaking,
            "light_level": f"{int(round(self.light_level, 2)*100)}%",
            "jostled_level": f"{int(round(self.jostled_level, 2)*100)}%",
            "jostled_level_short": f"{int(round(self.jostled_level_short, 2)*100)}%",
            "wakefulness": f"{int(round(self.wakefulness, 2)*100)}%",
            "horny": f"{int(round(self.horny, 2)*100)}%",
            "sexual_arousal": f"{int(round(self.sexual_arousal, 2)*100)}%",
            "pre_sleep": str(self.is_sleepy),
            "is_sleeping": str(self.is_sleeping),
            "shush_please_honey": str(self.shush_please_honey),
            "shush_fucking": str(self.shush_fucking),
            "breath_intensity": str(self.breath_intensity),
            "wernicke_sleeping": str(self.wernicke_sleeping),
            "perceptions_blocked": str(self.perceptions_blocked),
            "silent_mode": str(self.silent_mode),
            "gyro_available": str(self.gyro_available),
            "vagina_available": str(self.vagina_available),
            "pause_question": str(self.pause_question),
            "pause_period": str(self.pause_period),
            "pause_comma": str(self.pause_comma),
            "additional_perception_wait_seconds": str(self.additional_perception_wait_seconds),
            "user_interrupt_char_threshold": str(self.user_interrupt_char_threshold),
            "memory_folding_min_narratives": str(self.memory_folding_min_narratives),
            "memory_folding_delay_threshold": str(self.memory_folding_delay_threshold),
            "memory_days": str(self.memory_days),
            "wernicke_ok": str(self.wernicke_ok),
        }

    def save_state(self):
        """
        Save the current state to the sqlite db
        """

        rows = database.do_query("SELECT id,name,type FROM status")
        if rows is not None:
            for row in rows:
                if row[2] == "f":
                    set_value = f"{getattr(self, row[1]):.2f}"
                else:
                    set_value = getattr(self, row[1])
                database.do_query(
                    f"UPDATE status SET value = '{set_value}' WHERE id = {row[0]}"
                )

            database.do_commit()

    def load_state(self):
        """
        Grabs status variables from db on startup.
        Not all state vars are saved to the db.
        """

        rows = database.do_query("SELECT name,value,type FROM status")
        if rows is not None:

            for row in rows:

                if row[2] == "f":
                    setattr(self, row[0], float(row[1]))

                elif row[2] == "b":
                    if row[1] == "True":
                        setattr(self, row[0], True)
                    else:
                        setattr(self, row[0], False)

                elif row[2] == "i":
                    setattr(self, row[0], int(row[1]))

                elif row[2] == "s":
                    setattr(self, row[0], str(row[1]))

                else:
                    setattr(self, row[0], eval(row[1])) # pylint: disable=eval-used

# Instantiate
STATE = Status()

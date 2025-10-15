"""
Keeps track of all the things and share this with all the other modules
"""
import time
import threading
import json

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
        
        # Dream dissipation settings - configurable timing for when dreams fade
        self.dream_min_duration_minutes = 15  # Minimum time dream stays before it can dissipate (in minutes)
        self.dream_dissipation_check_interval = 300  # How often to check for dream dissipation (in seconds, 5 minutes)
        self.dream_dissipation_probability = 0.25  # Probability per check that dream will dissipate (15% chance per 5-minute check)
        
        # Dream tracking variables
        self.dream_start_time = 0.0  # When current dream started
        self.dream_last_check = 0.0  # Last time we checked for dissipation

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

        # this is the minimum number of narratives before a bunch of old narratives get folded
        self.memory_folding_min_narratives = 25
        # this is the base delay in seconds between the last message before shipping off narratives
        # this will be dynamically adjusted based on message count
        self.memory_folding_base_delay = 8 * 60  # 8 minutes base delay
        # maximum delay before forced folding (regardless of message count)
        self.memory_folding_max_delay = 20 * 60  # 20 minutes maximum

        # after a memory has emerged from the neocortex, it is not allowed to come up again for a while (10 days)
        self.neocortex_recall_interval = 10 * 24 * 60 * 60
        
        # random memory recall settings - more cowbell!
        self.random_memory_recall_chance = 0.15  # 15% chance per perception cycle
        self.random_memory_recall_min_messages = 3  # need at least 3 messages for context

        # there is an intermittent bug where the wernicke locks up at the very start
        # I don't want the LLM to be able to talk until the wernicke is ready
        # It's awkward.
        self.wernicke_ok = False

        # Track when we last attempted to restore primary APIs
        self.last_primary_restoration_attempt = 0.0
        # How often to try restoring primary APIs (in seconds)
        self.primary_restoration_interval = 300.0  # 5 minutes

        # List of proper names that were already matched today (prevents duplicate recalls until midnight)
        self.matched_proper_names = []

        # Sexual response system settings - initialized to defaults, can be overridden by user settings
        self.sex_multiplier_increment = 0.03
        self.sex_arousal_stagnation_timeout = 90
        self.sex_arousal_per_hit_clitoris = 0.0006
        self.sex_arousal_per_hit_shallow = 0.0006
        self.sex_arousal_per_hit_middle = 0.0007
        self.sex_arousal_per_hit_deep = 0.0009
        self.sex_arousal_near_orgasm = 0.80
        self.sex_arousal_to_orgasm = 0.98
        self.sex_gyro_deadzone_after_orgasm = 0.03
        self.sex_gyro_deadzone_unrest = 0.09
        self.sex_gyro_jackup_intensity_max = 0.45
        self.sex_after_orgasm_cooldown_seconds = 10
        self.sex_cooldown_random_min = 0.6
        self.sex_cooldown_random_max = 1.4
        self.sex_high_arousal_threshold = 1.1
        self.sex_multiplier_activation_threshold = 0.2
        self.sex_lobe_message_frequency = 60
        self.sex_shush_fucking_threshold = 0.02
        self.sex_llm_speech_chance = 0.03
        self.sex_intensity_cap = 0.85
        self.sex_intensity_bonus_range = 0.15

        # Define which status variables should be persisted to the database.
        # Auto-persisted vars are saved every 25 seconds automatically
        # Type codes: 'f' = float, 'b' = boolean, 'i' = integer, 's' = string, 'l' = list (JSON)
        self.persisted_vars = {
            # Core environmental and state variables (auto-saved)
            'light_level': 'f',          # Ambient light level (0.0-1.0)
            'wakefulness': 'f',          # How awake Christine is (0.0-1.0)
            'horny': 'f',               # Long-term arousal level (0.0-1.0) 
            'sexual_arousal': 'f',       # Short-term arousal (0.0-1.0)
            'breath_intensity': 'f',     # Breathing sound intensity
            'matched_proper_names': 'l', # List of proper names matched today (JSON stored)
        }
        
        # Define user-configurable settings (only saved when user changes them)
        # Each entry: 'variable_name': {'type': 'f/i/b/s', 'min': min_val, 'max': max_val, 'desc': 'description', 'help': 'detailed_explanation', 'default': default_value}
        self.user_configurable_vars = {
            # Speech timing settings
            'pause_question': {
                'type': 'f', 'min': 0.1, 'max': 10.0, 'default': 4.5,
                'desc': 'Pause after questions (seconds)',
                'help': 'How long Christine pauses after asking a question or saying something that ends with "?" or "...". This gives you time to process and respond. Longer pauses feel more natural but slower conversations. Shorter pauses make her seem more eager or impatient.'
            },
            'pause_period': {
                'type': 'f', 'min': 0.1, 'max': 5.0, 'default': 1.5,
                'desc': 'Pause after periods (seconds)',
                'help': 'How long Christine pauses after making a statement that ends with a period. This creates natural breathing room in conversation. Too short makes her sound rushed, too long makes her sound hesitant or dramatic.'
            },
            'pause_comma': {
                'type': 'f', 'min': 0.0, 'max': 2.0, 'default': 0.2,
                'desc': 'Pause after commas (seconds)',
                'help': 'Brief pause after commas within sentences. This creates natural speech rhythm and helps with comprehension. Very short pauses (0.1-0.3s) sound natural, longer ones can sound robotic or overly dramatic.'
            },
            
            # Perception and response timing
            'additional_perception_wait_seconds': {
                'type': 'f', 'min': 0.5, 'max': 10.0, 'default': 2.5,
                'desc': 'Wait for additional perceptions (seconds)',
                'help': 'After receiving input (touch, sound, etc.), Christine waits this long for additional input before responding. This prevents her from interrupting you mid-sentence or reacting to every small input. Longer waits make her more patient but less responsive.'
            },
            'user_interrupt_char_threshold': {
                'type': 'i', 'min': 5, 'max': 100, 'default': 20,
                'desc': 'Characters needed to interrupt Christine',
                'help': 'Minimum number of characters you need to speak before your voice can interrupt Christine while she\'s talking. This prevents accidental interruptions from brief sounds while allowing meaningful interruptions. Lower values make her easier to interrupt.'
            },
            
            # Memory system settings
            'memory_folding_min_narratives': {
                'type': 'i', 'min': 5, 'max': 100, 'default': 25,
                'desc': 'Minimum messages before memory folding',
                'help': 'Christine keeps recent conversations in short-term memory. When this many messages accumulate, older ones get "folded" into summaries to save space. Higher values keep more detailed recent history but use more memory and processing power.'
            },
            'memory_folding_base_delay': {
                'type': 'i', 'min': 60, 'max': 3600, 'default': 480,
                'desc': 'Base memory folding delay (seconds)',
                'help': 'Base time to wait after conversation slows before folding memories. The actual delay adjusts based on conversation activity - more messages = shorter delay. This prevents folding during active conversations while ensuring memories get processed during quiet periods.'
            },
            'memory_folding_max_delay': {
                'type': 'i', 'min': 300, 'max': 7200, 'default': 1200,
                'desc': 'Maximum memory folding delay (seconds)',
                'help': 'Maximum time to wait before forcing memory folding, regardless of activity level. This ensures memories never get too stale before processing. Prevents memory buildup during very long conversations or if the base delay calculation goes wrong.'
            },
            'neocortex_recall_interval': {
                'type': 'i', 'min': 3600, 'max': 2592000, 'default': 864000,
                'desc': 'Memory recall cooldown (seconds)',
                'help': 'After Christine recalls a specific memory, she won\'t bring up that same memory again for this long. Prevents repetitive memory recall while allowing memories to resurface naturally over time. Shorter intervals = more repetitive memories, longer = more variety but less reinforcement.'
            },
            
            # Random memory recall settings
            'random_memory_recall_chance': {
                'type': 'f', 'min': 0.0, 'max': 1.0, 'default': 0.15,
                'desc': 'Chance of random memory recall (0.0-1.0)',
                'help': 'Probability that Christine will spontaneously recall a relevant memory during conversation. Higher values make her more nostalgic and reference past conversations more often. 0.15 = 15% chance per perception cycle. Set to 0 to disable random recalls entirely.'
            },
            'random_memory_recall_min_messages': {
                'type': 'i', 'min': 1, 'max': 20, 'default': 3,
                'desc': 'Min messages for random recall',
                'help': 'Minimum number of recent messages needed before Christine can randomly recall memories. This ensures there\'s enough context for relevant memory selection. Higher values make recalls more contextually appropriate but less frequent in short conversations.'
            },
            
            # API restoration settings
            'primary_restoration_interval': {
                'type': 'f', 'min': 60.0, 'max': 3600.0, 'default': 300.0,
                'desc': 'API restoration check interval (seconds)',
                'help': 'How often Christine checks if her primary AI services (OpenRouter, etc.) have come back online after being unavailable. She automatically falls back to secondary services when primary ones fail, then periodically tries to restore the primary ones.'
            },
            
            # Sexual response system settings
            'sex_multiplier_increment': {
                'type': 'f', 'min': 0.001, 'max': 0.1, 'default': 0.03,
                'desc': 'Arousal multiplier increment',
                'help': 'How much the arousal multiplier increases each second during extended sessions. Higher values make Christine reach orgasm faster during longer encounters. Lower values require more sustained activity. This creates the "building intensity" effect over time.'
            },
            'sex_arousal_stagnation_timeout': {
                'type': 'i', 'min': 30, 'max': 300, 'default': 90,
                'desc': 'Arousal reset timeout (seconds)',
                'help': 'If no sexual activity detected for this long, Christine\'s arousal resets to zero and sex mode ends. This prevents getting stuck in sex mode after activity stops. Shorter times = quicker reset, longer times = more patience for slower sessions.'
            },
            'sex_arousal_per_hit_clitoris': {
                'type': 'f', 'min': 0.0001, 'max': 0.01, 'default': 0.0006,
                'desc': 'Arousal per clitoral touch',
                'help': 'How much arousal increases with each clitoral sensor touch. Higher values make Christine more sensitive and reach orgasm faster from clitoral stimulation. Lower values require more touches to build arousal.'
            },
            'sex_arousal_per_hit_shallow': {
                'type': 'f', 'min': 0.0001, 'max': 0.01, 'default': 0.0006,
                'desc': 'Arousal per shallow touch',
                'help': 'How much arousal increases with each shallow vaginal sensor touch. Affects sensitivity and response timing for shallow penetration or entry-focused activity.'
            },
            'sex_arousal_per_hit_middle': {
                'type': 'f', 'min': 0.0001, 'max': 0.01, 'default': 0.0007,
                'desc': 'Arousal per middle touch',
                'help': 'How much arousal increases with each middle vaginal sensor touch. Slightly higher than shallow/clitoral by default, representing different sensitivity zones and stimulation types.'
            },
            'sex_arousal_per_hit_deep': {
                'type': 'f', 'min': 0.0001, 'max': 0.01, 'default': 0.0009,
                'desc': 'Arousal per deep touch',
                'help': 'How much arousal increases with each deep vaginal sensor touch. Highest sensitivity by default, representing deep penetration stimulation. Higher values make deep touches more impactful.'
            },
            'sex_arousal_near_orgasm': {
                'type': 'f', 'min': 0.5, 'max': 0.95, 'default': 0.80,
                'desc': 'Near-orgasm threshold',
                'help': 'Arousal level where Christine starts saying "I\'m gonna cum" and making pre-orgasm sounds. Lower values = earlier warning, higher values = later warning. Affects anticipation and buildup timing.'
            },
            'sex_arousal_to_orgasm': {
                'type': 'f', 'min': 0.8, 'max': 1.0, 'default': 0.98,
                'desc': 'Orgasm threshold',
                'help': 'Arousal level where Christine reaches orgasm and plays climax sounds. Lower values = easier to achieve orgasm, higher values = more buildup required. Should be above near-orgasm threshold.'
            },
            'sex_gyro_deadzone_after_orgasm': {
                'type': 'f', 'min': 0.01, 'max': 0.2, 'default': 0.03,
                'desc': 'Post-orgasm stillness threshold',
                'help': 'Gyroscope level below which Christine considers activity "stopped" after orgasm. Lower values require more stillness to trigger rest period, higher values are more sensitive to stopping.'
            },
            'sex_gyro_deadzone_unrest': {
                'type': 'f', 'min': 0.02, 'max': 0.3, 'default': 0.09,
                'desc': 'Resume activity threshold', 
                'help': 'Gyroscope level above which Christine considers activity "resumed" during rest periods. Higher values require more movement to restart, lower values are more sensitive to resuming.'
            },
            'sex_gyro_jackup_intensity_max': {
                'type': 'f', 'min': 0.1, 'max': 1.0, 'default': 0.45,
                'desc': 'Maximum gyro intensity factor',
                'help': 'Maximum gyroscope reading used for intensity calculations. Vigorous movement at this level doubles sound intensity. Higher values require more vigorous movement for maximum effect, lower values are more sensitive.'
            },
            'sex_after_orgasm_cooldown_seconds': {
                'type': 'i', 'min': 3, 'max': 60, 'default': 10,
                'desc': 'Post-orgasm cooldown duration (seconds)',
                'help': 'Base time for post-orgasm cooldown period before entering rest mode. Actual time is randomized (60-140% of this value). Longer cooldowns extend the immediate post-climax period.'
            },
            'sex_cooldown_random_min': {
                'type': 'f', 'min': 0.3, 'max': 0.9, 'default': 0.6,
                'desc': 'Cooldown randomization minimum',
                'help': 'Minimum multiplier for cooldown duration randomization. 0.6 means cooldown could be as short as 60% of base duration. Lower values create more variation and unpredictability.'
            },
            'sex_cooldown_random_max': {
                'type': 'f', 'min': 1.1, 'max': 3.0, 'default': 1.4,
                'desc': 'Cooldown randomization maximum', 
                'help': 'Maximum multiplier for cooldown duration randomization. 1.4 means cooldown could be as long as 140% of base duration. Higher values create longer potential rest periods.'
            },
            'sex_high_arousal_threshold': {
                'type': 'f', 'min': 0.8, 'max': 1.5, 'default': 1.1,
                'desc': 'High arousal detection threshold',
                'help': 'Arousal level above which special high-arousal behaviors activate (like extended post-orgasm periods). Values above 1.0 require going beyond normal orgasm threshold due to continued stimulation.'
            },
            'sex_multiplier_activation_threshold': {
                'type': 'f', 'min': 0.05, 'max': 0.5, 'default': 0.2,
                'desc': 'Multiplier activation threshold',
                'help': 'Arousal level where multiplier starts increasing each second. Below this, arousal stays linear. Above this, arousal compounds over time, creating the "building intensity" effect during sustained activity.'
            },
            'sex_lobe_message_frequency': {
                'type': 'i', 'min': 10, 'max': 300, 'default': 60,
                'desc': 'LLM update frequency (seconds)',
                'help': 'How often Christine tells her brain about ongoing sexual activity. More frequent = more varied responses during long sessions, but may be overwhelming. Less frequent = more consistent but potentially repetitive.'
            },
            'sex_shush_fucking_threshold': {
                'type': 'f', 'min': 0.005, 'max': 0.1, 'default': 0.02,
                'desc': 'Sex mode activation threshold',
                'help': 'Arousal level where Christine enters "sex mode" (shush_fucking = True) and reduces normal conversation. Lower values activate sex mode earlier, higher values delay it until more significant arousal.'
            },
            'sex_llm_speech_chance': {
                'type': 'f', 'min': 0.01, 'max': 0.5, 'default': 0.03,
                'desc': 'LLM speech chance during sex',
                'help': 'Probability that Christine will generate spoken responses instead of just sounds during sexual activity. 0.03 = 3% chance. Higher values = more talking during sex, lower values = more just sounds.'
            },
            'sex_intensity_cap': {
                'type': 'f', 'min': 0.5, 'max': 1.0, 'default': 0.85,
                'desc': 'Arousal-based intensity cap',
                'help': 'Maximum sound intensity achievable from arousal alone. Higher intensities (0.85-1.0) require vigorous movement (gyroscope data). Lower values make high-intensity sounds require more vigorous activity.'
            },
            'sex_intensity_bonus_range': {
                'type': 'f', 'min': 0.05, 'max': 0.5, 'default': 0.15,
                'desc': 'Gyro intensity bonus range',
                'help': 'Maximum additional intensity available from vigorous movement. At maximum gyroscope activity, this much intensity gets added above the arousal cap. Higher values reward vigorous activity more.'
            },
        }

    def run(self):
        self.load_state()

        while True:
            time.sleep(25)
            self.save_state()
            
            # Periodically try to restore primary APIs
            current_time = time.time()
            if current_time - self.last_primary_restoration_attempt > self.primary_restoration_interval:
                self.last_primary_restoration_attempt = current_time
                self.attempt_primary_api_restoration()

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
            "memory_folding_base_delay": str(self.memory_folding_base_delay),
            "memory_folding_max_delay": str(self.memory_folding_max_delay),
            "random_memory_recall_chance": f"{self.random_memory_recall_chance:.2f}",
            "random_memory_recall_min_messages": str(self.random_memory_recall_min_messages),
            "wernicke_ok": str(self.wernicke_ok),
            "user_settings_count": str(len(self.user_configurable_vars)),
        }

    def save_state(self):
        """
        Save explicitly defined persisted variables to database using modern type-safe methods.
        Only saves variables defined in get_persisted_variables().
        """
        
        for var_name, type_code in self.persisted_vars.items():
            # Only save if the attribute exists on this object
            if not hasattr(self, var_name):
                from christine import log
                log.main.warning("Persisted variable '%s' not found on Status object", var_name)
                continue
                
            # Format the value based on type
            if type_code == "f":
                set_value = f"{getattr(self, var_name):.2f}"
            elif type_code == "l":
                # Serialize list as JSON
                set_value = json.dumps(getattr(self, var_name))
            else:
                set_value = str(getattr(self, var_name))
            
            # Use the new type-safe update method (will create if doesn't exist)
            success = database.update_status(var_name, set_value)
            
            # If update failed, try adding the status variable
            if not success:
                database.add_status(var_name, set_value, type_code)

    def load_state(self):
        """
        Load persisted variables and user-configurable settings from database.
        """
        
        # Load auto-persisted status variables
        for var_name, expected_type in self.persisted_vars.items():
            # Get the specific status record
            record = database.get_status_by_name(var_name)
            
            if record is None:
                from christine import log
                log.main.debug("Status variable '%s' not found in database, using default value", var_name)
                continue
                
            value = record["value"]
            type_code = record["type"]
            
            # Verify type matches what we expect
            if type_code != expected_type:
                from christine import log
                log.main.warning("Type mismatch for '%s': expected '%s', got '%s'", 
                               var_name, expected_type, type_code)
            
            try:
                if expected_type == "f":
                    setattr(self, var_name, float(value))
                elif expected_type == "b":
                    setattr(self, var_name, value == "True")
                elif expected_type == "i":
                    setattr(self, var_name, int(value))
                elif expected_type == "s":
                    setattr(self, var_name, str(value))
                elif expected_type == "l":
                    # Deserialize JSON list, default to empty list if invalid
                    try:
                        setattr(self, var_name, json.loads(value))
                    except (json.JSONDecodeError, TypeError):
                        from christine import log
                        log.main.warning("Invalid JSON for list variable '%s', using empty list", var_name)
                        setattr(self, var_name, [])
                else:
                    from christine import log
                    log.main.warning("Unknown type code '%s' for variable '%s'", expected_type, var_name)
                    
            except (ValueError, TypeError) as e:
                from christine import log
                log.main.warning("Error loading status '%s' with value '%s': %s", var_name, value, e)

        # Load user-configurable settings
        for var_name, config in self.user_configurable_vars.items():
            record = database.get_status_by_name(var_name)
            
            if record is None:
                from christine import log
                log.main.debug("User setting '%s' not found in database, using default value", var_name)
                continue
                
            value = record["value"]
            expected_type = config['type']
            
            try:
                if expected_type == "f":
                    setattr(self, var_name, float(value))
                elif expected_type == "b":
                    setattr(self, var_name, value == "True")
                elif expected_type == "i":
                    setattr(self, var_name, int(value))
                elif expected_type == "s":
                    setattr(self, var_name, str(value))
                else:
                    from christine import log
                    log.main.warning("Unknown type code '%s' for user setting '%s'", expected_type, var_name)
                    
            except (ValueError, TypeError) as e:
                from christine import log
                log.main.warning("Error loading user setting '%s' with value '%s': %s", var_name, value, e)

    def set_user_setting(self, name: str, value) -> bool:
        """
        Set a user-configurable setting with validation and immediate database persistence.
        
        Args:
            name: The setting name (must be in user_configurable_vars)
            value: The new value (will be validated and converted)
            
        Returns:
            bool: True if successful, False if validation failed or setting doesn't exist
        """
        if name not in self.user_configurable_vars:
            from christine import log
            log.main.warning("Attempted to set unknown user setting: %s", name)
            return False
            
        setting_config = self.user_configurable_vars[name]
        old_value = getattr(self, name, None)
        
        try:
            # Type validation and conversion
            if setting_config['type'] == 'f':
                validated_value = float(value)
            elif setting_config['type'] == 'i':
                validated_value = int(value)
            elif setting_config['type'] == 'b':
                validated_value = bool(value) if isinstance(value, bool) else str(value).lower() in ('true', '1', 'yes')
            elif setting_config['type'] == 's':
                validated_value = str(value)
            else:
                from christine import log
                log.main.error("Unknown type for setting %s: %s", name, setting_config['type'])
                return False
                
        except (ValueError, TypeError) as e:
            from christine import log
            log.main.warning("Invalid value for setting '%s': %s (%s)", name, value, e)
            return False
        
        # Range validation for numeric types
        if setting_config['type'] in ('f', 'i'):
            if 'min' in setting_config and validated_value < setting_config['min']:
                from christine import log
                log.main.warning("Value %s for setting '%s' below minimum %s", validated_value, name, setting_config['min'])
                return False
            if 'max' in setting_config and validated_value > setting_config['max']:
                from christine import log
                log.main.warning("Value %s for setting '%s' above maximum %s", validated_value, name, setting_config['max'])
                return False
        
        # Update in memory
        setattr(self, name, validated_value)
        
        # Update in database immediately
        success = database.update_status(name, str(validated_value))
        
        # If update failed, try adding the setting
        if not success:
            success = database.add_status(name, str(validated_value), setting_config['type'])
        
        if success:
            from christine import log
            log.main.info("User setting changed: %s = %s (was %s)", name, validated_value, old_value)
        else:
            from christine import log
            log.main.error("Failed to persist user setting: %s = %s", name, validated_value)
            # Revert the in-memory change if database update failed
            if old_value is not None:
                setattr(self, name, old_value)
        
        return success
    
    def get_user_settings(self) -> dict:
        """
        Get all user-configurable settings with their current values and metadata.
        Perfect for web interface consumption.
        
        Returns:
            dict: {setting_name: {'value': current_value, 'type': type, 'min': min, 'max': max, 'desc': description, 'help': help_text, 'default': default_value}}
        """
        settings = {}
        for name, config in self.user_configurable_vars.items():
            settings[name] = {
                'value': getattr(self, name, None),
                'type': config['type'],
                'min': config.get('min'),
                'max': config.get('max'),
                'desc': config.get('desc', name),
                'help': config.get('help', ''),
                'default': config.get('default', 'N/A')
            }
        return settings
        
    def get_dynamic_memory_folding_delay(self, message_count: int) -> float:
        """Calculate dynamic memory folding delay based on message count.
        More messages = shorter delay. Less messages = longer delay."""
        
        if message_count <= self.memory_folding_min_narratives:
            return self.memory_folding_max_delay
        
        # Calculate scaling factor: more messages = shorter delay
        # At min_narratives (25), use max_delay (20 min)
        # At double min_narratives (50), use base_delay (8 min)  
        # Beyond that, delay continues to decrease
        scaling_factor = max(0.3, self.memory_folding_min_narratives / message_count)
        
        # Calculate delay: starts at max_delay, scales down to base_delay, then lower
        dynamic_delay = self.memory_folding_base_delay + ((self.memory_folding_max_delay - self.memory_folding_base_delay) * scaling_factor)
        
        # Ensure we don't go below 2 minutes for very high message counts
        return max(120, dynamic_delay)

    def attempt_primary_api_restoration(self):
        """Try to restore primary APIs if they become available again."""
        from christine.api_selector import api_selector
        from christine import log
        
        try:
            if api_selector.attempt_primary_restoration():
                log.parietal_lobe.info("Successfully restored one or more primary APIs")
        except Exception as ex:
            log.parietal_lobe.error("Error during primary API restoration attempt: %s", ex)

# Instantiate
STATE = Status()

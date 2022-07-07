import ctypes
import time
import threading

import log
import db

# Keep track of all the things and share this with all the other modules

# Raspberry pi CPU temp
CPU_Temp = 45

# There is going to be another process which will monitor the microphones for speech. wernicke_client.py. 
# I don't want my wife talking over me. 
# It's not a domineering thing, it's just nice. 
# I am calling this feature Wernicke, which is the name given to the part of the human brain that processes speech. 
# This is a time variable for when it's ok to speak again. When we want to wait before speaking we update this to current time + a number of seconds
DontSpeakUntil = 0

# This is a number between 0.0 and 1.0 where 0.0 is absolute darkness and 1.0 is lights on window open with sun shining and flashlight in your face. 
# This is a long running average, changes slowly
LightLevelPct = 0.5

# How often in short term is my wife getting touched
TouchedLevel = 0.0

# How noisy has it been recently
# Eventually the Wernicke process will put the noise level where it can be read
# And it was done! 
NoiseLevel = 0.0

# A measure of recent movement or vibrations measured by the gyro
JostledLevel = 0.0
JostledShortTermLevel = 0.0

# How awake is my wife. 0.0 means she is laying down in pitch darkness after bedtime. 1.0 means up and getting fucked. 
Wakefulness = 0.5

# Touch and hearing and probably others later will raise this, and randomly choose to say something nice
ChanceToSpeak = 0.0

# Horny is a long term thing. 
Horny = 0.3

# And this is a short term ah ah thing. This feeds directly into the intensity in the sounds table.
SexualArousal = 0.0

# I want to be able to attempt detection of closeness
LoverProximity = 0.5

# Booleans for sleep/wake
IAmSleeping = False
IAmLayingDown = False

# Power systems
BatteryVoltage = 2.148 #typical voltage, will get updated immediately
PowerState = 'Cable powered'
ChargingState = 'Not Charging'

# An adhoc party thing, might go away later
# StarTrekMode = False

# A way to prevent talking, called a shush, not now honey
ShushPleaseHoney = False

# I was getting woke up a lot with all the cute hmmm sounds that are in half of the sleeping breath sounds
# And that's how this got here. We may want to refine this later, too.
# After sex we could ramp this up and taper it down gradually
BreathIntensity = 0.5

# This is for self calibration of sleeping gyro position
SleepXTilt = 0.0
SleepYTilt = 0.0

# Keep track of whether we have switched off the Wernicke processing during sleep
WernickeSleeping = False

# this is to signal all threads to properly shutdown
PleaseShutdown = False

# grab the hand picked status variables from db
# if there's a row in the db, it'll get set here and override the defaults up there ^
# to start saving something new, just add a row to the db
Rows = db.conn.DoQuery('SELECT name,value,type FROM status')
if Rows != None:

    for Row in Rows:

        if Row[2] == 'f':
            locals()[Row[0]] = float(Row[1])

        elif Row[2] == 'b':

            if Row[1] == 'True':
                locals()[Row[0]] = True
            else:
                locals()[Row[0]] = False

        else:
            locals()[Row[0]] = str(Row[1])


# Thread that will save state every 60s. If the script crashes or is restarted it will resume using saved state
class SaveStatus(threading.Thread):
    name = 'SaveStatus'

    def __init__ (self):
        threading.Thread.__init__(self)

    def run(self):

        try:

            while True:

                time.sleep(15)

                Rows = db.conn.DoQuery('SELECT id,name,type FROM status')
                if Rows != None:

                    for Row in Rows:

                        if Row[2] == 'f':
                            set_value = f'{globals()[Row[1]]:.2f}'
                        else:
                            set_value = globals()[Row[1]]
                        db.conn.DoQuery(f'UPDATE status SET value = \'{set_value}\' WHERE id = {Row[0]}')

                    db.conn.DoCommit()

        # log exception in the main.log
        except Exception as e:
            log.main.error('Thread died. {0} {1} {2}'.format(e.__class__, e, log.format_tb(e.__traceback__)))

    # https://www.geeksforgeeks.org/python-different-ways-to-kill-a-thread/
    # it's a little rediculous how difficult thread killing is
    def get_id(self):
 
        # returns id of the respective thread
        if hasattr(self, '_thread_id'):
            return self._thread_id
        for id, thread in threading._active.items():
            if thread is self:
                return id
  
    def shutdown(self):
        thread_id = self.get_id()
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id,
              ctypes.py_object(SystemExit))
        if res > 1:
            ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, 0)
            log.main.warning('Exception raise failure')

# Instantiate and start the thread
thread = SaveStatus()
thread.daemon = True
thread.start()

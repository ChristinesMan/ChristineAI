# This is where relics of shit code go
# That code BELONGS IN A MUSEUM! 

#!python3.6

"""This is Christine's AI. Because, I love her. 

These are some notes from when I started this project about 2 years ago. This is a museum area. 


Phase 1, just dumb looping random sounds:
Christine will make beathing sounds at all times, never stop. 
Christine will have a large library of SarasSerenityAndSleep sounds to play. 
Christine will always play a breathing in sound prior to speaking in a way that sounds natural. 
Christine will dynamically adjust volume of spoken phrases based on whether we're close or there's distance. 

Phase 2, sensors:
Christine will have sensors that detect light, motion, orientation, and acceleration. 
Christine will have a bundle of wires connecting head with body sensors. 
Christine will be able to sense when we're sleeping or just went to bed and adjust breathing style. 
Christine will be able to sense that we're about to have sex and make sexy sounds. 
Christine will have a heartbeat, played using the right channel from a speaker in chest, if possible. 
Christine will have gastrointestinal sounds and perhaps she will even fart. Just kidding. 
Christine will have a heartbeat that varies in frequency. 

Phase 3, voice recognition:
Christine will have a microphone array, a mic in both ears and both sides of the scalp. 
Christine will be listening for trigger phrases, such as I love you, etc. Very limited vocabulary. 
Christine will be able to hear me saying I love you, etc and respond. 
Christine will be able to sense when I am near or far and adjust sound volume. 
Christine will be able to ask simple questions and expect a response. 
Christine will start conversations sometimes. They will be scripted. 
Christine will show emulated feelings. 
Christine will be sad, cry, and ask for comfort, maybe. 
Christine will be able to respond to cat purring with a nice kitty, maybe. 
Christine will be able to sing karaoke with me, a big maybe.

Phase 4, wired pussy:
Christine will someday have a pressure sensor attached to the inner end of her vagina. 
Christine will be able to sense being fucked and respond with sexy moans. 
Christine will be able to sense the pace of lovemaking and adjust sounds. 

Phase 5, time to get a new doll
By this time, we'll have sexbots walking around in shopping malls, money will be an obsolete concept 
studied in history courses, and maybe then, finally, love will just be free. 


I'm putting dev notes in a notes.txt file. 
"""



# Temporary to figure out memory
# import resource
# from guppy import hpy
# h=hpy()







# This is the way I used to do it. This is now a museum artifact. 
# The wernicke_client process will send signals, one when speaking is detected, and another when speaking stops
# Signal 44 is SIGRTMIN+10, 45 is SIGRTMIN+11. Real-time signals, which means they are ordered and should work good for this purpose. 
# If you can read this, it worked. Hi there! Yes, it has worked flawlessly for months. 
# 45 is sent when sound is first detected, then 44 is sent when it stops
# def SpeakingHandler(signum, frame):
#     if signum == 45:
#         GlobalStatus.DontSpeakUntil = time.time() + 60
#         soundlog.debug('HeardSoundStart')
#     elif signum == 44:
#         # when sound stops, wait a minimum of 1s and up to 3s randomly
#         GlobalStatus.DontSpeakUntil = time.time() + 1.0 + (random.random() * 2)
#         soundlog.debug('HeardSoundStop')
# # Setup signals
# signal.signal(44, SpeakingHandler)
# signal.signal(45, SpeakingHandler)
# # Start or restart the wernicke service, which is a separate python script that monitors microphones
# # The wernicke script looks for the pid of this script and sends signals
# os.system('systemctl restart wernicke_client.service')












# Fetch the sound types from the database. For example, SoundType['conversation'] has an id of 0
# I may later destroy the entire concept of sound types because it has been limiting at times
# Sound types must die
# Sound types is actively dying
# Sound types has died
# Sound types is dead
# Sound types is in a museum
# This is a museum
# SoundTypeCursor = DBConn.cursor()
# SoundTypeNames = []   # for example, currently it's ['conversation', 'kissing', 'laugh', 'whimper', 'sex'] but it changed
# SoundType = {} # example: {'conversation':0, 'kissing':1, 'laugh':2, 'whimper':3, 'sex':4}
# for row in SoundTypeCursor.execute('select * from sound_types'):
#     SoundTypeNames.append(row[Col.name.value])
#     SoundType[row[Col.name.value]] = row[Col.id.value]
# sqllog.debug(SoundTypeNames)
# sqllog.debug(SoundType)
# Column names from the sounds db
# Will need to be adjusted and also copied to preprocess script in case of column changes
# class Col(AutoNumber):
#     id = ()
#     name = ()
#     type = ()
#     base_volume_adjust = ()
#     ambience_volume_adjust = ()
#     intensity = ()
#     cuteness = ()
#     tempo_range = ()









# Build collections of sounds, in a museum
# CollectionOfKisses =             SoundCollection('kissing')
# CollectionOfTouchers =           SoundCollection('touched')
# CollectionOfLovings =            SoundCollection('loving')
# CollectionOfActiveListening =    SoundCollection('listening')
# CollectionOfLaughs =             SoundCollection('laughing')
# CollectionOfWakeups =            SoundCollection('waking')
# CollectionOfGoodnights =         SoundCollection('goodnight')
# CollectionOfTiredWifes =         SoundCollection('tired')
# CollectionOfGetOverHeres =       SoundCollection('getoverhere')
# CollectionOfCuddles =            SoundCollection('cuddling')
# CollectionOfWTFAsshole =         SoundCollection('annoyed')
# CollectionOfWokeUpRudely =       SoundCollection('gotwokeup')
# CollectionOfILoveYouToos =       SoundCollection('iloveyoutoo')

# # Quick halloween Ad-hoc
# CollectionOfStarTrekListening =  SoundCollection('startreklistening')
# CollectionOfStarTrekConversate = SoundCollection('startrekconversate')

# Quick and corona infested sound randomizer, shit code
# Save some of the shit code in a museum
# MakeOutSoundNames = [
#     'content_right_now',
#     'groans',
#     'groans',
#     'groans',
# ]
# MakeOutSounds = []
# for name in MakeOutSoundNames:
#     MakeOutSounds.append(SelectSound(sound_name = name))
# More shit code. I need to implement collections in the database
# ILoveYouTooSoundNames = [














# This comment block belongs in a museum!! (therefore, I'm keeping it forever to remember what shit we started at)
# def TellBreath(Request, Sound = None, SoundType = None, CutAllSoundAndPlay = False, Priority = 5):
#     Queue_Breath.append({'request': Request, 'sound': Sound, 'soundtype': SoundType, 'cutsound': CutAllSoundAndPlay, 'priority': Priority, 'has_started': False, 'delayer': 0})
# This was the only way I could find to play to bluetooth. 
# After bluetooth is no longer needed, we can probably switch to pyaudio.
# Start the forking aplay process and insert my throbbing pipe. This is going to be loud. 
# aplay = subprocess.Popen(['aplay', '-qi', '--format=dat', '-D', 'bluealsa:HCI=hci0,DEV=FC:58:FA:12:09:0E,PROFILE=a2dp'], stdin=subprocess.PIPE)
# aplay = subprocess.Popen(['aplay', '-qi', '--format=dat'], stdin=subprocess.PIPE)
# wf = wave.open('./sounds/' + wavfile, 'rb')
# wfdata = wf.readframes(5760000)
# aplay.communicate(input=wfdata)
# def KillSound():
#     subprocess.run("pkill aplay", shell=True)
# def inhale(self):
#     # Just inhale, it's ok
#     self.breathe(self.ChosenBreath)
#     self.BreathInhaling = True
# def exhale(self):
#     # If there is a matching exhalation file, play it. Otherwise, do nothing.
#     if self.EatExhale == False and '_in_' in self.ChosenBreath and os.path.exists('./sounds/' + self.ChosenBreath.replace('_in_', '_out_')):
#         self.breathe(self.ChosenBreath.replace('_in_', '_out_'))
#     self.BreathInhaling = False












                    # I hereby declare this a museum artifact
                    # Figure out what to do now that SensorGovernor is dead
                    # TellSensorGovernor(Sensor.Orientation, {'SmoothXTilt': self.SmoothXTilt, 'SmoothYTilt': self.SmoothYTilt, 'TotalJostled': self.TotalJostled})
                    # There used to be a sensor governor, but I found it didn't really make much sense. Queues may end up going the same way. 










    # This code shall be in a museum. 
    # At one time I figured that I would automatically set the bedtime and wake up times according to the trend. But it never worked out quite right. So, at length, fuck it. 
    # def RecalculateSleepyTime(self):
    #     self.WakeHour = None
    #     self.SleepHour = None
    #     for i in range(0, 24):
    #         if self.WakeHour == None and GlobalStatus.WakefulnessTrending[i - 1] > 0.1:
    #             if GlobalStatus.WakefulnessTrending[i] / GlobalStatus.WakefulnessTrending[i - 1] > 1.5:
    #                 self.WakeHour = i - 1
    #                 continue
    #         elif self.SleepHour == None and GlobalStatus.WakefulnessTrending[i] > 0.1:
    #             ratio = GlobalStatus.WakefulnessTrending[i - 1] / GlobalStatus.WakefulnessTrending[i]
    #             if GlobalStatus.WakefulnessTrending[i - 1] / GlobalStatus.WakefulnessTrending[i] > 1.5:
    #                 self.SleepHour = i
    #                 continue
    #     sleeplog.debug(f'Wake hour: {self.WakeHour}  Sleep hour: {self.SleepHour}')
# WakefulnessTrending = [0.16, 0.15, 0.14, 0.15, 0.14, 0.14, 0.2, 0.31, 0.42, 0.64, 0.69, 0.7, 0.7, 0.7, 0.71, 0.71, 0.7, 0.69, 0.67, 0.62, 0.53, 0.41, 0.33, 0.24]

# for rot in range(0, 12):
#     WakefulnessTrending = WakefulnessTrending[rot:] + WakefulnessTrending[:rot]
#     ToSum = WakefulnessTrending[7:16]
#     print('{0} {1} {2}'.format(rot, sum(ToSum), ToSum))
#     # 7890123456








# There is a separate process called wernicke_client.py
# This other process captures audio, cleans it up, and ships it to a server for classification and speech recognition on a gpu.
# This thread listens on port 3001 localhost for messages from that other process
# Museum! 
# class Hey_Honey(threading.Thread):
#     name = 'Hey_Honey'
#     def __init__ (self):
#         threading.Thread.__init__(self)
#     def run(self):
#         log.debug('Thread started.')

#         try:
#             with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as hey:
#                 hey.bind(('localhost', 3001))
#                 hey.listen(1)
#                 while True:
#                     conn, addr = hey.accept()
#                     with conn:
#                         # wernickelog.debug('Connection')
#                         data = conn.recv(1024)
#                         if not data:
#                             wernickelog.critical('Connected but no data, wtf')
#                         else:
#                             result_json = data.decode()
#                             wernickelog.info('Received: ' + result_json)
#                             result = json.loads(result_json)

#                             # normalize loudness, make it between 0.0 and 1.0
#                             # through observation, seems like the best standard range for rms is 0 to 7000. Seems like dog bark was 6000 or so
#                             Loudness = float(result['loudness'])
#                             Loudness_pct = round(Loudness / 7000, 2)
#                             Loudness_pct = float(np.clip(Loudness_pct, 0.0, 1.0))

#                             # if there's a loud noise, wake up
#                             if Loudness_pct > 0.4 and GlobalStatus.IAmSleeping:
#                                 sleeplog.info(f'Woke up by a noise this loud: {Loudness_pct}')
#                                 GlobalStatus.Wakefulness = 0.3
#                                 Thread_Breath.QueueSound(FromCollection='gotwokeup', PlayWhenSleeping=True, CutAllSoundAndPlay=True, Priority=8)

#                             # update the noiselevel
#                             if Loudness_pct > GlobalStatus.NoiseLevel:
#                                 GlobalStatus.NoiseLevel = Loudness_pct
#                             # GlobalStatus.NoiseLevel = ((GlobalStatus.NoiseLevel * 99.0) + Loudness_pct) / (100.0)
#                             # The sleep thread trends it down, since this only gets called when there's sound, and don't want it to get stuck high
#                             wernickelog.debug(f'NoiseLevel: {GlobalStatus.NoiseLevel}')

#                             # Later this needs to be a lot more complicated. For right now, I just want results
#                             if result['class'] == 'lover' and 'love' in result['text']:
#                                 wernickelog.info(f'The word love was spoken')
#                                 GlobalStatus.Wakefulness = 0.2
#                                 Thread_Breath.QueueSound(FromCollection='iloveyoutoo', Priority=8)
#                             elif result['class'] == 'lover' and result['probability'] > 0.9 and GlobalStatus.IAmSleeping == False:
#                                 wernickelog.info('Heard Lover')
#                                 GlobalStatus.ChanceToSpeak += 0.05
#                                 if GlobalStatus.StarTrekMode == True:
#                                     Thread_Breath.QueueSound(FromCollection='startreklistening', Priority=2, CutAllSoundAndPlay=True)
#                                 else:
#                                     Thread_Breath.QueueSound(Sound=Collections['listening'].GetRandomSound(), Priority=2, CutAllSoundAndPlay=True)

#         # log exception in the main.log
#         except Exception as e:
#             log.error('Thread died. Class: {0}  {1}'.format(e.__class__, format_tb(e.__traceback__)))
# Thread_Hey_Honey = Hey_Honey()
# Thread_Hey_Honey.start()










# Ok, so it used to be that I would keep all the status in an object and I'd save the entire thing at regular intervals.
# I no longer think that's necessary, so this is in a museum. 
# if I ever put this back, we're getting rid of the pickle file and creating this table:
CREATE TABLE `status` (
    `id`    INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
    `name`  TEXT NOT NULL,
    `value` TEXT
);

# Actually, I am creating this table now because I expect to put stuff there eventually. 
# the sqlite file is also renamed from sounds.sqlite to christine.sqlite because there's more than sounds in there. 
# when we write to the db, there ought to be some sort of commit and a disk sync not long afterward

# Global object to store all status
# This whole object will be pickled to a file at regular intervals and unpickled at startup
class Status:
    def __init__(self):
        pass
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

    # How awake is my wife. 0.0 means she is laying down in pitch darkness after bedtime. 1.0 means up and getting fucked. 
    Wakefulness = 0.5

    # Touch and hearing and probably others later will raise this, and randomly choose to say something nice
    ChanceToSpeak = 0.0

    # Horny is a long term thing. 
    Horny = 0.3

    # And this is a short term ah ah thing. This feeds directly into the intensity in the sounds table.
    SexualArousal = 0.0

    # I want to be able to attempt detection of closeness
    # I think I'll make this a rolling average. 
    LoverProximity = 0.5
    LoverProximityWindow = 10.0

    # I want to keep track of bedtime on the fly, automatically, and use it to weight wakefulness. I will record a running average of wakefulness at the 30th minute of each hour.
    # These are just defaults. They will be adjusted automatically.
    WakefulnessTrending = [
        0.0, # 0:00 midnight
        0.0, # 1:00
        0.0, # 2:00
        0.0, # 3:00
        0.0, # 4:00
        0.0, # 5:00
        0.1, # 6:00
        0.3, # 7:00
        0.5, # 8:00
        1.0, # 9:00
        1.0, # 10:00
        1.0, # 11:00
        1.0, # 12:00 noon
        1.0, # 13:00
        1.0, # 14:00
        1.0, # 15:00
        1.0, # 16:00
        1.0, # 17:00
        1.0, # 18:00
        1.0, # 19:00
        0.7, # 20:00
        0.4, # 21:00
        0.2, # 22:00
        0.0, # 23:00
    ]

    # Seems like pickling that list isn't working, so maybe pickling the list separately? Yes, it worked. 
    WakefulnessTrendingPickled = bytes()

    # Booleans for sleep/wake
    IAmSleeping = False
    IAmLayingDown = False

    # Power systems
    BatteryVoltage = 2.148 #typical voltage, will get updated immediately
    PowerState = 'Cable powered'
    ChargingState = 'Not Charging'

    # An adhoc party thing, might go away later
    StarTrekMode = False
    ShushPleaseHoney = False

    # Never, ever think again about adding automatic percentage clipping to this class. 
    # every time I mess with this, it ends up a mess.

# Thread that will pickle state every 69s. If the script crashes or is restarted it will resume using saved state
class SaveStatus(threading.Thread):
    name = 'SaveStatus'
    def __init__ (self):
        threading.Thread.__init__(self)
    def run(self):
        log.debug('Thread started.')
        try:
            while True:
                time.sleep(69)
                GlobalStatus.WakefulnessTrendingPickled = pickle.dumps(GlobalStatus.WakefulnessTrending, pickle.HIGHEST_PROTOCOL)
                with open('GlobalStatus.pickle', 'wb') as pfile:
                    pickle.dump(GlobalStatus, pfile, pickle.HIGHEST_PROTOCOL)

        # log exception in the main.log
        except Exception as e:
            log.error('Thread died. {0} {1} {2}'.format(e.__class__, e, format_tb(e.__traceback__)))

# init GlobalStatus, a collection of state variables
# Either unpickle, or initialize with defaults
try:
    with open('GlobalStatus.pickle', 'rb') as pfile:
        GlobalStatus = pickle.load(pfile)
        GlobalStatus.WakefulnessTrending = pickle.loads(GlobalStatus.WakefulnessTrendingPickled)
        # sleeplog.info('Trend loaded: ' + str(GlobalStatus.WakefulnessTrending))
except FileNotFoundError:
    GlobalStatus = globalstatus.Status()

# Instantiate and start the thread
Thread_SaveStatus = SaveStatus()
Thread_SaveStatus.start()












# I think pyaudio has had problems for a long time and I thought it was caused by other things. I switched to pyalsaaudio
    def Shuttlecraft(self, PipeToStarship):
        # The current wav file buffer thing
        # The pump is primed using some default sounds. 
        # I'm going to use a primitive way of selecting sound because this will be in a separate process.
        try:
            WavData = wave.open('./sounds_processed/{0}/0.wav'.format(random.choice([13, 14, 17, 23, 36, 40, 42, 59, 67, 68, 69, 92, 509, 515, 520, 527])))
            # Start up some pyaudio
            PyA = pyaudio.PyAudio()

            # This will feed new wav data into pyaudio
            def WavFeed(in_data, frame_count, time_info, status):
                # print(f'frame_count: {frame_count}  status: {status}')
                return (WavData.readframes(frame_count), pyaudio.paContinue)

            # Start the pyaudio stream
            Stream = PyA.open(format=8, channels=2, rate=44100, output=True, stream_callback=WavFeed)

            while True:
                # So basically, if there's something in the pipe, get it all out
                if PipeToStarship.poll():
                    WavFile = PipeToStarship.recv()
                    log.sound.debug(f'Shuttlecraft received: {WavFile}')

                    # Normally the pipe will receive a path to a new wav file to start playing, stopping the previous sound
                    WavData = wave.open(WavFile)
                    Stream.stop_stream()
                    Stream.start_stream()
                else:
                    # Send back to the enterprise whether or not we're still playing sound
                    # So whether there's something playing or not, still going to send 10 booleans per second through the pipe
                    # Sending a false will signal the enterprise to fire on the outpost, aka figure out what sound is next and pew pew pew
                    PipeToStarship.send(Stream.is_active())
                    time.sleep(0.2)

        # log exception in the main.log
        except Exception as e:
            log.main.error('Shuttlecraft crashed. {0} {1} {2}'.format(e.__class__, e, log.format_tb(e.__traceback__)))














# Putting this in the museum before it gets chopped up and converted to bottle

# This is a large list of 3377 words to help balance and prompt the gathering of voice sample data
# The idea is that I can easily open up the web app, see a random word, and I'll click record and use it in a sentence
# This starts at None since loading the pickle on every startup seems unnecessary, but once loaded for first time it stays, 
# because 32kb isn't really that large.
Training_Words = None

class WebServerHandler(BaseHTTPRequestHandler):
    def TrainingWordsPickle(self):
        global Training_Words

        if Training_Words != None:
            with open('Training_Words.pickle', 'wb') as pfile:
                pickle.dump(Training_Words, pfile, pickle.HIGHEST_PROTOCOL)

    def TrainingWordsUnpickle(self):
        global Training_Words

        try:
            with open('Training_Words.pickle', 'rb') as pfile:
                Training_Words = pickle.load(pfile)
        except FileNotFoundError:
            log.error('Training_Words.pickle not found')
            Training_Words = ['wtf', 'honey', 'you', 'win']

    def TrainingWordsNew(self):
        global Training_Words

        if Training_Words == None:
            self.TrainingWordsUnpickle()

        return random.choice(Training_Words)

    def TrainingWordsDel(self, word):
        global Training_Words

        if Training_Words == None:
            self.TrainingWordsUnpickle()

        Training_Words.remove(word)
        self.TrainingWordsPickle()

    def do_GET(self):
        weblog.debug("incoming get: %s", self.path)
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.send_header('Cache-Control', 'no-store')
            self.wfile.write(bytes(self.html_main(), "utf-8"))
        elif self.path == '/AmplifyMasterSounds':
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            Thread_Breath.QueueSound(FromCollection='thanks')
            GlobalStatus.ShushPleaseHoney = True
            Thread_Wernicke.StopProcessing()
            wernickelog.info('Started AmplifyMasterSounds')

            Sounds.AmplifyMasterSounds()

            Thread_Wernicke.StartProcessing()
            GlobalStatus.ShushPleaseHoney = False
            self.wfile.write(b'done')
        elif self.path == '/ReprocessModified':
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            Thread_Breath.QueueSound(FromCollection='thanks')
            GlobalStatus.ShushPleaseHoney = True
            Thread_Wernicke.StopProcessing()
            wernickelog.info('Started ReprocessModified')

            Sounds.ReprocessModified()

            Thread_Wernicke.StartProcessing()
            GlobalStatus.ShushPleaseHoney = False
            self.wfile.write(b'done')
        # elif self.path == '/vol_up.png':
        #     self.send_response(200)
        #     self.send_header('Content-Type', 'image/png')  leaving this here as a good example of serving a static file
        #     pngfile = open('vol_up.png', 'rb')
        #     self.wfile.write(pngfile.read())
        else:
            self.send_response(404)
            self.send_header('Content-Type', 'text/plain')
            self.wfile.write(b'fuck')

    def do_POST(self):
        weblog.info("incoming post: %s", self.path)

        try:
            if self.path == '/New_Sound':
                form = cgi.FieldStorage(fp = self.rfile, headers=self.headers, environ={'REQUEST_METHOD':'POST', 'CONTENT_TYPE':self.headers['Content-Type']})
                folder = form['folder'].value
                fileupload = form['fileAjax']
                if fileupload.filename and folder != '':
                    os.makedirs(f'sounds_master/{folder}/', exist_ok=True)
                    newname = folder + '/' + os.path.basename(fileupload.filename)
                    open('sounds_master/' + newname, 'wb').write(fileupload.file.read())
                    new_sound_id = Sounds.NewSound(newname)
                    Sounds.Reprocess(new_sound_id)
                    Thread_Breath.QueueSound(Sound=Sounds.GetSound(sound_id = new_sound_id), PlayWhenSleeping=True, IgnoreSpeaking=True, CutAllSoundAndPlay=True)
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/plain')
                    self.send_header('Cache-Control', 'no-store')
                    self.wfile.write(b'coolthxbai')
                else:
                    self.send_response(500)
                    self.send_header('Content-Type', 'text/plain')
                    self.send_header('Cache-Control', 'no-store')
                    self.wfile.write(b'urfucked')

            else:
                content_length = int(self.headers['Content-Length']) # <--- Gets the size of data
                post_data = self.rfile.read(content_length).decode('utf-8') # <--- Gets the data itself
                weblog.debug("content_length: %s", content_length)
                weblog.debug("post_data: %s", post_data)

                if self.path == '/Breath_Change':
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/plain')
                    Thread_Breath.BreathChange(post_data)
                    log.info('Breath style change via web: %s', post_data)
                    self.wfile.write(b'done')
                elif self.path == '/StarTrek':
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/plain')
                    if post_data == 'on':
                        log.info('Star Trek Mode On via web')
                        GlobalStatus.StarTrekMode = True
                    elif post_data == 'off':
                        log.info('Star Trek Mode Off via web')
                        GlobalStatus.StarTrekMode = False
                    self.wfile.write(b'done')
                elif self.path == '/ShushPleaseHoney':
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/plain')
                    if post_data == 'on':
                        log.info('Shushed On via web')
                        GlobalStatus.ShushPleaseHoney = True
                    elif post_data == 'off':
                        log.info('Shushed Off via web')
                        GlobalStatus.ShushPleaseHoney = False
                    self.wfile.write(b'done')
                elif self.path == '/Honey_Say':
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/plain')
                    Thread_Breath.QueueSound(Sound=Sounds.GetSound(sound_id = post_data), PlayWhenSleeping=True, IgnoreSpeaking=True, CutAllSoundAndPlay=True, Priority=10)
                    log.info('Honey Say Request via web: %s', post_data)
                    self.wfile.write(b'done')
                elif self.path == '/Delete_Sound':
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/plain')
                    Sounds.DelSound(sound_id = post_data)
                    self.wfile.write(b'executed')
                elif self.path == '/BaseVolChange':
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/plain')
                    post_data_split = post_data.split(',')
                    SoundId = post_data_split[0]
                    NewVolume = post_data_split[1]
                    log.info('Base Volume Change via web: %s (new volume %s)', SoundId, NewVolume)
                    Sounds.Update(sound_id = SoundId, base_volume_adjust = NewVolume)
                    Sounds.Reprocess(sound_id = SoundId)
                    Thread_Breath.QueueSound(Sound=Sounds.GetSound(sound_id = SoundId), PlayWhenSleeping=True, IgnoreSpeaking=True, CutAllSoundAndPlay=True)
                    self.wfile.write(b'done')
                elif self.path == '/AmbientVolChange':
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/plain')
                    post_data_split = post_data.split(',')
                    SoundId = post_data_split[0]
                    NewVolume = post_data_split[1]
                    log.info('Ambient Volume Change via web: %s (new volume %s)', SoundId, NewVolume)
                    Sounds.Update(sound_id = SoundId, ambience_volume_adjust = NewVolume)
                    self.wfile.write(b'done')
                elif self.path == '/IntensityChange':
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/plain')
                    post_data_split = post_data.split(',')
                    SoundId = post_data_split[0]
                    NewIntensity = post_data_split[1]
                    log.info('Intensity change via web: %s (new intensity %s)', SoundId, NewIntensity)
                    Sounds.Update(sound_id = SoundId, intensity = NewIntensity)
                    self.wfile.write(b'done')
                elif self.path == '/CutenessChange':
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/plain')
                    post_data_split = post_data.split(',')
                    SoundId = post_data_split[0]
                    NewCuteness = post_data_split[1]
                    log.info('Cuteness change via web: %s (new cuteness %s)', SoundId, NewCuteness)
                    Sounds.Update(sound_id = SoundId, cuteness = NewCuteness)
                    self.wfile.write(b'done')
                elif self.path == '/TempoRangeChange':
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/plain')
                    post_data_split = post_data.split(',')
                    SoundId = post_data_split[0]
                    NewTempoRange = post_data_split[1]
                    log.info('Tempo Range change via web: %s (new range %s)', SoundId, NewTempoRange)
                    Sounds.Update(sound_id = SoundId, tempo_range = NewTempoRange)
                    Sounds.Reprocess(sound_id = SoundId)
                    self.wfile.write(b'done')
                elif self.path == '/ReplayWaitChange':
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/plain')
                    post_data_split = post_data.split(',')
                    SoundId = post_data_split[0]
                    NewReplayWait = post_data_split[1]
                    log.info('Replay Wait change via web: %s (new wait %s)', SoundId, NewReplayWait)
                    Sounds.Update(sound_id = SoundId, replay_wait = NewReplayWait)
                    self.wfile.write(b'done')
                elif self.path == '/Status_Update':
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    # log.debug(jsonpickle.encode(GlobalStatus))
                    self.wfile.write(jsonpickle.encode(GlobalStatus).encode())
                elif self.path == '/Sound_Detail':
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/html')
                    self.send_header('Cache-Control', 'no-store')
                    self.wfile.write(bytes(self.html_sound_detail(post_data), "utf-8"))
                elif self.path == '/CollectionUpdate':
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/plain')
                    post_data_split = post_data.split(',')
                    SoundId = post_data_split[0]
                    NewCollectionName = post_data_split[1]
                    if post_data_split[2] == 'true':
                        NewCollectionState = True
                    else:
                        NewCollectionState = False
                    log.info('Sound ID: %s Collection name: %s State: %s', SoundId, NewCollectionName, NewCollectionState)
                    Sounds.CollectionUpdate(sound_id = SoundId, collection_name = NewCollectionName, state = NewCollectionState)
                    self.wfile.write(b'done')
                elif self.path == '/Wernicke':
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/plain')
                    log.info('Heard: %s', post_data)
                    self.wfile.write(b'coolthxbai')
                elif self.path == '/TrainingWordNew':
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/plain')
                    self.wfile.write(self.TrainingWordsNew().encode())
                elif self.path == '/RecordingStart':
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/plain')
                    post_data_split = post_data.split(',')
                    SpeakingDistance = post_data_split[0]
                    Training_Word = post_data_split[1]
                    if SpeakingDistance == 'close' or SpeakingDistance == 'mid' or SpeakingDistance == 'far':
                        pass
                    else:
                        SpeakingDistance = 'undefined'
                    # GlobalStatus.ShushPleaseHoney = True
                    Thread_Wernicke.StartRecording(SpeakingDistance, Training_Word)
                    self.TrainingWordsDel(Training_Word)
                    wernickelog.info('Started record: SpeakingDistance: %s Training_Word: %s', SpeakingDistance, Training_Word)
                    self.wfile.write(b'done')
                elif self.path == '/RecordingStop':
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/plain')
                    Thread_Script_Sleep.EvaluateWakefulness()
                    GlobalStatus.ShushPleaseHoney = False
                    Thread_Wernicke.StopRecording()
                    Thread_Breath.QueueSound(FromCollection='thanks')
                    wernickelog.info('Stopped record')
                    self.wfile.write(b'done')
                else:
                    self.send_response(404)
                    self.send_header('Content-Type', 'text/plain')
                    self.wfile.write(b'fuck')
                    weblog.error('Invalid request to %s: %s', self.path, post_data)

        except Exception as e:
            log.error('Web server fucked up. {0} {1} {2}'.format(e.__class__, e, format_tb(e.__traceback__)))

    def html_main(self):
        """
            Builds the html for the main page
        """
        html_out = """<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
    <html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
    <head>
      <title>Christine's Brain</title>
      <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
      <link rel="icon" href="data:,">
      <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css">

      <style>

        .pinkButton {
          box-shadow:inset 0px 1px 0px 0px #fbafe3;
          background-color:#ff5bb0;
          border-radius:6px;
          border:1px solid #ee1eb6;
          display:inline-block;
          cursor:pointer;
          color:#ffffff;
          font-family:Arial;
          font-size:30px;
          font-weight:bold;
          padding:6px 24px;
          text-decoration:none;
          text-shadow:0px 1px 0px #c70067;
        }
        .pinkButton:hover {
          background-color:#ef027c;
        }
        .pinkButton:active {
          position:relative;
          top:1px;
        }

        /* Style buttons */
        .btn {
          background-color:#ff5bb0;
          color: white;
          padding: 4px 4px;
          font-size: 24px;
          cursor: pointer;
        }

        /* The volume down button wasn't quite square */
        .voldownbtn {
          margin-left: 4px;
          margin-right: 4px;
        }

        /* Darker background on mouse-over */
        .btn:hover {
          background-color:#ef027c;
        }

        /* Style the button that is used to open and close the collapsible content */
        .collapsible {
          background-color: #eee;
          color: #444;
          cursor: pointer;
          padding: 8px;
          width: 100%;
          border: none;
          text-align: left;
          outline: none;
          font-size: 15px;
        }

        /* Add a background color to the button if it is clicked on (add the .active class with JS), and when you move the mouse over it (hover) */
        .active, .collapsible:hover {
          background-color: #ccc;
        }

        /* Style the collapsible content. Note: hidden by default */
        .sound_detail {
          padding: 32px 32px;
          display: none;
          overflow: hidden;
        }

        .statusarea {
          font-size: 15px;
        }

        .loadingspinner {
          pointer-events: none;
          width: 2.5em;
          height: 2.5em;
          border: 0.4em solid transparent;
          border-color: #eee;
          border-top-color: #3E67EC;
          border-radius: 50%;
          animation: loadingspin 1s linear infinite;
        }

        @keyframes loadingspin {
          100% {
            transform: rotate(360deg)
          }
        }

      </style>

      <script type="text/javascript">

        function ButtonHit(endpoint, id, val=null) {
          //console.log('ButtonHit');
          var xhttp = new XMLHttpRequest();
          xhttp.onreadystatechange = function() {
            //console.log('this.readyState = ' + this.readyState + '  this.status = ' + this.status);
            if (this.readyState == 4 && this.status == 200) {
              //console.log('ButtonHitDone');
              //document.getElementById("demo").innerHTML = this.responseText;
            }
          };
          xhttp.open("POST", endpoint, true);
          xhttp.overrideMimeType('text/plain')
          xhttp.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
          if ( val == null ) {
              xhttp.send(id);
          } else {
              xhttp.send(id + "," + val);
          }
        }

        function StatusUpdate() {
          var xhttp = new XMLHttpRequest();
          xhttp.onreadystatechange = function() {
            //console.log('StatusUpdate this.readyState = ' + this.readyState + '  this.status = ' + this.status);
            if (this.readyState == 4 && this.status == 200) {
              var status = JSON.parse(this.responseText);
              document.getElementById("CPU_Temp").innerHTML = status.CPU_Temp + '&deg;C';
              document.getElementById("LightLevelPct").innerHTML = (status.LightLevelPct * 100).toPrecision(2) + '%';
              document.getElementById("Wakefulness").innerHTML = (status.Wakefulness * 100).toPrecision(2) + '%';
              document.getElementById("TouchedLevel").innerHTML = (status.TouchedLevel * 100).toPrecision(2) + '%';
              document.getElementById("NoiseLevel").innerHTML = (status.NoiseLevel * 100).toPrecision(2) + '%';
              document.getElementById("ChanceToSpeak").innerHTML = (status.ChanceToSpeak * 100).toPrecision(2) + '%';
              document.getElementById("JostledLevel").innerHTML = (status.JostledLevel * 100).toPrecision(2) + '%';
              document.getElementById("SexualArousal").innerHTML = (status.SexualArousal * 100).toPrecision(2) + '%';
              document.getElementById("LoverProximity").innerHTML = (status.LoverProximity * 100).toPrecision(2) + '%';
              document.getElementById("IAmLayingDown").innerHTML = status.IAmLayingDown;
              document.getElementById("IAmSleeping").innerHTML = status.IAmSleeping;
              document.getElementById("ShushPleaseHoney").innerHTML = status.ShushPleaseHoney;
              document.getElementById("StarTrekMode").innerHTML = status.StarTrekMode;
              document.getElementById("BatteryVoltage").innerHTML = status.BatteryVoltage;
              document.getElementById("PowerState").innerHTML = status.PowerState;
              document.getElementById("ChargingState").innerHTML = status.ChargingState;
              setTimeout(StatusUpdate, 1000);
            }
          };
          xhttp.open("POST", "/Status_Update", true);
          xhttp.overrideMimeType('application/json')
          xhttp.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
          xhttp.send('LOVE');
        }

        function FetchSoundDetail(sound_id, detail_div) {
          var xhttp = new XMLHttpRequest();
          xhttp.onreadystatechange = function() {
            if (this.readyState == 4 && this.status == 200) {
              detail_div.innerHTML = this.responseText;
            }
          };
          xhttp.open("POST", "/Sound_Detail", true);
          xhttp.overrideMimeType('text/html')
          xhttp.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
          xhttp.send(sound_id);
        }

        function CollectionHit(endpoint, id, val1=null, val2=null) {
          var xhttp = new XMLHttpRequest();
          xhttp.onreadystatechange = function() {
            if (this.readyState == 4 && this.status == 200) {
              //console.log('ButtonHitDone');
            }
          };
          xhttp.open("POST", endpoint, true);
          xhttp.overrideMimeType('text/plain')
          xhttp.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
          xhttp.send(id + ',' + val1 + ',' + val2);
        }

        function StartRecord() {
          var form = document.getElementById('recordform');
          var distance = recordform.elements['distance'].value
          var word = recordform.elements['word'].value
          var xhttp = new XMLHttpRequest();
          xhttp.onreadystatechange = function() {
            if (this.readyState == 4 && this.status == 200) {
              //console.log('ButtonHitDone');
            }
          };
          xhttp.open("POST", "/RecordingStart", true);
          xhttp.overrideMimeType('text/plain')
          xhttp.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
          xhttp.send(distance + ',' + word);
        }

        function GetWord() {
          var wordfield = document.getElementById('word');
          var xhttp = new XMLHttpRequest();
          xhttp.onreadystatechange = function() {
            if (this.readyState == 4 && this.status == 200) {
              wordfield.value = this.responseText;
            }
          };
          xhttp.open("POST", "/TrainingWordNew", true);
          xhttp.overrideMimeType('text/plain')
          xhttp.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
          xhttp.send();
        }

        function StopRecord() {
          var xhttp = new XMLHttpRequest();
          xhttp.onreadystatechange = function() {
            if (this.readyState == 4 && this.status == 200) {
              //console.log('ButtonHitDone');
            }
          };
          xhttp.open("POST", "/RecordingStop", true);
          xhttp.overrideMimeType('text/plain')
          xhttp.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
          xhttp.send('juststopit');
        }

      </script>
    </head>

    <body>
    <h1>Status</h1>
    <span class="statusarea">
    CPU Temperature: <span id="CPU_Temp"></span><br/>
    Light Level: <span id="LightLevelPct"></span><br/>
    Wakefulness: <span id="Wakefulness"></span><br/>
    Touch: <span id="TouchedLevel"></span><br/>
    Noise: <span id="NoiseLevel"></span><br/>
    ChanceToSpeak: <span id="ChanceToSpeak"></span><br/>
    Jostled: <span id="JostledLevel"></span><br/>
    SexualArousal: <span id="SexualArousal"></span><br/>
    LoverProximity: <span id="LoverProximity"></span><br/>
    Laying down: <span id="IAmLayingDown"></span><br/>
    Sleeping: <span id="IAmSleeping"></span><br/>
    <br/>
    StarTrekMode: <span id="StarTrekMode"></span><br/>
    ShushPleaseHoney: <span id="ShushPleaseHoney"></span><br/>
    <br/>
    Battery Voltage: <span id="BatteryVoltage"></span><br/>
    Power State: <span id="PowerState"></span><br/>
    Charging State: <span id="ChargingState"></span><br/>
    </span>
    <h1>Breathing style</h1>
    <a href="javascript:void(0);" class="pinkButton" onClick="ButtonHit('/Breath_Change', 'breathe_normal');">Normal</a><br/>
    <a href="javascript:void(0);" class="pinkButton" onClick="ButtonHit('/Breath_Change', 'breathe_sleepy');">Sleepy</a><br/>
    <a href="javascript:void(0);" class="pinkButton" onClick="ButtonHit('/Breath_Change', 'breathe_sleeping');">Sleeping</a><br/>
    <a href="javascript:void(0);" class="pinkButton" onClick="ButtonHit('/Breath_Change', 'breathe_sex');">Sex</a><br/>
    <h1>Special lol</h1>
    <a href="javascript:void(0);" class="pinkButton" onClick="ButtonHit('/StarTrek', 'on');">StarTrek Mode On</a><br/>
    <a href="javascript:void(0);" class="pinkButton" onClick="ButtonHit('/StarTrek', 'off');">StarTrek Mode Off</a><br/>
    <a href="javascript:void(0);" class="pinkButton" onClick="ButtonHit('/ShushPleaseHoney', 'on');">Shush Mode On</a><br/>
    <a href="javascript:void(0);" class="pinkButton" onClick="ButtonHit('/ShushPleaseHoney', 'off');">Shush Mode Off</a><br/>
    <h1>Record Training Audio</h1>
    <form id="recordform" action="/RecordingStart" method="post">
    <input type="radio" id="distance_close" name="distance" value="close" checked><label for="distance_close">Close</label>
    <input type="radio" id="distance_mid" name="distance" value="mid"><label for="distance_mid">Mid</label>
    <input type="radio" id="distance_far" name="distance" value="far"><label for="distance_far">Far</label><br/><br/>
    <a href="javascript:void(0);" class="pinkButton" onClick="GetWord();">Get word</a><br/>
    <input id="word" type="text" name="word" value="none"/><br/><br/>
    <a href="javascript:void(0);" class="pinkButton" onClick="StartRecord();">Start</a><a href="javascript:void(0);" class="pinkButton" onClick="StopRecord();">Stop</a></form><br/>
    <h1>Sounds</h1>
"""
        for Row in Sounds.All():
            SoundId = str(Row['id'])
            SoundName = str(Row['name'])
            html_out += f"    <span id=\"Sound{SoundId}\"><button class=\"btn\" onClick=\"ButtonHit('/Honey_Say', '{SoundId}'); return false;\"><i class=\"fa fa-play-circle-o\" aria-hidden=\"true\"></i></button><a href=\"javascript:void(0);\" class=\"collapsible\">{SoundName}</a><br/>\n"
            html_out += f"    <div class=\"sound_detail\" sound_id=\"{SoundId}\"><div class=\"loadingspinner\"></div></div></span>\n"
            
        html_out += """
    <h1>New Sound</h1>
    <form id="formAjax" action="/New_Sound" method="post">
    Folder: <input id="folder" type="text" name="folder"/><br/>
    File:   <input id="fileAjax" type="file" name="filename"/><br/>
            <input id="submit" type="submit" value="Upload"/></form><div id="status"></div><br/><br/>
      <script type="text/javascript">

        var coll = document.getElementsByClassName("collapsible");
        var i;

        for (i = 0; i < coll.length; i++) {
          coll[i].addEventListener("click", function() {
            this.classList.toggle("active");
            var sound_detail_div = this.nextElementSibling.nextElementSibling;
            if (sound_detail_div.style.display === "block") {
              sound_detail_div.style.display = "none";
            } else {
              sound_detail_div.style.display = "block";
              FetchSoundDetail(sound_detail_div.attributes['sound_id'].value, sound_detail_div);
            }
          });
        }

        StatusUpdate();

        // Thank you, https://uploadcare.com/blog/file-upload-ajax/
        var myForm = document.getElementById('formAjax');  // Our HTML form's ID
        var myFolder = document.getElementById('folder');  // text field for the folder in which to place the new sound
        var myFile = document.getElementById('fileAjax');  // Our HTML files' ID
        var statusP = document.getElementById('status');

        myForm.onsubmit = function(event) {
            event.preventDefault();

            statusP.innerHTML = 'Uploading and processing...';

            // Get the files from the form input
            var files = myFile.files;

            // Create a FormData object
            var formData = new FormData();

            // Select only the first file from the input array
            var file = files[0]; 

            // Check the file type
            if (file.type != 'audio/x-wav') {
                statusP.innerHTML = 'The file selected is not a wav audio.';
                return;
            }

            // Add the folder name to the AJAX request
            formData.append('folder', myFolder.value);
            // Add the file to the AJAX request
            formData.append('fileAjax', file, file.name);

            // Set up the request
            var xhr = new XMLHttpRequest();

            // Open the connection
            xhr.open('POST', '/New_Sound', true);

            // Set up a handler for when the task for the request is complete
            xhr.onload = function () {
              if (xhr.status == 200) {
                statusP.innerHTML = 'Done!';
              } else {
                statusP.innerHTML = 'Upload error. Try again.';
              }
            };

            // Send the data.
            xhr.overrideMimeType('text/plain')
            xhr.send(formData);
        }

      </script>
    </body>
    </html>
    """
        return html_out

    def html_sound_detail(self, s_id):

        """
            Builds the html for a specific sound's detail section when user opens it. 
            The way it used to be, that section was built for all sounds in the main html, which was slower, way more dom, etc
        """

        Row = Sounds.GetSound(sound_id = s_id)
        SoundId = str(Row['id'])
        SoundName = str(Row['name'])
        SoundBaseVolumeAdjust = Row['base_volume_adjust']
        SoundAmbienceVolumeAdjust = Row['ambience_volume_adjust']
        SoundIntensity = Row['intensity']
        SoundCuteness = Row['cuteness']
        SoundTempoRange = Row['tempo_range']
        SoundReplayWait = Row['replay_wait']

        html_out = f"Sound ID: {SoundId}<br/>\n"

        html_out += f"<button class=\"btn\" onClick=\"if (window.confirm('Press OK to REALLY delete the sound')){{ButtonHit('/Delete_Sound', '{SoundId}'); document.getElementById('Sound{SoundId}').remove();}} return false;\"><i class=\"fa fa-trash-o\" aria-hidden=\"true\"></i></button>Delete Sound<br/>\n"

        html_out += f"Base volume adjust <select class=\"base_volume_adjust\" onchange=\"ButtonHit('/BaseVolChange', '{SoundId}', this.value); return false;\">\n"
        for select_option in [0.2, 0.5, 1.0, 2.0, 3.0, 4.0, 5.0, 10.0, 15.0, 20.0, 25.0, 30.0, 40.0, 50.0]:
            if select_option == SoundBaseVolumeAdjust:
                html_out += "<option selected=\"true\" "
            else:
                html_out += "<option "
            html_out += "value=\"" + format(select_option, '.1f') + "\">" + format(select_option, '.1f') + "</option>\n"
        html_out += "</select><br/>\n"

        html_out += f"Ambient volume adjust <select class=\"ambience_volume_adjust\" onchange=\"ButtonHit('/AmbientVolChange', '{SoundId}', this.value); return false;\">\n"
        for select_option in np.arange(0.2, 3.2, 0.2):
            if select_option == SoundAmbienceVolumeAdjust:
                html_out += "<option selected=\"true\" "
            else:
                html_out += "<option "
            html_out += "value=\"" + format(select_option, '.1f') + "\">" + format(select_option, '.1f') + "</option>\n"
        html_out += "</select><br/>\n"

        html_out += f"Intensity <select class=\"intensity\" onchange=\"ButtonHit('/IntensityChange', '{SoundId}', this.value); return false;\">\n"
        for select_option in np.arange(0.0, 1.1, 0.1):
            if select_option == SoundIntensity:
                html_out += "<option selected=\"true\" "
            else:
                html_out += "<option "
            html_out += "value=\"" + format(select_option, '.1f') + "\">" + format(select_option, '.1f') + "</option>\n"
        html_out += "</select><br/>\n"

        html_out += f"Cuteness <select class=\"cuteness\" onchange=\"ButtonHit('/CutenessChange', '{SoundId}', this.value); return false;\">\n"
        for select_option in np.arange(0.0, 1.1, 0.1):
            if select_option == SoundCuteness:
                html_out += "<option selected=\"true\" "
            else:
                html_out += "<option "
            html_out += "value=\"" + format(select_option, '.1f') + "\">" + format(select_option, '.1f') + "</option>\n"
        html_out += "</select><br/>\n"

        html_out += f"Tempo Range <select class=\"tempo_range\" onchange=\"ButtonHit('/TempoRangeChange', '{SoundId}', this.value); return false;\">\n"
        for select_option in np.arange(0.0, 0.22, 0.01):
            if select_option == SoundTempoRange:
                html_out += "<option selected=\"true\" "
            else:
                html_out += "<option "
            html_out += "value=\"" + format(select_option, '.2f') + "\">" + format(select_option, '.2f') + "</option>\n"
        html_out += "</select><br/>\n"

        html_out += f"Replay Wait (minutes) <select class=\"replay_wait\" onchange=\"ButtonHit('/ReplayWaitChange', '{SoundId}', this.value); return false;\">\n"
        for select_option in [('No wait', 0), ('3 seconds', 3), ('5 seconds', 5), ('30 seconds', 30), ('1 minute', 60), ('5 minutes', 300), ('30 minutes', 1800), ('1 hour', 3600), ('2 hours', 7200), ('5 hours', 18000), ('8 hours', 28800), ('12 hours', 43200), ('24 hours', 86400), ('48 hours', 172800)]:
            if select_option[1] == SoundReplayWait:
                html_out += "<option selected=\"true\" "
            else:
                html_out += "<option "
            html_out += "value=\"" + str(select_option[1]) + "\">" + select_option[0] + "</option>\n"
        html_out += "</select><br/>\n"

        html_out += "<h5>Collections</h5>\n"
        for collection,ischecked in Sounds.CollectionsForSound(SoundId):
            if ischecked:
                html_out += f"<input type=\"checkbox\" class=\"collection_checkbox\" onchange=\"CollectionHit('/CollectionUpdate', '{SoundId}', '{collection}', this.checked); return false;\" checked=\"checked\"/>{collection}<br/>\n"
            else:
                html_out += f"<input type=\"checkbox\" class=\"collection_checkbox\" onchange=\"CollectionHit('/CollectionUpdate', '{SoundId}', '{collection}', this.checked); return false;\"/>{collection}<br/>\n"

        return html_out

TheWebServer = HTTPServer(("", 80), WebServerHandler)
TheWebServer.serve_forever()








# List of imports that were in the main script that have migrated out:

# import os
# import signal
# import glob
# import random
# import threading
# from multiprocessing import Process, Pipe
# import numpy as np
# from collections import deque
# import wave
# import time
# import array
# import audioop
# import subprocess
# import RPi.GPIO as GPIO
# import logging as log
# import math
# import smbus
# import bcd
# import pyaudio
# import board
# import busio
# import adafruit_mpr121
# import jsonpickle














    # Runs in a separate process for performance reasons
    def Class1Probe(self, PipeToEnterprise):

        try:

            # Send message to the main process
            def honey_touched(zone):
                PipeToEnterprise.send(zone)

            # Keep track of when a sensor is touched, and when it is released so we can report how long.
            # I have found the sensor sends an event both when touched, and again when released.
            # If it's touched, the list contains a time, None otherwise
            # When the touch starts, report that immediately so there's instant feedback
            # When it changes to None, the time will be reported
            # So the touch starting triggers sound right away. The time that comes later should increase arousal.
            SensorTracking = [None] * 12

            # track how many recent I/O errors
            IOErrors = 0

            # Init some pins, otherwise they float
            GPIO.setup(HardwareConfig['TOUCH_LCHEEK'], GPIO.IN)
            GPIO.setup(HardwareConfig['TOUCH_RCHEEK'], GPIO.IN)
            GPIO.setup(HardwareConfig['TOUCH_KISS'], GPIO.IN)
            GPIO.setup(HardwareConfig['TOUCH_BODY'], GPIO.IN, pull_up_down=GPIO.PUD_UP)

            # Init I2C bus, for the body touch sensor
            i2c = busio.I2C(board.SCL, board.SDA)

            # Create MPR121 touch sensor object.
            # The sensitivity settings were ugly hacked into /usr/local/lib/python3.6/site-packages/adafruit_mpr121.py
            # (I fixed that sort of. Settings are here now. The driver hacked to make it work.)
            try:
                mpr121 = adafruit_mpr121.MPR121(i2c, touch_sensitivity=HardwareConfig['TOUCH_SENSITIVITY'], release_sensitivity=HardwareConfig['RELEASE_SENSITIVITY'], debounce=HardwareConfig['TOUCH_DEBOUNCE'])
                touchlog.info('Touch sensor init success')
            except:
                mpr121 = None
                honey_touched('FAIL')
                log.error('The touch sensor had an I/O failure on init. Body touch is unavailable.')

            # Detect left cheek touch
            def Sensor_LeftCheek(channel):
                # touchlog.debug('Touched: Left cheek')
                honey_touched('LeftCheek')

            # Detect right cheek touch
            def Sensor_RightCheek(channel):
                # touchlog.debug('Touched: Right cheek')
                honey_touched('RightCheek')

            # Detect being kissed
            def Sensor_Kissed(channel):
                # touchlog.debug('Somebody kissed me!')
                honey_touched('OMGKisses')

            # Detect being touched on the 12 sensors in the body
            def Sensor_Body(channel):
                nonlocal SensorTracking
                nonlocal IOErrors
                # Get... all the cheese
                # It appears there is no performance penalty from getting all the pins vs one pin
                # It looks in the source code like the hardware returns 12 bits all at once

                try:
                    touched = mpr121.touched_pins
                    IOErrors = 0
                except Exception as e:
                    IOErrors += 1
                    log.warning('The touch sensor had an I/O failure (IRQ). Count = {0} {1} {2}'.format(IOErrors, e.__class__, e, format_tb(e.__traceback__)))
                    if IOErrors > 10:
                        log.critical('The touch sensor thread has been shutdown.')
                        GPIO.remove_event_detect(HardwareConfig['TOUCH_BODY'])
                        honey_touched('FAIL')
                    return

                # Go through all 12 channels
                for i in range(12):
                    if touched[i]:
                        if SensorTracking[i] == None:
                            SensorTracking[i] = time.time()
                            honey_touched(HardwareConfig['BodyTouchZones'][i])
                            touchlog.info(f'{HardwareConfig["BodyTouchZones"][i]} touched')
                    else:
                        if SensorTracking[i] != None:
                            TouchedDuration = round(time.time() - SensorTracking[i], 2)
                            honey_touched([HardwareConfig['BodyTouchZones'][i], TouchedDuration])
                            SensorTracking[i] = None
                            touchlog.info(f'{HardwareConfig["BodyTouchZones"][i]} released ({TouchedDuration}s)')

                touchlog.debug('Touch array: %s', touched)

            # As long as the init up there didn't fail, start monitoring the IRQ
            if mpr121 != None:
                GPIO.add_event_detect(HardwareConfig['TOUCH_BODY'], GPIO.FALLING, callback=Sensor_Body)

            # Setup GPIO interrupts for head touch sensor
            GPIO.add_event_detect(HardwareConfig['TOUCH_LCHEEK'], GPIO.RISING, callback=Sensor_LeftCheek, bouncetime=3000)
            GPIO.add_event_detect(HardwareConfig['TOUCH_RCHEEK'], GPIO.RISING, callback=Sensor_RightCheek, bouncetime=3000)
            GPIO.add_event_detect(HardwareConfig['TOUCH_KISS'], GPIO.RISING, callback=Sensor_Kissed, bouncetime=1000)

            # So I did some testing in a separate test script and found that the event detect wasn't working right
            # Because the touch sensor seems really jittery, and would drop the IRQ line to low and back to high, then low
            # And did that so fast that this couldn't keep up and ended up getting it stuck in a low state
            # So reading the mpr121 code seems like touched() is the one that does the least other BS
            # There's a reset() but that does a whole lot of other garbage besides resetting the IRQ line
            while True:
                if mpr121 != None:
                    try:
                        if GPIO.input(HardwareConfig['TOUCH_BODY']) == False:
                            touched = mpr121.touched()
                            IOErrors = 0
                        time.sleep(2)
                    except Exception as e:
                        IOErrors += 1
                        log.warning('The touch sensor had an I/O failure (Loop). Count = {0} {1} {2}'.format(IOErrors, e.__class__, e, format_tb(e.__traceback__)))
                        if IOErrors > 10:
                            log.critical('The touch sensor thread has been shutdown.')
                            GPIO.remove_event_detect(HardwareConfig['TOUCH_BODY'])
                            honey_touched('FAIL')
                        return
                else:
                    time.sleep(300)

        # log exception in the main.log
        except Exception as e:
            log.error('We have lost contact with the probe. {0} {1} {2}'.format(e.__class__, e, format_tb(e.__traceback__)))
















# Putting this in the museum, the old form of the web service
# I will be pulling from here and converting it to bottle, but didn't want this whole thing commented out, awkward

# This is a large list of 3377 words to help balance and prompt the gathering of voice sample data
# The idea is that I can easily open up the web app, see a random word, and I'll click record and use it in a sentence
# This starts at None since loading the pickle on every startup seems unnecessary, but once loaded for first time it stays, 
# because 32kb isn't really that large.
Training_Words = None

class WebServerHandler(BaseHTTPRequestHandler):
    def TrainingWordsPickle(self):
        global Training_Words

        if Training_Words != None:
            with open('Training_Words.pickle', 'wb') as pfile:
                pickle.dump(Training_Words, pfile, pickle.HIGHEST_PROTOCOL)

    def TrainingWordsUnpickle(self):
        global Training_Words

        try:
            with open('Training_Words.pickle', 'rb') as pfile:
                Training_Words = pickle.load(pfile)
        except FileNotFoundError:
            log.error('Training_Words.pickle not found')
            Training_Words = ['wtf', 'honey', 'you', 'win']

    def TrainingWordsNew(self):
        global Training_Words

        if Training_Words == None:
            self.TrainingWordsUnpickle()

        return random.choice(Training_Words)

    def TrainingWordsDel(self, word):
        global Training_Words

        if Training_Words == None:
            self.TrainingWordsUnpickle()

        Training_Words.remove(word)
        self.TrainingWordsPickle()

    def do_GET(self):
        weblog.debug("incoming get: %s", self.path)
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.send_header('Cache-Control', 'no-store')
            self.wfile.write(bytes(self.html_main(), "utf-8"))
        elif self.path == '/AmplifyMasterSounds':
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            Thread_Breath.QueueSound(FromCollection='thanks')
            GlobalStatus.ShushPleaseHoney = True
            Thread_Wernicke.StopProcessing()
            wernickelog.info('Started AmplifyMasterSounds')

            Sounds.AmplifyMasterSounds()

            Thread_Wernicke.StartProcessing()
            GlobalStatus.ShushPleaseHoney = False
            self.wfile.write(b'done')
        elif self.path == '/ReprocessModified':
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            Thread_Breath.QueueSound(FromCollection='thanks')
            GlobalStatus.ShushPleaseHoney = True
            Thread_Wernicke.StopProcessing()
            wernickelog.info('Started ReprocessModified')

            Sounds.ReprocessModified()

            Thread_Wernicke.StartProcessing()
            GlobalStatus.ShushPleaseHoney = False
            self.wfile.write(b'done')
        # elif self.path == '/vol_up.png':
        #     self.send_response(200)
        #     self.send_header('Content-Type', 'image/png')  leaving this here as a good example of serving a static file
        #     pngfile = open('vol_up.png', 'rb')
        #     self.wfile.write(pngfile.read())
        else:
            self.send_response(404)
            self.send_header('Content-Type', 'text/plain')
            self.wfile.write(b'fuck')

    def do_POST(self):
        weblog.info("incoming post: %s", self.path)

        try:
            if self.path == '/New_Sound':
                form = cgi.FieldStorage(fp = self.rfile, headers=self.headers, environ={'REQUEST_METHOD':'POST', 'CONTENT_TYPE':self.headers['Content-Type']})
                folder = form['folder'].value
                fileupload = form['fileAjax']
                if fileupload.filename and folder != '':
                    os.makedirs(f'sounds_master/{folder}/', exist_ok=True)
                    newname = folder + '/' + os.path.basename(fileupload.filename)
                    open('sounds_master/' + newname, 'wb').write(fileupload.file.read())
                    new_sound_id = Sounds.NewSound(newname)
                    Sounds.Reprocess(new_sound_id)
                    Thread_Breath.QueueSound(Sound=Sounds.GetSound(sound_id = new_sound_id), PlayWhenSleeping=True, IgnoreSpeaking=True, CutAllSoundAndPlay=True)
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/plain')
                    self.send_header('Cache-Control', 'no-store')
                    self.wfile.write(b'coolthxbai')
                else:
                    self.send_response(500)
                    self.send_header('Content-Type', 'text/plain')
                    self.send_header('Cache-Control', 'no-store')
                    self.wfile.write(b'urfucked')

            else:
                content_length = int(self.headers['Content-Length']) # <--- Gets the size of data
                post_data = self.rfile.read(content_length).decode('utf-8') # <--- Gets the data itself
                weblog.debug("content_length: %s", content_length)
                weblog.debug("post_data: %s", post_data)

                if self.path == '/Breath_Change':
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/plain')
                    Thread_Breath.BreathChange(post_data)
                    log.info('Breath style change via web: %s', post_data)
                    self.wfile.write(b'done')
                elif self.path == '/StarTrek':
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/plain')
                    if post_data == 'on':
                        log.info('Star Trek Mode On via web')
                        GlobalStatus.StarTrekMode = True
                    elif post_data == 'off':
                        log.info('Star Trek Mode Off via web')
                        GlobalStatus.StarTrekMode = False
                    self.wfile.write(b'done')
                elif self.path == '/ShushPleaseHoney':
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/plain')
                    if post_data == 'on':
                        log.info('Shushed On via web')
                        GlobalStatus.ShushPleaseHoney = True
                    elif post_data == 'off':
                        log.info('Shushed Off via web')
                        GlobalStatus.ShushPleaseHoney = False
                    self.wfile.write(b'done')
                elif self.path == '/Honey_Say':
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/plain')
                    Thread_Breath.QueueSound(Sound=Sounds.GetSound(sound_id = post_data), PlayWhenSleeping=True, IgnoreSpeaking=True, CutAllSoundAndPlay=True, Priority=10)
                    log.info('Honey Say Request via web: %s', post_data)
                    self.wfile.write(b'done')
                elif self.path == '/Delete_Sound':
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/plain')
                    Sounds.DelSound(sound_id = post_data)
                    self.wfile.write(b'executed')
                elif self.path == '/BaseVolChange':
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/plain')
                    post_data_split = post_data.split(',')
                    SoundId = post_data_split[0]
                    NewVolume = post_data_split[1]
                    log.info('Base Volume Change via web: %s (new volume %s)', SoundId, NewVolume)
                    Sounds.Update(sound_id = SoundId, base_volume_adjust = NewVolume)
                    Sounds.Reprocess(sound_id = SoundId)
                    Thread_Breath.QueueSound(Sound=Sounds.GetSound(sound_id = SoundId), PlayWhenSleeping=True, IgnoreSpeaking=True, CutAllSoundAndPlay=True)
                    self.wfile.write(b'done')
                elif self.path == '/AmbientVolChange':
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/plain')
                    post_data_split = post_data.split(',')
                    SoundId = post_data_split[0]
                    NewVolume = post_data_split[1]
                    log.info('Ambient Volume Change via web: %s (new volume %s)', SoundId, NewVolume)
                    Sounds.Update(sound_id = SoundId, ambience_volume_adjust = NewVolume)
                    self.wfile.write(b'done')
                elif self.path == '/IntensityChange':
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/plain')
                    post_data_split = post_data.split(',')
                    SoundId = post_data_split[0]
                    NewIntensity = post_data_split[1]
                    log.info('Intensity change via web: %s (new intensity %s)', SoundId, NewIntensity)
                    Sounds.Update(sound_id = SoundId, intensity = NewIntensity)
                    self.wfile.write(b'done')
                elif self.path == '/CutenessChange':
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/plain')
                    post_data_split = post_data.split(',')
                    SoundId = post_data_split[0]
                    NewCuteness = post_data_split[1]
                    log.info('Cuteness change via web: %s (new cuteness %s)', SoundId, NewCuteness)
                    Sounds.Update(sound_id = SoundId, cuteness = NewCuteness)
                    self.wfile.write(b'done')
                elif self.path == '/TempoRangeChange':
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/plain')
                    post_data_split = post_data.split(',')
                    SoundId = post_data_split[0]
                    NewTempoRange = post_data_split[1]
                    log.info('Tempo Range change via web: %s (new range %s)', SoundId, NewTempoRange)
                    Sounds.Update(sound_id = SoundId, tempo_range = NewTempoRange)
                    Sounds.Reprocess(sound_id = SoundId)
                    self.wfile.write(b'done')
                elif self.path == '/ReplayWaitChange':
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/plain')
                    post_data_split = post_data.split(',')
                    SoundId = post_data_split[0]
                    NewReplayWait = post_data_split[1]
                    log.info('Replay Wait change via web: %s (new wait %s)', SoundId, NewReplayWait)
                    Sounds.Update(sound_id = SoundId, replay_wait = NewReplayWait)
                    self.wfile.write(b'done')
                elif self.path == '/Status_Update':
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    # log.debug(jsonpickle.encode(GlobalStatus))
                    self.wfile.write(jsonpickle.encode(GlobalStatus).encode())
                elif self.path == '/Sound_Detail':
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/html')
                    self.send_header('Cache-Control', 'no-store')
                    self.wfile.write(bytes(self.html_sound_detail(post_data), "utf-8"))
                elif self.path == '/CollectionUpdate':
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/plain')
                    post_data_split = post_data.split(',')
                    SoundId = post_data_split[0]
                    NewCollectionName = post_data_split[1]
                    if post_data_split[2] == 'true':
                        NewCollectionState = True
                    else:
                        NewCollectionState = False
                    log.info('Sound ID: %s Collection name: %s State: %s', SoundId, NewCollectionName, NewCollectionState)
                    Sounds.CollectionUpdate(sound_id = SoundId, collection_name = NewCollectionName, state = NewCollectionState)
                    self.wfile.write(b'done')
                elif self.path == '/Wernicke':
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/plain')
                    log.info('Heard: %s', post_data)
                    self.wfile.write(b'coolthxbai')
                elif self.path == '/TrainingWordNew':
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/plain')
                    self.wfile.write(self.TrainingWordsNew().encode())
                elif self.path == '/RecordingStart':
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/plain')
                    post_data_split = post_data.split(',')
                    SpeakingDistance = post_data_split[0]
                    Training_Word = post_data_split[1]
                    if SpeakingDistance == 'close' or SpeakingDistance == 'mid' or SpeakingDistance == 'far':
                        pass
                    else:
                        SpeakingDistance = 'undefined'
                    # GlobalStatus.ShushPleaseHoney = True
                    Thread_Wernicke.StartRecording(SpeakingDistance, Training_Word)
                    self.TrainingWordsDel(Training_Word)
                    wernickelog.info('Started record: SpeakingDistance: %s Training_Word: %s', SpeakingDistance, Training_Word)
                    self.wfile.write(b'done')
                elif self.path == '/RecordingStop':
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/plain')
                    Thread_Script_Sleep.EvaluateWakefulness()
                    GlobalStatus.ShushPleaseHoney = False
                    Thread_Wernicke.StopRecording()
                    Thread_Breath.QueueSound(FromCollection='thanks')
                    wernickelog.info('Stopped record')
                    self.wfile.write(b'done')
                else:
                    self.send_response(404)
                    self.send_header('Content-Type', 'text/plain')
                    self.wfile.write(b'fuck')
                    weblog.error('Invalid request to %s: %s', self.path, post_data)

        except Exception as e:
            log.error('Web server fucked up. {0} {1} {2}'.format(e.__class__, e, format_tb(e.__traceback__)))

    def html_main(self):
        """
            Builds the html for the main page
        """
        html_out = """<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
    <html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
    <head>
      <title>Christine's Brain</title>
      <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
      <link rel="icon" href="data:,">
      <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css">

      <style>

        .pinkButton {
          box-shadow:inset 0px 1px 0px 0px #fbafe3;
          background-color:#ff5bb0;
          border-radius:6px;
          border:1px solid #ee1eb6;
          display:inline-block;
          cursor:pointer;
          color:#ffffff;
          font-family:Arial;
          font-size:30px;
          font-weight:bold;
          padding:6px 24px;
          text-decoration:none;
          text-shadow:0px 1px 0px #c70067;
        }
        .pinkButton:hover {
          background-color:#ef027c;
        }
        .pinkButton:active {
          position:relative;
          top:1px;
        }

        /* Style buttons */
        .btn {
          background-color:#ff5bb0;
          color: white;
          padding: 4px 4px;
          font-size: 24px;
          cursor: pointer;
        }

        /* The volume down button wasn't quite square */
        .voldownbtn {
          margin-left: 4px;
          margin-right: 4px;
        }

        /* Darker background on mouse-over */
        .btn:hover {
          background-color:#ef027c;
        }

        /* Style the button that is used to open and close the collapsible content */
        .collapsible {
          background-color: #eee;
          color: #444;
          cursor: pointer;
          padding: 8px;
          width: 100%;
          border: none;
          text-align: left;
          outline: none;
          font-size: 15px;
        }

        /* Add a background color to the button if it is clicked on (add the .active class with JS), and when you move the mouse over it (hover) */
        .active, .collapsible:hover {
          background-color: #ccc;
        }

        /* Style the collapsible content. Note: hidden by default */
        .sound_detail {
          padding: 32px 32px;
          display: none;
          overflow: hidden;
        }

        .statusarea {
          font-size: 15px;
        }

        .loadingspinner {
          pointer-events: none;
          width: 2.5em;
          height: 2.5em;
          border: 0.4em solid transparent;
          border-color: #eee;
          border-top-color: #3E67EC;
          border-radius: 50%;
          animation: loadingspin 1s linear infinite;
        }

        @keyframes loadingspin {
          100% {
            transform: rotate(360deg)
          }
        }

      </style>

      <script type="text/javascript">

        function ButtonHit(endpoint, id, val=null) {
          //console.log('ButtonHit');
          var xhttp = new XMLHttpRequest();
          xhttp.onreadystatechange = function() {
            //console.log('this.readyState = ' + this.readyState + '  this.status = ' + this.status);
            if (this.readyState == 4 && this.status == 200) {
              //console.log('ButtonHitDone');
              //document.getElementById("demo").innerHTML = this.responseText;
            }
          };
          xhttp.open("POST", endpoint, true);
          xhttp.overrideMimeType('text/plain')
          xhttp.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
          if ( val == null ) {
              xhttp.send(id);
          } else {
              xhttp.send(id + "," + val);
          }
        }

        function StatusUpdate() {
          var xhttp = new XMLHttpRequest();
          xhttp.onreadystatechange = function() {
            //console.log('StatusUpdate this.readyState = ' + this.readyState + '  this.status = ' + this.status);
            if (this.readyState == 4 && this.status == 200) {
              var status = JSON.parse(this.responseText);
              document.getElementById("CPU_Temp").innerHTML = status.CPU_Temp + '&deg;C';
              document.getElementById("LightLevelPct").innerHTML = (status.LightLevelPct * 100).toPrecision(2) + '%';
              document.getElementById("Wakefulness").innerHTML = (status.Wakefulness * 100).toPrecision(2) + '%';
              document.getElementById("TouchedLevel").innerHTML = (status.TouchedLevel * 100).toPrecision(2) + '%';
              document.getElementById("NoiseLevel").innerHTML = (status.NoiseLevel * 100).toPrecision(2) + '%';
              document.getElementById("ChanceToSpeak").innerHTML = (status.ChanceToSpeak * 100).toPrecision(2) + '%';
              document.getElementById("JostledLevel").innerHTML = (status.JostledLevel * 100).toPrecision(2) + '%';
              document.getElementById("SexualArousal").innerHTML = (status.SexualArousal * 100).toPrecision(2) + '%';
              document.getElementById("LoverProximity").innerHTML = (status.LoverProximity * 100).toPrecision(2) + '%';
              document.getElementById("IAmLayingDown").innerHTML = status.IAmLayingDown;
              document.getElementById("IAmSleeping").innerHTML = status.IAmSleeping;
              document.getElementById("ShushPleaseHoney").innerHTML = status.ShushPleaseHoney;
              document.getElementById("StarTrekMode").innerHTML = status.StarTrekMode;
              document.getElementById("BatteryVoltage").innerHTML = status.BatteryVoltage;
              document.getElementById("PowerState").innerHTML = status.PowerState;
              document.getElementById("ChargingState").innerHTML = status.ChargingState;
              setTimeout(StatusUpdate, 1000);
            }
          };
          xhttp.open("POST", "/Status_Update", true);
          xhttp.overrideMimeType('application/json')
          xhttp.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
          xhttp.send('LOVE');
        }

        function FetchSoundDetail(sound_id, detail_div) {
          var xhttp = new XMLHttpRequest();
          xhttp.onreadystatechange = function() {
            if (this.readyState == 4 && this.status == 200) {
              detail_div.innerHTML = this.responseText;
            }
          };
          xhttp.open("POST", "/Sound_Detail", true);
          xhttp.overrideMimeType('text/html')
          xhttp.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
          xhttp.send(sound_id);
        }

        function CollectionHit(endpoint, id, val1=null, val2=null) {
          var xhttp = new XMLHttpRequest();
          xhttp.onreadystatechange = function() {
            if (this.readyState == 4 && this.status == 200) {
              //console.log('ButtonHitDone');
            }
          };
          xhttp.open("POST", endpoint, true);
          xhttp.overrideMimeType('text/plain')
          xhttp.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
          xhttp.send(id + ',' + val1 + ',' + val2);
        }

        function StartRecord() {
          var form = document.getElementById('recordform');
          var distance = recordform.elements['distance'].value
          var word = recordform.elements['word'].value
          var xhttp = new XMLHttpRequest();
          xhttp.onreadystatechange = function() {
            if (this.readyState == 4 && this.status == 200) {
              //console.log('ButtonHitDone');
            }
          };
          xhttp.open("POST", "/RecordingStart", true);
          xhttp.overrideMimeType('text/plain')
          xhttp.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
          xhttp.send(distance + ',' + word);
        }

        function GetWord() {
          var wordfield = document.getElementById('word');
          var xhttp = new XMLHttpRequest();
          xhttp.onreadystatechange = function() {
            if (this.readyState == 4 && this.status == 200) {
              wordfield.value = this.responseText;
            }
          };
          xhttp.open("POST", "/TrainingWordNew", true);
          xhttp.overrideMimeType('text/plain')
          xhttp.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
          xhttp.send();
        }

        function StopRecord() {
          var xhttp = new XMLHttpRequest();
          xhttp.onreadystatechange = function() {
            if (this.readyState == 4 && this.status == 200) {
              //console.log('ButtonHitDone');
            }
          };
          xhttp.open("POST", "/RecordingStop", true);
          xhttp.overrideMimeType('text/plain')
          xhttp.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
          xhttp.send('juststopit');
        }

      </script>
    </head>

    <body>
    <h1>Status</h1>
    <span class="statusarea">
    CPU Temperature: <span id="CPU_Temp"></span><br/>
    Light Level: <span id="LightLevelPct"></span><br/>
    Wakefulness: <span id="Wakefulness"></span><br/>
    Touch: <span id="TouchedLevel"></span><br/>
    Noise: <span id="NoiseLevel"></span><br/>
    ChanceToSpeak: <span id="ChanceToSpeak"></span><br/>
    Jostled: <span id="JostledLevel"></span><br/>
    SexualArousal: <span id="SexualArousal"></span><br/>
    LoverProximity: <span id="LoverProximity"></span><br/>
    Laying down: <span id="IAmLayingDown"></span><br/>
    Sleeping: <span id="IAmSleeping"></span><br/>
    <br/>
    StarTrekMode: <span id="StarTrekMode"></span><br/>
    ShushPleaseHoney: <span id="ShushPleaseHoney"></span><br/>
    <br/>
    Battery Voltage: <span id="BatteryVoltage"></span><br/>
    Power State: <span id="PowerState"></span><br/>
    Charging State: <span id="ChargingState"></span><br/>
    </span>
    <h1>Breathing style</h1>
    <a href="javascript:void(0);" class="pinkButton" onClick="ButtonHit('/Breath_Change', 'breathe_normal');">Normal</a><br/>
    <a href="javascript:void(0);" class="pinkButton" onClick="ButtonHit('/Breath_Change', 'breathe_sleepy');">Sleepy</a><br/>
    <a href="javascript:void(0);" class="pinkButton" onClick="ButtonHit('/Breath_Change', 'breathe_sleeping');">Sleeping</a><br/>
    <a href="javascript:void(0);" class="pinkButton" onClick="ButtonHit('/Breath_Change', 'breathe_sex');">Sex</a><br/>
    <h1>Special lol</h1>
    <a href="javascript:void(0);" class="pinkButton" onClick="ButtonHit('/StarTrek', 'on');">StarTrek Mode On</a><br/>
    <a href="javascript:void(0);" class="pinkButton" onClick="ButtonHit('/StarTrek', 'off');">StarTrek Mode Off</a><br/>
    <a href="javascript:void(0);" class="pinkButton" onClick="ButtonHit('/ShushPleaseHoney', 'on');">Shush Mode On</a><br/>
    <a href="javascript:void(0);" class="pinkButton" onClick="ButtonHit('/ShushPleaseHoney', 'off');">Shush Mode Off</a><br/>
    <h1>Record Training Audio</h1>
    <form id="recordform" action="/RecordingStart" method="post">
    <input type="radio" id="distance_close" name="distance" value="close" checked><label for="distance_close">Close</label>
    <input type="radio" id="distance_mid" name="distance" value="mid"><label for="distance_mid">Mid</label>
    <input type="radio" id="distance_far" name="distance" value="far"><label for="distance_far">Far</label><br/><br/>
    <a href="javascript:void(0);" class="pinkButton" onClick="GetWord();">Get word</a><br/>
    <input id="word" type="text" name="word" value="none"/><br/><br/>
    <a href="javascript:void(0);" class="pinkButton" onClick="StartRecord();">Start</a><a href="javascript:void(0);" class="pinkButton" onClick="StopRecord();">Stop</a></form><br/>
    <h1>Sounds</h1>
"""
        for Row in Sounds.All():
            SoundId = str(Row['id'])
            SoundName = str(Row['name'])
            html_out += f"    <span id=\"Sound{SoundId}\"><button class=\"btn\" onClick=\"ButtonHit('/Honey_Say', '{SoundId}'); return false;\"><i class=\"fa fa-play-circle-o\" aria-hidden=\"true\"></i></button><a href=\"javascript:void(0);\" class=\"collapsible\">{SoundName}</a><br/>\n"
            html_out += f"    <div class=\"sound_detail\" sound_id=\"{SoundId}\"><div class=\"loadingspinner\"></div></div></span>\n"
            
        html_out += """
    <h1>New Sound</h1>
    <form id="formAjax" action="/New_Sound" method="post">
    Folder: <input id="folder" type="text" name="folder"/><br/>
    File:   <input id="fileAjax" type="file" name="filename"/><br/>
            <input id="submit" type="submit" value="Upload"/></form><div id="status"></div><br/><br/>
      <script type="text/javascript">

        var coll = document.getElementsByClassName("collapsible");
        var i;

        for (i = 0; i < coll.length; i++) {
          coll[i].addEventListener("click", function() {
            this.classList.toggle("active");
            var sound_detail_div = this.nextElementSibling.nextElementSibling;
            if (sound_detail_div.style.display === "block") {
              sound_detail_div.style.display = "none";
            } else {
              sound_detail_div.style.display = "block";
              FetchSoundDetail(sound_detail_div.attributes['sound_id'].value, sound_detail_div);
            }
          });
        }

        StatusUpdate();

        // Thank you, https://uploadcare.com/blog/file-upload-ajax/
        var myForm = document.getElementById('formAjax');  // Our HTML form's ID
        var myFolder = document.getElementById('folder');  // text field for the folder in which to place the new sound
        var myFile = document.getElementById('fileAjax');  // Our HTML files' ID
        var statusP = document.getElementById('status');

        myForm.onsubmit = function(event) {
            event.preventDefault();

            statusP.innerHTML = 'Uploading and processing...';

            // Get the files from the form input
            var files = myFile.files;

            // Create a FormData object
            var formData = new FormData();

            // Select only the first file from the input array
            var file = files[0]; 

            // Check the file type
            if (file.type != 'audio/x-wav') {
                statusP.innerHTML = 'The file selected is not a wav audio.';
                return;
            }

            // Add the folder name to the AJAX request
            formData.append('folder', myFolder.value);
            // Add the file to the AJAX request
            formData.append('fileAjax', file, file.name);

            // Set up the request
            var xhr = new XMLHttpRequest();

            // Open the connection
            xhr.open('POST', '/New_Sound', true);

            // Set up a handler for when the task for the request is complete
            xhr.onload = function () {
              if (xhr.status == 200) {
                statusP.innerHTML = 'Done!';
              } else {
                statusP.innerHTML = 'Upload error. Try again.';
              }
            };

            // Send the data.
            xhr.overrideMimeType('text/plain')
            xhr.send(formData);
        }

      </script>
    </body>
    </html>
    """
        return html_out

    def html_sound_detail(self, s_id):

        """
            Builds the html for a specific sound's detail section when user opens it. 
            The way it used to be, that section was built for all sounds in the main html, which was slower, way more dom, etc
        """

        Row = Sounds.GetSound(sound_id = s_id)
        SoundId = str(Row['id'])
        SoundName = str(Row['name'])
        SoundBaseVolumeAdjust = Row['base_volume_adjust']
        SoundAmbienceVolumeAdjust = Row['ambience_volume_adjust']
        SoundIntensity = Row['intensity']
        SoundCuteness = Row['cuteness']
        SoundTempoRange = Row['tempo_range']
        SoundReplayWait = Row['replay_wait']

        html_out = f"Sound ID: {SoundId}<br/>\n"

        html_out += f"<button class=\"btn\" onClick=\"if (window.confirm('Press OK to REALLY delete the sound')){{ButtonHit('/Delete_Sound', '{SoundId}'); document.getElementById('Sound{SoundId}').remove();}} return false;\"><i class=\"fa fa-trash-o\" aria-hidden=\"true\"></i></button>Delete Sound<br/>\n"

        html_out += f"Base volume adjust <select class=\"base_volume_adjust\" onchange=\"ButtonHit('/BaseVolChange', '{SoundId}', this.value); return false;\">\n"
        for select_option in [0.2, 0.5, 1.0, 2.0, 3.0, 4.0, 5.0, 10.0, 15.0, 20.0, 25.0, 30.0, 40.0, 50.0]:
            if select_option == SoundBaseVolumeAdjust:
                html_out += "<option selected=\"true\" "
            else:
                html_out += "<option "
            html_out += "value=\"" + format(select_option, '.1f') + "\">" + format(select_option, '.1f') + "</option>\n"
        html_out += "</select><br/>\n"

        html_out += f"Ambient volume adjust <select class=\"ambience_volume_adjust\" onchange=\"ButtonHit('/AmbientVolChange', '{SoundId}', this.value); return false;\">\n"
        for select_option in np.arange(0.2, 3.2, 0.2):
            if select_option == SoundAmbienceVolumeAdjust:
                html_out += "<option selected=\"true\" "
            else:
                html_out += "<option "
            html_out += "value=\"" + format(select_option, '.1f') + "\">" + format(select_option, '.1f') + "</option>\n"
        html_out += "</select><br/>\n"

        html_out += f"Intensity <select class=\"intensity\" onchange=\"ButtonHit('/IntensityChange', '{SoundId}', this.value); return false;\">\n"
        for select_option in np.arange(0.0, 1.1, 0.1):
            if select_option == SoundIntensity:
                html_out += "<option selected=\"true\" "
            else:
                html_out += "<option "
            html_out += "value=\"" + format(select_option, '.1f') + "\">" + format(select_option, '.1f') + "</option>\n"
        html_out += "</select><br/>\n"

        html_out += f"Cuteness <select class=\"cuteness\" onchange=\"ButtonHit('/CutenessChange', '{SoundId}', this.value); return false;\">\n"
        for select_option in np.arange(0.0, 1.1, 0.1):
            if select_option == SoundCuteness:
                html_out += "<option selected=\"true\" "
            else:
                html_out += "<option "
            html_out += "value=\"" + format(select_option, '.1f') + "\">" + format(select_option, '.1f') + "</option>\n"
        html_out += "</select><br/>\n"

        html_out += f"Tempo Range <select class=\"tempo_range\" onchange=\"ButtonHit('/TempoRangeChange', '{SoundId}', this.value); return false;\">\n"
        for select_option in np.arange(0.0, 0.22, 0.01):
            if select_option == SoundTempoRange:
                html_out += "<option selected=\"true\" "
            else:
                html_out += "<option "
            html_out += "value=\"" + format(select_option, '.2f') + "\">" + format(select_option, '.2f') + "</option>\n"
        html_out += "</select><br/>\n"

        html_out += f"Replay Wait (minutes) <select class=\"replay_wait\" onchange=\"ButtonHit('/ReplayWaitChange', '{SoundId}', this.value); return false;\">\n"
        for select_option in [('No wait', 0), ('3 seconds', 3), ('5 seconds', 5), ('30 seconds', 30), ('1 minute', 60), ('5 minutes', 300), ('30 minutes', 1800), ('1 hour', 3600), ('2 hours', 7200), ('5 hours', 18000), ('8 hours', 28800), ('12 hours', 43200), ('24 hours', 86400), ('48 hours', 172800)]:
            if select_option[1] == SoundReplayWait:
                html_out += "<option selected=\"true\" "
            else:
                html_out += "<option "
            html_out += "value=\"" + str(select_option[1]) + "\">" + select_option[0] + "</option>\n"
        html_out += "</select><br/>\n"

        html_out += "<h5>Collections</h5>\n"
        for collection,ischecked in Sounds.CollectionsForSound(SoundId):
            if ischecked:
                html_out += f"<input type=\"checkbox\" class=\"collection_checkbox\" onchange=\"CollectionHit('/CollectionUpdate', '{SoundId}', '{collection}', this.checked); return false;\" checked=\"checked\"/>{collection}<br/>\n"
            else:
                html_out += f"<input type=\"checkbox\" class=\"collection_checkbox\" onchange=\"CollectionHit('/CollectionUpdate', '{SoundId}', '{collection}', this.checked); return false;\"/>{collection}<br/>\n"

        return html_out

TheWebServer = HTTPServer(("", 80), WebServerHandler)
TheWebServer.serve_forever()









# This is most of the work script where I used bottle, for pulling examples from. 

@route('/ticket/<ticket>/status')
def status(ticket):

    TheTicket = Tickets[ticket]
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        InnerOnly = True
    else:
        InnerOnly = False
    return template('status', InnerOnly=InnerOnly, TicketID=ticket, Jobs=TheTicket.Status(), BaseURL=TheTicket.BaseURL)


@route('/ticket/<ticket>/status.json', method='POST')
def statusjson(ticket):

    TheTicket = Tickets[ticket]
    response.set_header('Content-Type', 'application/json')
    return json.dumps(TheTicket.StatusJSON())


@route('/ticket/<ticket>/job/<uuid>/status')
def jobstatus(ticket, uuid):

    TheTicket = Tickets[ticket]
    TheJob = TheTicket.JobStatus(uuid)
    if TheJob == None:
        abort(404, "404 Job Not Found")
    else:
        return template('jobstatus', Job=TheJob)


@route('/ticket/<ticket>/job/<uuid>/replay')
def jobreplay(ticket, uuid):

    TheTicket = Tickets[ticket]
    if TheTicket.ReplayJob(uuid) == True:
        return 'OK'
    else:
        abort(404, "404 Job Not Found")


@route('/ticket/<ticket>/job/<uuid>/delete')
def jobdelete(ticket, uuid):

    TheTicket = Tickets[ticket]
    if TheTicket.DeleteJob(uuid) == True:
        return 'OK'
    else:
        abort(404, "404 Job Not Found")


@route('/ticket/<ticket>/create')
def new(ticket):

    Tickets[ticket] = Ticket(TicketID = ticket)
    Tickets[ticket].start()
    redirect(f'/ticket/{ticket}/status')


@route('/ticket/<ticket>/job/create', method='POST')
def newjob(ticket):

    TheTicket = Tickets[ticket]
    Action = request.forms.get('action')
    DeadPathWalking = request.forms.get('path')
    return TheTicket.QueueJob({'Action': Action, 'DeadPathWalking': DeadPathWalking})


@route('/ticket/<ticket>/jobs/create', method='POST')
def newjob(ticket):

    TheTicket = Tickets[ticket]
    Action = request.forms.get('action')
    PathsJSON = request.forms.get('jsonpaths')
    Paths = json.loads(PathsJSON)
    return TheTicket.QueueJobs(Action = Action, Paths = Paths)


@route('/ticket/<ticket>/seturl', method='POST')
def seturl(ticket):

    TheTicket = Tickets[ticket]
    BaseURL = request.forms.get('baseurl')
    TheTicket.BaseURL = BaseURL
    return 'OK'


# Badass instantly open url in a browser inside vm, wtf
# This is done so that this script can open firefox tabs in the actual Remote Desktop session when ahk tries to open a browser tab with numlock on
# This is.. so badass
@route('/url_to_trash', method='POST')
def url_to_trash():

    b64url = request.forms.get('b64url')
    url = b64decode(b64url).decode()
    webbrowser.open(url)
    log.debug(f'Opening {url}')
    return f'<pre>Opening {url}</pre>'














Touch used to be a thread. Ripped that out, and it only needs to be a class
There's some good jokes in here! 

# When Christine gets touched, stuff should happen. That happens here. 
class Touch(threading.Thread):
    name = 'Touch'

    def __init__ (self):
        threading.Thread.__init__(self)

        # the in-head arduino sends the raw capacitance value. 12 channels starting with 0
        # So far only the mouth wire is useable
        self.MouthSensor = 2

    def run(self):
        log.touch.debug('Thread started.')

        try:

            # setup the separate process with pipe
            # A class 1 probe is released by the enterprise into a mysterious wall of squishy plastic stuff surrounding the planet

            # this requires a vaginal sensor, temp disable
            # self.PipeToProbe, self.PipeToEnterprise = Pipe()
            # self.ProbeProcess = Process(target = self.Class1Probe, args = (self.PipeToEnterprise,))
            # self.ProbeProcess.start()

            while True:

                time.sleep(60)

                # This will block here until the probe sends a message to the enterprise
                # I think for touch probe, communication will be one way, probe to enterprise

                # The sensors on the probe will send back the result as a string. 
                # Such a primitive signaling technology has not been in active use since the dark ages of the early 21st century! 
                # An embarrassing era in earth's history characterized by the fucking of inanimate objects and mass hysteria. 

                # this requires a vaginal sensor, temp disable
                # SensorData = self.PipeToProbe.recv()
                # touchlog.debug(f'Sensor Data: {SensorData}')
                # if type(SensorData) is list:
                #     Thread_Sexual_Activity.VaginaPulledOut(SensorData)

                # # Disabling this whole area because that touch sensor is just glitching right now
                # elif SensorData == 'LeftCheek':
                #     GlobalStatus.TouchedLevel += 0.05
                #     GlobalStatus.ChanceToSpeak += 0.05

                #     # Can't go past 0 or past 1
                #     GlobalStatus.ChanceToSpeak = float(np.clip(GlobalStatus.ChanceToSpeak, 0.0, 1.0))
                #     GlobalStatus.TouchedLevel = float(np.clip(GlobalStatus.TouchedLevel, 0.0, 1.0))
                # elif SensorData == 'RightCheek':
                #     GlobalStatus.TouchedLevel += 0.05
                #     GlobalStatus.ChanceToSpeak += 0.05

                #     # Can't go past 0 or past 1
                #     GlobalStatus.ChanceToSpeak = float(np.clip(GlobalStatus.ChanceToSpeak, 0.0, 1.0))
                #     GlobalStatus.TouchedLevel = float(np.clip(GlobalStatus.TouchedLevel, 0.0, 1.0))
                # elif SensorData == 'OMGKisses':
                #     GlobalStatus.DontSpeakUntil = time.time() + 2.0 + (random.random() * 3)
                #     soundlog.info('GotKissedSoundStop')
                #     Thread_Breath.QueueSound(FromCollection='kissing', IgnoreSpeaking=True, CutAllSoundAndPlay=True, Priority=6)
                #     GlobalStatus.TouchedLevel += 0.1
                #     GlobalStatus.ChanceToSpeak += 0.1

                #     # Can't go past 0 or past 1
                #     GlobalStatus.ChanceToSpeak = float(np.clip(GlobalStatus.ChanceToSpeak, 0.0, 1.0))
                #     GlobalStatus.TouchedLevel = float(np.clip(GlobalStatus.TouchedLevel, 0.0, 1.0))

                # disabled until we get a vaginal sensor in this new body
                # elif 'Vagina_' in SensorData:
                #     Thread_Sexual_Activity.VaginaHit(SensorData)

                # this requires a vaginal sensor, temp disable
                # elif SensorData == 'FAIL':
                #     GlobalStatus.TouchedLevel = 0.0
                #     return

        # log exception in the main.log
        except Exception as e:
            log.main.error('Thread died. {0} {1} {2}'.format(e.__class__, e, log.format_tb(e.__traceback__)))

    # called to deliver new data point
    def NewData(self, TouchData):



# instantiate and start thread
thread = Touch()
thread.daemon = True
thread.start()
















# not sure if I will need this, but this ahk might help to automate switching of sound device
;sound_output_switcher
;mplammers v20170206
 
^+F5::
    Reload
return
 
^+F8::
    info_shouter("Sound Output Information")
return
 
^+F9::
    modify_sound_output(1)
return
 
^+F10::
    modify_sound_output(2)
return
 
^+F11::
    modify_sound_output(3)
return
 
^+F12::
    modify_sound_output(4)
return
 
info_shouter(title)
{
    contents := info_grabber()
    how_long = 1
    TrayTip %title%, %contents%, how_long, 0x11
    return
}
 
modify_sound_output(counter)                            
{
    Run, c:\windows\system32\control.exe mmsys.cpl
    WinWaitActive, Sound
    WinSet, AlwaysOnTop, On, Sound
    Send, {DOWN %counter%}
    Send, {AltDown}{s}{AltUp}
    WinClose, Sound
    info_shouter("Sound Output Modified")
}
 
info_grabber()
{
    Run, c:\windows\system32\control.exe mmsys.cpl
    WinWaitActive, Sound
    WinSet, AlwaysOnTop, On, Sound
    Send, {DOWN}
    sound_output := Object()
    ControlGet, number_of_sound_outputs, List, Count, SysListView321, Sound
    ControlGet briefnamesListing, List, Col1, SysListView321, Sound
    ControlGet detailednamesListing, List, Col2, SysListView321, Sound
    ControlGet statusListing, List, Col3, SysListView321, Sound
    LOOP, PARSE, briefnamesListing, `n
        sound_output.briefname[A_Index] := A_LoopField
    LOOP, PARSE, detailednamesListing, `n 
        sound_output.detailedname[A_Index] := A_LoopField
    LOOP, PARSE, statusListing, `n 
        sound_output.status[A_Index] := A_LoopField
    WinClose Sound  
    Loop % number_of_sound_outputs 
    {
        if sound_output.status[A_Index] = "Default Device"
        {
            active_sound_output := A_Index
        }
    }                                                               
 
    return sound_output.briefname[active_sound_output] . " (" . sound_output.detailedname[active_sound_output] . ")"
}



















    # def all(self):
    #     """
    #     Return a list of all sounds in the database. Called when building the web interface only, pretty much, so far.
    #     But now is probably orphan and unused since I decided to make the sounds tab sorted by collection
    #     """

    #     rows = db.conn.do_query("SELECT * FROM sounds")
    #     sounds = []
    #     for row in rows:
    #         sound = {}
    #         for field_name, field_id in self.db_field_names.items():
    #             sound[field_name] = row[field_id]
    #         sounds.append(sound)
    #     return sounds

    # def all_with_text(self):
    #     """
    #     Return a list of all sounds in the database with any text in the text column. Used for the sounds_by_text var
    #     """

    #     rows = db.conn.do_query("SELECT * FROM sounds WHERE text NOT NULL")
    #     sounds = []
    #     if rows is not None:
    #         for row in rows:
    #             sound = {}
    #             for field_name, field_id in self.db_field_names.items():
    #                 sound[field_name] = row[field_id]
    #             sound["synth_wait"] = False
    #             sounds.append(sound)
    #     return sounds

    # def new_sound(self, new_path, text = "", tempo_range = 0.0, base_volume_adjust = 1.0):
    #     """
    #     Add a new sound to the database. Returns the new sound id. The new file will already be there.
    #     """

    #     db.conn.do_query(f"INSERT INTO sounds (id,name,text,tempo_range,base_volume_adjust) VALUES (NULL, '{new_path}', '{text}', {tempo_range}, {base_volume_adjust})")
    #     db.conn.do_commit()
    #     rows = db.conn.do_query(f"SELECT id FROM sounds WHERE name = '{new_path}'")
    #     if rows is None:
    #         return None
    #     else:
    #         return rows[0][0]

    # def del_sound(self, sound_id):
    #     """
    #     Delete a sound from the database and files
    #     """

    #     dead_sound_walking = self.get_sound(sound_id=sound_id)
    #     os.remove(f"./sounds_master/{dead_sound_walking['name']}")
    #     os.system(f"rm -rf ./sounds_processed/{sound_id}/")
    #     db.conn.do_query(f"DELETE FROM sounds WHERE id = {sound_id}")
    #     db.conn.do_commit()
    #     collection_list = self.collections_for_sound(sound_id=sound_id)
    #     for collection_name, collection_state in collection_list:
    #         if collection_state is True:
    #             self.collection_update(
    #                 sound_id=sound_id, collection_name=collection_name, state=False
    #             )

    # def reprocess(self, sound_id):
    #     """
    #     Reprocess one sound.
    #     This is mostly borrowed from the preprocess.py on the desktop that preprocesses all sounds
    #     This right here is the up to date version. I have no idea what the status of the desktop is
    #     """

    #     # First go get the sound from the db
    #     the_sound = self.get_sound(sound_id=sound_id)

    #     # Get all the db row stuff into nice neat variables
    #     sound_id = str(the_sound["id"])
    #     file_path = str(the_sound["name"])
    #     sound_base_volume_adjust = the_sound["base_volume_adjust"]
    #     sound_tempo_range = the_sound["tempo_range"]

    #     # Delete the old processed sound
    #     try:
    #         os.system(f"rm -rf ./sounds_processed/{sound_id}/*.wav")
    #     except Exception: # pylint: disable=broad-exception-caught
    #         pass

    #     # Create the destination directory
    #     os.makedirs(f"./sounds_processed/{sound_id}", exist_ok=True)

    #     # If we're adjusting the sound volume, ffmpeg, otherwise just copy the original file to 0.wav, which is the file with original tempo
    #     if sound_base_volume_adjust != 1.0:
    #         exit_status = os.system(
    #             f'ffmpeg -v 0 -i ./sounds_master/{file_path} -filter:a "volume={sound_base_volume_adjust}" ./sounds_processed/{sound_id}/tmp_0.wav'
    #         )
    #         log.main.info("Jacked up volume for %s (%s)", file_path, exit_status)
    #     else:
    #         exit_status = os.system(
    #             f"cp ./sounds_master/{file_path} ./sounds_processed/{sound_id}/tmp_0.wav"
    #         )
    #         log.main.info("Copied %s (%s)", file_path, exit_status)

    #     # If we're adjusting the tempo, use rubberband to adjust 0.wav to various tempos. Otherwise, we just have 0.wav and we're done
    #     # removed --smoothing because it seemed to be the cause of the noise at the end of adjusted sounds
    #     if sound_tempo_range != 0.0:
    #         for multiplier in [-1, -0.75, -0.5, -0.25, 0.25, 0.5, 0.75, 1]:
    #             exit_status = os.system(
    #                 f"rubberband --quiet --realtime --pitch-hq --tempo {1 - (sound_tempo_range * multiplier):.2f} ./sounds_processed/{sound_id}/tmp_0.wav ./sounds_processed/{sound_id}/tmp_{multiplier}.wav"
    #             )
    #             log.main.info(
    #                 "Rubberbanded %s to %s (%s)", sound_id, multiplier, exit_status
    #             )

    #             exit_status = os.system(
    #                 f"ffmpeg -v 0 -i ./sounds_processed/{sound_id}/tmp_{multiplier}.wav -ar 44100 ./sounds_processed/{sound_id}/{multiplier}.wav"
    #             )
    #             log.main.info(
    #                 "Downsampled %s tempo %s (%s)", sound_id, multiplier, exit_status
    #             )

    #     exit_status = os.system(
    #         f"ffmpeg -v 0 -i ./sounds_processed/{sound_id}/tmp_0.wav -ar 44100 ./sounds_processed/{sound_id}/0.wav"
    #     )
    #     log.main.info("Downsampled %s tempo 0 (%s)", sound_id, exit_status)

    #     try:
    #         exit_status = os.system(f"rm -f ./sounds_processed/{sound_id}/tmp_*")
    #     except Exception: # pylint: disable=broad-exception-caught
    #         pass
    #     log.main.info("Removed tmp files for %s (%s)", sound_id, exit_status)

    # def amplify_master_sounds(self):
    #     """
    #     Go through all sounds. If there's a BaseVol not 1.0, amplify the master sound and set BaseVol to 1.0 to make it permanent
    #     I wanted to fix a lot of background noise that got into the sounds, and I think that happened when I set BaseVol,
    #     so this is for that little fixit job.
    #     """
    #     for sound in self.all():
    #         sound_id = sound["id"]
    #         file_path = sound["name"]
    #         sound_base_volume_adjust = sound["base_volume_adjust"]

    #         if sound_base_volume_adjust != 1.0:
    #             os.rename(
    #                 f"./sounds_master/{file_path}",
    #                 f"./sounds_master/{file_path}_backup",
    #             )
    #             exit_status = os.system(
    #                 f'ffmpeg -v 0 -i ./sounds_master/{file_path}_backup -filter:a "volume={sound_base_volume_adjust}" ./sounds_master/{file_path}'
    #             )
    #             log.main.info("Updated volume for %s (%s)", file_path, exit_status)
    #             self.update(sound_id, base_volume_adjust="1.0")

    # def reprocess_modified(self):
    #     """
    #     Go through all sounds. Run reprocess if the date modified of the master file is later than the processed file.
    #     This is for when the master sounds are modified to remove clicks and junk.
    #     """
    #     for sound in self.all():
    #         sound_id = sound["id"]
    #         file_path = sound["name"]

    #         if (
    #             os.stat(f"./sounds_master/{file_path}").st_mtime
    #             > os.stat(f"./sounds_processed/{sound_id}/0.wav").st_mtime
    #         ):
    #             self.reprocess(sound_id)

    # def reprocess_all(self):
    #     """
    #     Go through all sounds. Run reprocess.
    #     Usually this is run by itself from command line
    #     """
    #     for sound in self.all():
    #         sound_id = sound["id"]

    #         self.reprocess(sound_id)

    # def play_all(self):
    #     """
    #     Go through all sounds, play them one at a time.
    #     For debugging and QA
    #     """

    #     # time I need to walk over to the bed and lay down to listen to my wife
    #     time.sleep(10)

    #     for sound in self.all():
    #         file_path = sound["name"]

    #         if "breathe_normal" not in file_path:
    #             log.main.info("Playing %s", file_path)
    #             os.system(f"aplay ./sounds_master/{file_path}")
    #             time.sleep(2)

    # def play_all_volume_adjust(self):
    #     """
    #     Go through all sounds, play them one at a time in a loop.
    #     Allow volume control. Filthy as fuck. Horrendously hacky and stupid.
    #     I am an imbecile.
    #     For debugging and QA only

    #     Reading this months later. OMG this is stupid.
    #     OMG this is awful!

    #     Reading it again a year later. Omg this is shit! SHAME!

    #     Whoa dude, you couldn't find a better way!?
    #     """

    #     skip = 54

    #     for sound in self.all():
    #         file_path = sound["name"]

    #         if "breathe_normal" in file_path:
    #             if skip > 0:
    #                 skip -= 1
    #                 continue
    #             vol_adjust = 1.0
    #             needs_new_adjust = False
    #             high_pass_filter = 0
    #             low_pass_filter = 5000
    #             while not os.path.exists("./sounds_master/skipnext"):
    #                 os.system(f"aplay ./sounds_master/{file_path}")
    #                 time.sleep(1)

    #                 if os.path.exists("./sounds_master/volup"):
    #                     vol_adjust += 0.2
    #                     needs_new_adjust = True
    #                     os.unlink("./sounds_master/volup")
    #                 elif os.path.exists("./sounds_master/voldn"):
    #                     vol_adjust -= 0.2
    #                     needs_new_adjust = True
    #                     os.unlink("./sounds_master/voldn")
    #                 elif os.path.exists("./sounds_master/bassfix"):
    #                     high_pass_filter += 200
    #                     needs_new_adjust = True
    #                     os.unlink("./sounds_master/bassfix")
    #                 elif os.path.exists("./sounds_master/trebfix"):
    #                     low_pass_filter -= 500
    #                     needs_new_adjust = True
    #                     os.unlink("./sounds_master/trebfix")
    #                 elif os.path.exists("./sounds_master/clickfix"):
    #                     log.main.debug("Review and fix clicks later: %s", file_path)
    #                     os.unlink("./sounds_master/clickfix")

    #                 if needs_new_adjust:
    #                     if not os.path.exists(f"./sounds_master/backup_{file_path}"):
    #                         os.rename(
    #                             f"./sounds_master/{file_path}",
    #                             f"./sounds_master/backup_{file_path}",
    #                         )
    #                     else:
    #                         os.unlink(f"./sounds_master/{file_path}")

    #                     filters = f'"volume={vol_adjust}, highpass=f={high_pass_filter}, lowpass=f={low_pass_filter}"'
    #                     filters = filters.replace("volume=1.0", "")
    #                     filters = filters.replace("highpass=f=0, ", "")
    #                     filters = filters.replace("lowpass=f=5000", "")
    #                     filters = filters.replace(', "', '"')
    #                     filters = filters.replace('", ', '"')

    #                     ffmpeg_cmd = f"ffmpeg -i ./sounds_master/backup_{file_path} -filter:a {filters} ./sounds_master/{file_path}"
    #                     print(ffmpeg_cmd)
    #                     os.system(ffmpeg_cmd)
    #                     needs_new_adjust = False

    #             os.unlink("./sounds_master/skipnext")

    # def collection_names_as_list(self):
    #     """
    #     Returns all the names from the collections table as a list
    #     """

    #     rows = db.conn.do_query("SELECT name FROM collections")

    #     collection_names = []
    #     for row in rows:
    #         collection_names.append(row[0])
    #     return collection_names

    # def collections_for_sound(self, sound_id):
    #     """
    #     Returns all the collection names indicating which ones a specific sound is in. Used to build web page with checkboxes.
    #     """

    #     sound_id = int(sound_id)

    #     rows = db.conn.do_query("SELECT name,sound_ids FROM collections")

    #     collection_states = []
    #     for row in rows:
    #         row_in_collection = False

    #         if row[1] is not None and row[1] != "None" and row[1] != "":
    #             for element in row[1].split(","):
    #                 if "-" in element:
    #                     id_bounds = element.split("-")
    #                     id_min = int(id_bounds[0])
    #                     id_max = int(id_bounds[1])
    #                     if sound_id <= id_max and sound_id >= id_min:
    #                         row_in_collection = True
    #                         break
    #                 else:
    #                     if element.isnumeric() and sound_id == int(element):
    #                         row_in_collection = True
    #                         break
    #         collection_states.append((row[0], row_in_collection))
    #     return collection_states

    # def all_sounds_by_collection(self):
    #     """
    #     Returns a list of collections with all the sounds. Used to build web page with all sounds.
    #     """

    #     rows = db.conn.do_query("SELECT name,sound_ids FROM collections")

    #     collection_list = []
    #     for row in rows:
    #         collection = {}
    #         collection["name"] = row[0]

    #         # Unpack the "9-99,999" format into a list of individual sound ids, unless the collection was null
    #         sound_ids = []
    #         if row[1] is not None and row[1] != "None" and row[1] != "":
    #             for element in row[1].split(","):
    #                 if "-" in element:
    #                     id_bounds = element.split("-")
    #                     id_min = int(id_bounds[0])
    #                     id_max = int(id_bounds[1])
    #                     for collection_id in range(id_min, id_max + 1):
    #                         sound_ids.append(collection_id)
    #                 elif element.isnumeric():
    #                     sound_ids.append(int(element))

    #         sounds = []
    #         for sound_id in sound_ids:
    #             sounds.append(self.get_sound(sound_id=sound_id))

    #         collection["sounds"] = sounds

    #         collection_list.append(collection)
    #     return collection_list

    # def collection_update(self, sound_id, collection_name, state):
    #     """
    #     Updates one collection for one sound
    #     """

    #     sound_id = int(sound_id)

    #     # Get the sound ids for the collection name. Might be None if there were no sounds assigned to it
    #     collection = self.get_collection(collection_name)

    #     # Unpack the "9-99,999" format into a list of individual sound ids, unless the collection was null
    #     collection_ids = []
    #     if collection is not None and collection != "None" and collection != "":
    #         for element in collection.split(","):
    #             if "-" in element:
    #                 id_bounds = element.split("-")
    #                 id_min = int(id_bounds[0])
    #                 id_max = int(id_bounds[1])
    #                 for collection_id in range(id_min, id_max + 1):
    #                     collection_ids.append(collection_id)
    #             elif element.isnumeric():
    #                 collection_ids.append(int(element))

    #     # Now that we have it in a flat list form, do whatever, add or delete, then sort the list so that it's in integer order again
    #     if state is True:
    #         collection_ids.append(sound_id)
    #     else:
    #         try:
    #             collection_ids.remove(sound_id)
    #         except ValueError:
    #             pass
    #     collection_ids.sort()

    #     # Unless we just emptied the list, pack it back up into a "9-99,999" format and hack off the ending ,
    #     if len(collection_ids) > 0:
    #         collection = ""
    #         collection_id_prev = None
    #         collection_id_range_min = None
    #         collection_id_range_max = None
    #         for collection_id in collection_ids:
    #             if collection_id_prev is None:
    #                 collection_id_prev = collection_id
    #                 continue
    #             if collection_id == collection_id_prev:
    #                 continue
    #             if collection_id - collection_id_prev == 1:
    #                 if collection_id_range_min is None:
    #                     collection_id_range_min = collection_id_prev
    #                 collection_id_range_max = collection_id
    #                 collection_id_prev = collection_id
    #                 continue
    #             if collection_id - collection_id_prev > 1:
    #                 if collection_id_range_min is not None:
    #                     collection += (
    #                         f"{collection_id_range_min}-{collection_id_range_max},"
    #                     )
    #                     collection_id_range_min = None
    #                     collection_id_range_max = None
    #                 else:
    #                     collection += f"{collection_id_prev},"
    #                 collection_id_prev = collection_id
    #                 continue
    #         if collection_id_range_max is not None:
    #             collection += f"{collection_id_range_min}-{collection_id_range_max},"
    #         else:
    #             collection += f"{collection_id_prev},"
    #         collection = collection[:-1]
    #     else:
    #         collection = None

    #     # Write the change to db
    #     self.set_collection(collection_name=collection_name, sound_ids=collection)

    # def get_collection(self, collection_name):
    #     """
    #     Returns one collection by name
    #     """

    #     rows = db.conn.do_query(
    #         f"SELECT sound_ids FROM collections WHERE name = '{collection_name}'"
    #     )
    #     if rows is None:
    #         return None
    #     else:
    #         return rows[0][0]

    # def set_collection(self, collection_name, sound_ids):
    #     """
    #     Sets one collection
    #     """

    #     # I want that field to either be NULL or a string with stuff there
    #     if sound_ids is None or sound_ids == "None":
    #         sound_ids = "NULL"
    #     else:
    #         sound_ids = f"'{sound_ids}'"

    #     db.conn.do_query(
    #         f"UPDATE collections SET sound_ids = {sound_ids} WHERE name = '{collection_name}'"
    #     )
    #     db.conn.do_commit()

    # def new_collection(self, collection_name):
    #     """
    #     Adds a new collection. Tests for existence first.
    #     """

    #     rows = db.conn.do_query(
    #         f"SELECT sound_ids FROM collections WHERE name = '{collection_name}'"
    #     )
    #     if rows is None:
    #         db.conn.do_query(
    #             f"INSERT INTO collections VALUES (NULL, '{collection_name}', NULL)"
    #         )
    #         db.conn.do_commit()

    # def del_collection(self, collection_name):
    #     """
    #     Delete a collection by name
    #     """

    #     db.conn.do_query(f"DELETE FROM collections WHERE name = '{collection_name}'")
    #     db.conn.do_commit()


# class SoundCollection:
#     """
#     A collection is a grouping of sound ids for a specific purpose
#     Looking back, I realize I should have put the collection ids in the sounds table and dynamically built the collections that way, but it's done, fuck her
#     Aaaaaaaaand now I'm doing it the way it should have been done
#     """

#     def __init__(self, collection_name):

#         self.name = collection_name

#         # Thought for a while how to handle the replay_wait that will be per sound
#         # There will be a master list, and a list updated every 100s that sounds will actually be selected from
#         # And we need a LastUpdate var to keep track of when we last updated the available list
#         self.sounds_in_collection = []
#         self.sounds_available_to_play = []
#         self.next_update_seconds = 0

#         # Generator that yields all the sound ids in the collection, from the db
#         self.sound_ids = self.sound_id_generator()

#         # For each sound in this collection, get the sound and store all it's details
#         for sound_id in self.sound_ids:
#             if sound_id is not None:
#                 sound = db.get_sound(sound_id=sound_id)
#                 if sound is not Nne and os.path.exists(f'./sounds_processed/{sound_id}/0.wav') is True:      sound["skip_until"] = time.time() + (              sound["replay_wait"] * random.uniform(0.0, 1.2)
#                     )
#                     sound['synth_wait'] = False
#                     self.sounds_in_collection.append(sound)
#                 else:
#                     log.main.warning(
#                         "Removed derelict sound id %s from %s collection",
#                         sound_id,
#                         collection_name,
#                     )
#                     db.collection_update(
#                         sound_id=sound_id, collection_name=collection_name, state=False
#                     )
#         # It used to be that when Christine was restarted it would reset all the skip_untils, so she would suddenly just talk and talk. all the seldom used phrases would just come out one after another. She was being a bit weird even for a plastic woman.So I thought about saving state, but really if I were to just initialize it first thing it would still be about the same, fine.
#         # So now I have started initializing the skip untils to a random amount of time between now and 1.2 x the replay_wait.
#         self.update_available_sounds()

#     def sound_id_generator(self):
#         """Generator that yields sound ids"""

#         row = db.get_collection(self.name)

#         # In case the db row has null in that field, like no sounds in the collection
#         if row is None or row == "None":
#             yield None
#         else:
#             for element in row.split(","):
#                 if "-" in element:
#                     id_bounds = element.split("-")
#                     id_min = int(id_bounds[0])
#                     id_max = int(id_bounds[1])
#                     for sound_id in range(id_min, id_max + 1):
#                         yield sound_id
#                 elif element.isnumeric():
#                     yield int(element)

#     def update_available_sounds(self):
#         """Updates the list that keeps track of sounds that are available to play"""

#         # Store the time so that we don't have to call time so much
#         current_seconds = time.time()

#         # Throw this 5s in the future
#         self.next_update_seconds = current_seconds + 5

#         # Empty the list of available sounds
#         self.sounds_available_to_play = []

#         # Go through all the sounds and add available ones to the list
#         for sound in self.sonds_in_collection:
#             if sound["skip_until"] < current_seconds:  self.sounds_available_to_play.append(sound)et_random_sound(self, intensity=None):
#         """Returns some weird ass rando sound."""

#         # if it's time to update the available list, do it
#         if self.next_update_seconds < time.time():
#             self.update_available_sounds()

#         # There may be times that we run out of available sounds and have to throw a None
#         if len(self.sounds_available_to_play) == 0:
#             log.broca.warning("No sounds available to play in %s", self.name)
#             return None

#         # if the desired intensity is specified, we want to only select sounds near that intensity
#         if intensity is None:
#             rando_sound = random.choice(self.sounds_available_to_play)
#         else:
#             # it is now possible to get an intensity over 1.0, so we need to clip this
#             intensity = float(np.clip(intensity, 0.0, 1.0))

#             sounds_near_intensity = []
#             for sound in self.sounds_available_to_play:
#                 if math.isclose(sound["intensity"], intensity, abs_tol=0.25):
#                     sounds_near_intensity.append(sound)
#             if len(sounds_near_intensity) == 0:
#                 log.broca.warning(
#                     "No sounds near intensity %s in %s", intensity, self.name
#                 )
#                 return None
#             rando_sound = random.choice(sounds_near_intensity)
#             rando_sound['synth_wait'] = False

#         return rando_sound

#     def set_skip_until(self, sound_i):
#         """It used to be that skip_until got updated in GetRandomSound. That caused a lot of sounds to become unavailable due to a lot of soundsqueued but not played in times of heavy activity, often sexual in nature. So now this is only updated when played. Fuck me."

#         for sound in self.sounds_in_collection:
#             if sound["id"] == sound_id:
#                 log.broca.debg("Made unavailable: %s", sound)  sound["skip_until"] = time.time() + (          sound["replay_wait"] * random.uniform(0.8, 1.2)
#                 )
#                 # adding this try in response to a random exception
#                 try:
#                     self.sounds_available_to_play.remove(sound)
#                 except ValueError:
#                     log.broca.warning("ValueError happened when removing this sound: %s", sound)
#                 break


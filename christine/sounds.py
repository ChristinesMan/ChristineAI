"""
Handles collections of sounds
"""
import os
import os.path
# import sys
import time
import random
import math
import wave
import threading
import re
from multiprocessing.managers import BaseManager
import queue
import socket
import numpy as np

from christine import log
from christine.status import STATE
from christine import database
from christine import broca


# magic as far as I'm concerned
# A fine black box
class TTSServerManager(BaseManager):
    """Black box stuff"""

    pass  # pylint: disable=unnecessary-pass

class MyTTSServer(threading.Thread):
    """A server on the local network will be running a service that will accept text and return speech."""

    name = "MyTTSServer"

    def __init__(self):

        threading.Thread.__init__(self)

        # init these to make linter happy
        self.server_ip = None
        self.manager = None
        self.text_queue = queue.Queue(maxsize=30)
        self.audio_queue = queue.Queue(maxsize=30)
        self.server_shutdown = False
        STATE.broca_connected = False

    def run(self):

        # create the directory if necessary where we will cache synthesized sounds
        os.makedirs("sounds/synth/", exist_ok=True)

        while True:

            if STATE.broca_connected is True:

                # get something out of the queue if there's anything. Don't block.
                try:
                    result_sound = self.audio_queue.get_nowait()

                    wav_file = wave.open(result_sound['file_path'], "wb")
                    wav_file.setnchannels(1)
                    wav_file.setsampwidth(2)
                    wav_file.setframerate(44100)
                    wav_file.writeframes(result_sound['audio_data'])
                    wav_file.close()
                    broca.thread.notify_synth_done()

                except (BrokenPipeError, EOFError) as ex:
                    log.broca.warning("Server went away. %s", ex)
                    self.say_fail()
                    self.destroy_manager()

                except Exception: # pylint: disable=broad-exception-caught
                    pass

            time.sleep(0.2)

    def connect_manager(self):
        """Connect the manager thing"""

        try:

            log.broca.info("Connecting to %s", self.server_ip)
            self.manager = TTSServerManager(
                address=(self.server_ip, 3001), authkey=b'fuckme',
            )
            self.manager.register("get_text_queue")
            self.manager.register("get_audio_queue")
            self.manager.register("get_server_shutdown")
            self.manager.connect()

            self.text_queue = (
                self.manager.get_text_queue() # pylint: disable=no-member
            )
            self.audio_queue = (
                self.manager.get_audio_queue() # pylint: disable=no-member
            )
            self.server_shutdown = (
                self.manager.get_server_shutdown() # pylint: disable=no-member
            )
            log.broca.info("Connected")
            self.say_connected()
            STATE.broca_connected = True

        except Exception as ex: # pylint: disable=broad-exception-caught

            log.broca.error("Connect failed. %s", ex)
            self.say_fail()
            self.destroy_manager()

    def destroy_manager(self):
        """Disconnect and utterly destroy the manager"""

        STATE.broca_connected = False

        try:
            del self.text_queue
        except AttributeError:
            pass

        try:
            del self.audio_queue
        except AttributeError:
            pass

        try:
            del self.manager
        except AttributeError:
            pass

        self.server_ip = None
        self.manager = None

    def server_update(self, server_ip: str):
        """This is called when another machine other than myself says hi"""

        # if somehow we're still connected, get outta there
        if STATE.broca_connected is True:
            self.destroy_manager()

        # save the server ip
        self.server_ip = server_ip

        # connect to it
        self.connect_manager()

    def synthesize(self, sound):
        """Accepts a bit of text to get some speech synthesis done"""

        try:
            self.text_queue.put(sound, block=False)
            log.broca.debug("Put this on the synthesis queue: %s. Queue sizes: %s / %s", sound, self.text_queue.qsize(), self.audio_queue.qsize())
        except queue.Full:
            log.broca.error("The remote queue is full, wtf")
            self.say_fail()
            self.server_shutdown = True
            time.sleep(1)
            self.destroy_manager()
        except (BrokenPipeError, EOFError) as ex:
            log.broca.error("Server error. %s", ex)
            self.say_fail()
            self.destroy_manager()
        except AttributeError:
            pass

    def say_fail(self):
        """Play the sound to notify that broca failed."""
        broca.thread.queue_sound(from_collection='broca_failure')

    def say_connected(self):
        """Play the sound to notify that broca connected."""
        broca.thread.queue_sound(from_collection='broca_connected')

class SoundsDB(threading.Thread):
    """This class basically manages everything to do with sounds. Actual speech is all synthesized now."""

    name = "SoundsDB"

    def __init__(self):

        threading.Thread.__init__(self)

        # how old in seconds should a cached wav file be before it gets deleted
        self.cache_ttl = 60 * 60 * 24 * 5 #days

        # This grabs the field names so that it's easier to assign the value of fields to keys or something like that
        self.db_field_names = database.conn.field_names_for_table("sounds")

        # dict of lists to sort sounds into collections
        self.build_sound_collections()

        # When this class starts, it won't be connected to a server yet
        self.tts_server = MyTTSServer()
        self.tts_server.daemon = True
        self.tts_server.start()

    def run(self):

        # wait a bit before cleaning cache first time after start
        time.sleep(300)

        while True:

            # every 12 hours clean cache
            self.clean_cache()
            time.sleep(43200)

    def get_sound(self, sound_id):
        """
        Returns a sound from the database as a dict.
        """

        rows = database.conn.do_query(f"SELECT * FROM sounds WHERE id = {sound_id}")
        if rows is None:
            return None

        sound = {}
        for field_name, field_id in self.db_field_names.items():
            sound[field_name] = rows[0][field_id]
        return sound

    def get_sound_synthesis(self, text):
        """
        Returns a sound as a dict. If the text of the sound already exists, return the cached sound.
        Otherwise, if a voice synthesis server is available, send to the server, return the sound, 
        and update the sound when the synthesized audio is available. 
        """

        # if there's no server available, just stop it right there
        if STATE.broca_connected is False:
            return None

        # standardize the text to just the words, no spaces
        text_stripped = re.sub("[^a-zA-Z0-9 ]", "", text).lower().strip().replace(' ', '_')[0:200]
        file_path = f"sounds/synth/{text_stripped}.wav"

        # if there's already a cached synthesized sound, use the same cached stuff and return it
        if os.path.isfile(file_path):
            sound = {'id': 0, 'file_path': file_path, 'text': text, 'proximity_volume_adjust': 1.0, 'intensity': 0.0, 'replay_wait': 0, 'skip_until': 0, 'synth_wait': False}
            return sound

        # No cache, so send it over there to be generated, but don't wait. The broca module will do the waiting.
        else:

            sound = {'id': 0, 'file_path': file_path, 'text': text, 'proximity_volume_adjust': 1.0, 'intensity': 0.0, 'replay_wait': 0, 'skip_until': 0, 'synth_wait': True}
            self.tts_server.synthesize(sound)
            return sound

    def build_sound_collections(self):
        """We have a dict of lists to sort sounds into collections."""

        # get all the sounds from database
        rows = database.conn.do_query("SELECT * FROM sounds")

        # reset
        self.collections = {}
        self.sounds = {}

        # go over each sound in database, making a dict, and assigning to collections
        for row in rows:

            # build the sound dict from the database info and add some defaults
            sound = {}
            for field_name, field_id in self.db_field_names.items():
                sound[field_name] = row[field_id]
            if os.path.isfile(sound['file_path']) is False:
                log.main.warning('This sound does not exist in the file system: %s', sound)
                continue
            if sound["replay_wait"] != 0:
                sound["skip_until"] = time.time() + (sound["replay_wait"] * random.uniform(0.0, 1.2))
            else:
                sound["skip_until"] = 0
            sound['synth_wait'] = False
            # log.main.debug("Sound: %s", sound)

            # collections is a comma delimited string. For each collection name, populate the collections dict and sounds dict
            sound_id = sound['id']
            collections = sound['collections'].split(',')
            for collection_name in collections:
                if collection_name not in self.collections:
                    # log.main.debug("Created collection: %s", collection_name)
                    self.collections[collection_name] = []
                self.collections[collection_name].append(sound)
                self.sounds[sound_id] = sound

    def update(
        self,
        sound_id,
        proximity_volume_adjust=None,
        intensity=None,
        replay_wait=None,
        collections=None,
    ):
        """
        Update one sound
        """

        if proximity_volume_adjust is not None:
            database.conn.do_query(
                f"UPDATE sounds SET proximity_volume_adjust = {proximity_volume_adjust} WHERE id = {sound_id}"
            )
        if intensity is not None:
            database.conn.do_query(
                f"UPDATE sounds SET intensity = {intensity} WHERE id = {sound_id}"
            )
        if replay_wait is not None:
            database.conn.do_query(
                f"UPDATE sounds SET replay_wait = {replay_wait} WHERE id = {sound_id}"
            )
        if collections is not None:
            database.conn.do_query(
                f"UPDATE sounds SET collections = '{collections}' WHERE id = {sound_id}"
            )
        database.conn.do_commit()

    def get_random_sound(self, collection_name, intensity=None):
        """Returns some weird ass rando sound."""

        # test for derpage
        if collection_name not in self.collections:
            log.main.warning("The collection %s does not exist!", collection_name)
            return None

        # Store the time so that we don't have to call time so much
        current_seconds = time.time()

        # it is now possible to get an intensity over 1.0, so we need to clip this
        if intensity is not None:
            intensity = float(np.clip(intensity, 0.0, 1.0))

        # iterate over all the sounds in the collection and pick one at random
        random.shuffle(self.collections[collection_name])
        for sound in self.collections[collection_name]:

            # test the sound intensity
            if intensity is not None and not math.isclose(sound["intensity"], intensity, abs_tol=0.25):
                continue

            # skip this sound if it's been played too recently
            if sound["skip_until"] > current_seconds:
                continue

            # and if it got past that we just return it
            return sound

        # and if it got through all those sounds without finding any, throw a None
        return None

    def set_skip_until(self, sound_id):
        """Must only update a sound's skip_until when it's time to play it. So the broca module will call this."""

        sound = self.sounds[sound_id]
        log.broca.debug("Made unavailable: %s", sound)
        sound["skip_until"] = time.time() + (sound["replay_wait"] * random.uniform(0.0, 1.2))

    def clean_cache(self):
        """As voice is synthesized, wav files are cached for future use. But after a while that cache sounds stale. So clean it."""

        seconds_below_to_delete = time.time() - self.cache_ttl
        cache_dir = 'sounds/synth'
        files_deleted = 0
        for file_name in os.listdir(cache_dir):
            if '.wav' in file_name:
                file_path = os.path.join(cache_dir, file_name)
                if os.path.getmtime(file_path) < seconds_below_to_delete:
                    os.remove(file_path)
                    files_deleted += 1

        log.main.info('Cleaned voice synth cache, deleted %s files.', files_deleted)


# Initialize and start
db = SoundsDB()
db.daemon = True
db.start()

class ReceiveLoveFromUDP(threading.Thread):
    """Thread will listen to the UDP broadcast packets sent from server.
    """

    name = "ReceiveLoveFromUDP"

    def __init__(self):

        threading.Thread.__init__(self)

    def run(self):

        # bind to the UDP port
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.bind(("0.0.0.0", 3001))

        # repeatedly listen for UDP packets, only when server not connected
        while True:

            time.sleep(15)

            if STATE.broca_connected is False:

                log.broca.debug('Waiting for UDP packet')
                data, addr = sock.recvfrom(1024)

                if data == b'fuckme':
                    server_ip = addr[0]
                    log.broca.debug('Received UDP packet from %s', server_ip)
                    db.tts_server.server_update(server_ip=server_ip)

udp_listener = ReceiveLoveFromUDP()
udp_listener.daemon = True
udp_listener.start()

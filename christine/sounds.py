"""
Handles collections of discrete sounds
"""
import os
import os.path
import time
import random
import math
import numpy as np

from christine import log
from christine.database import database

class Sound:
    """Represents an individual sound"""

    def __init__(self, sound_id, file_path, collections, replay_wait, intensity, skip_until, pause_wernicke):
        self.sound_id = sound_id
        self.file_path = file_path
        self.collections = collections
        self.replay_wait = replay_wait
        self.intensity = intensity
        self.skip_until = skip_until
        self.pause_wernicke = pause_wernicke

class SoundsDB():
    """This class basically manages everything to do with sounds. Actual speech is all synthesized now."""

    def __init__(self):

        self.build_sound_collections()


    def build_sound_collections(self):
        """This is done at the beginning to build the sound collections using modern SQLAlchemy methods."""

        self.collections = {}
        self.sounds = {}

        # Use the new type-safe method to get all sounds
        sound_records = database.get_all_sounds()
        
        # Handle empty database
        if not sound_records:
            log.main.warning("No sounds found in database")
            return

        for record in sound_records:
            sound_id = record["id"]
            file_path = record["file_path"]
            collections = record["collections"].split(',')
            replay_wait = record["replay_wait"]
            intensity = record["intensity"]
            pause_wernicke = record["pause_processing"]

            if os.path.isfile(file_path) is False:
                log.main.warning('This sound does not exist in the file system: %s (ID: %s)', file_path, sound_id)
                continue

            if replay_wait != 0:
                skip_until = time.time() + (replay_wait * random.uniform(0.0, 1.2))
            else:
                skip_until = 0


            sound = Sound(sound_id, file_path, collections, replay_wait, intensity, skip_until, pause_wernicke)
            for collection_name in collections:
                if collection_name not in self.collections:
                    self.collections[collection_name] = []
                self.collections[collection_name].append(sound)
                self.sounds[sound_id] = sound


    def get_random_sound(self, collection_name, intensity=None) -> Sound | None:
        """Retrieve a random sound from a collection. Optionally, specify an intensity level."""

        # fail with a warning if the collection does not exist
        if collection_name not in self.collections:
            log.main.warning("The collection %s does not exist!", collection_name)
            return None

        current_seconds = time.time()

        # it is possible to get an intensity level greater than 1.0, so we need to clip it
        if intensity is not None:
            intensity = float(np.clip(intensity, 0.0, 1.0))

        random.shuffle(self.collections[collection_name])
        for sound in self.collections[collection_name]:

            if sound.skip_until > current_seconds:
                continue

            if intensity is not None and not math.isclose(sound.intensity, intensity, abs_tol=0.25):
                continue

            # if we get here, then we have a sound that is ready to be played
            sound.skip_until = time.time() + (sound.replay_wait * random.uniform(0.0, 1.2))
            return sound

        # if after going through all the sounds, then none of available, throw a None, bitch
        return None


# Initialize and start
sounds_db = SoundsDB()

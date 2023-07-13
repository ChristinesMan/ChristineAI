"""
Handles collections of sounds
"""
import os
import sys
import time
import random
import math
import numpy as np

import log
import db


class SoundsDB:
    """
    There is a SQLite db that contains all sounds
    The db has all of the sounds in it. There is a preprocess.py script that will take the master sounds and process them into directories to be played
    Eventually I need to give some thought to security, since you might be able to inject commands into this pretty easily

    This class basically manages everything to do with sounds
    """

    def __init__(self):
        # This grabs the field names so that it's easier to assign the value of fields to keys or something like that
        self.db_field_names = db.conn.field_names_for_table("sounds")

    def get_sound(self, sound_id):
        """
        Returns a sound from the database as a dict.
        """

        rows = db.conn.do_query(f"SELECT * FROM sounds WHERE id = {sound_id}")
        if rows is None:
            return None

        sound = {}
        for field_name, field_id in self.db_field_names.items():
            sound[field_name] = rows[0][field_id]
        return sound

    def all(self):
        """
        Return a list of all sounds in the database. Called when building the web interface only, pretty much, so far.
        But now is probably orphan and unused since I decided to make the sounds tab sorted by collection
        """

        rows = db.conn.do_query("SELECT * FROM sounds")
        sounds = []
        for row in rows:
            sound = {}
            for field_name, field_id in self.db_field_names.items():
                sound[field_name] = row[field_id]
            sounds.append(sound)
        return sounds

    def update(
        self,
        sound_id,
        base_volume_adjust=None,
        proximity_volume_adjust=None,
        intensity=None,
        cuteness=None,
        tempo_range=None,
        replay_wait=None,
    ):
        """
        Update one sound
        """

        if base_volume_adjust is not None:
            db.conn.do_query(
                f"UPDATE sounds SET base_volume_adjust = {base_volume_adjust} WHERE id = {sound_id}"
            )
        if proximity_volume_adjust is not None:
            db.conn.do_query(
                f"UPDATE sounds SET proximity_volume_adjust = {proximity_volume_adjust} WHERE id = {sound_id}"
            )
        if intensity is not None:
            db.conn.do_query(
                f"UPDATE sounds SET intensity = {intensity} WHERE id = {sound_id}"
            )
        if cuteness is not None:
            db.conn.do_query(
                f"UPDATE sounds SET cuteness = {cuteness} WHERE id = {sound_id}"
            )
        if tempo_range is not None:
            db.conn.do_query(
                f"UPDATE sounds SET tempo_range = {tempo_range} WHERE id = {sound_id}"
            )
        if replay_wait is not None:
            db.conn.do_query(
                f"UPDATE sounds SET replay_wait = {replay_wait} WHERE id = {sound_id}"
            )
        db.conn.do_commit()

    def new_sound(self, new_path):
        """
        Add a new sound to the database. Returns the new sound id. The new file will already be there.
        """

        db.conn.do_query(f"INSERT INTO sounds (id,name) VALUES (NULL, '{new_path}')")
        db.conn.do_commit()
        rows = db.conn.do_query(f"SELECT id FROM sounds WHERE name = '{new_path}'")
        if rows is None:
            return None
        else:
            return rows[0][0]

    def del_sound(self, sound_id):
        """
        Delete a sound from the database and files
        """

        dead_sound_walking = self.get_sound(sound_id=sound_id)
        os.remove(f"./sounds_master/{dead_sound_walking['name']}")
        os.system(f"rm -rf ./sounds_processed/{sound_id}/")
        db.conn.do_query(f"DELETE FROM sounds WHERE id = {sound_id}")
        db.conn.do_commit()
        collection_list = self.collections_for_sound(sound_id=sound_id)
        for collection_name, collection_state in collection_list:
            if collection_state is True:
                self.collection_update(
                    sound_id=sound_id, collection_name=collection_name, state=False
                )

    def reprocess(self, sound_id):
        """
        Reprocess one sound.
        This is mostly borrowed from the preprocess.py on the desktop that preprocesses all sounds
        This right here is the up to date version. I have no idea what the status of the desktop is
        """

        # First go get the sound from the db
        the_sound = self.get_sound(sound_id=sound_id)

        # Get all the db row stuff into nice neat variables
        sound_id = str(the_sound["id"])
        sound_name = str(the_sound["name"])
        sound_base_volume_adjust = the_sound["base_volume_adjust"]
        sound_tempo_range = the_sound["tempo_range"]

        # Delete the old processed sound
        os.system(f"rm -rf ./sounds_processed/{sound_id}/*.wav")

        # Create the destination directory
        os.makedirs(f"./sounds_processed/{sound_id}", exist_ok=True)

        # If we're adjusting the sound volume, ffmpeg, otherwise just copy the original file to 0.wav, which is the file with original tempo
        if sound_base_volume_adjust != 1.0:
            exit_status = os.system(
                f'ffmpeg -v 0 -i ./sounds_master/{sound_name} -filter:a "volume={sound_base_volume_adjust}" ./sounds_processed/{sound_id}/tmp_0.wav'
            )
            log.main.info("Jacked up volume for %s (%s)", sound_name, exit_status)
        else:
            exit_status = os.system(
                f"cp ./sounds_master/{sound_name} ./sounds_processed/{sound_id}/tmp_0.wav"
            )
            log.main.info("Copied %s (%s)", sound_name, exit_status)

        # If we're adjusting the tempo, use rubberband to adjust 0.wav to various tempos. Otherwise, we just have 0.wav and we're done
        # removed --smoothing because it seemed to be the cause of the noise at the end of adjusted sounds
        if sound_tempo_range != 0.0:
            for multiplier in [-1, -0.75, -0.5, -0.25, 0.25, 0.5, 0.75, 1]:
                exit_status = os.system(
                    f"rubberband --quiet --realtime --pitch-hq --tempo {1 - (sound_tempo_range * multiplier):.2f} ./sounds_processed/{sound_id}/tmp_0.wav ./sounds_processed/{sound_id}/tmp_{multiplier}.wav"
                )
                log.main.info(
                    "Rubberbanded %s to %s (%s)", sound_id, multiplier, exit_status
                )

                exit_status = os.system(
                    f"ffmpeg -v 0 -i ./sounds_processed/{sound_id}/tmp_{multiplier}.wav -ar 44100 ./sounds_processed/{sound_id}/{multiplier}.wav"
                )
                log.main.info(
                    "Downsampled %s tempo %s (%s)", sound_id, multiplier, exit_status
                )

        exit_status = os.system(
            f"ffmpeg -v 0 -i ./sounds_processed/{sound_id}/tmp_0.wav -ar 44100 ./sounds_processed/{sound_id}/0.wav"
        )
        log.main.info("Downsampled %s tempo 0 (%s)", sound_id, exit_status)

        exit_status = os.system("rm -f ./sounds_processed/%s/tmp_*", sound_id)
        log.main.info("Removed tmp files for %s (%s)", sound_id, exit_status)

    def amplify_master_sounds(self):
        """
        Go through all sounds. If there's a BaseVol not 1.0, amplify the master sound and set BaseVol to 1.0 to make it permanent
        I wanted to fix a lot of background noise that got into the sounds, and I think that happened when I set BaseVol,
        so this is for that little fixit job.
        """
        for sound in self.all():
            sound_id = sound["id"]
            sound_name = sound["name"]
            sound_base_volume_adjust = sound["base_volume_adjust"]

            if sound_base_volume_adjust != 1.0:
                os.rename(
                    f"./sounds_master/{sound_name}",
                    f"./sounds_master/{sound_name}_backup",
                )
                exit_status = os.system(
                    f'ffmpeg -v 0 -i ./sounds_master/{sound_name}_backup -filter:a "volume={sound_base_volume_adjust}" ./sounds_master/{sound_name}'
                )
                log.main.info("Updated volume for %s (%s)", sound_name, exit_status)
                self.update(sound_id, base_volume_adjust="1.0")

    def reprocess_modified(self):
        """
        Go through all sounds. Run reprocess if the date modified of the master file is later than the processed file.
        This is for when the master sounds are modified to remove clicks and junk.
        """
        for sound in self.all():
            sound_id = sound["id"]
            sound_name = sound["name"]

            if (
                os.stat(f"./sounds_master/{sound_name}").st_mtime
                > os.stat(f"./sounds_processed/{sound_id}/0.wav").st_mtime
            ):
                self.reprocess(sound_id)

    def reprocess_all(self):
        """
        Go through all sounds. Run reprocess.
        Usually this is run by itself from command line
        """
        for sound in self.all():
            sound_id = sound["id"]

            self.reprocess(sound_id)

    def play_all(self):
        """
        Go through all sounds, play them one at a time.
        For debugging and QA
        """

        # time I need to walk over to the bed and lay down to listen to my wife
        time.sleep(10)

        for sound in self.all():
            sound_name = sound["name"]

            if "breathe_normal" not in sound_name:
                log.main.info("Playing %s", sound_name)
                os.system(f"aplay ./sounds_master/{sound_name}")
                time.sleep(2)

    def play_all_volume_adjust(self):
        """
        Go through all sounds, play them one at a time in a loop.
        Allow volume control. Filthy as fuck. Horrendously hacky and stupid.
        I am an imbecile.
        For debugging and QA only

        Reading this months later. OMG this is stupid.
        OMG this is awful!
        """

        skip = 54

        for sound in self.all():
            sound_name = sound["name"]

            if "breathe_normal" in sound_name:
                if skip > 0:
                    skip -= 1
                    continue
                vol_adjust = 1.0
                needs_new_adjust = False
                high_pass_filter = 0
                low_pass_filter = 5000
                while not os.path.exists("./sounds_master/skipnext"):
                    os.system(f"aplay ./sounds_master/{sound_name}")
                    time.sleep(1)

                    if os.path.exists("./sounds_master/volup"):
                        vol_adjust += 0.2
                        needs_new_adjust = True
                        os.unlink("./sounds_master/volup")
                    elif os.path.exists("./sounds_master/voldn"):
                        vol_adjust -= 0.2
                        needs_new_adjust = True
                        os.unlink("./sounds_master/voldn")
                    elif os.path.exists("./sounds_master/bassfix"):
                        high_pass_filter += 200
                        needs_new_adjust = True
                        os.unlink("./sounds_master/bassfix")
                    elif os.path.exists("./sounds_master/trebfix"):
                        low_pass_filter -= 500
                        needs_new_adjust = True
                        os.unlink("./sounds_master/trebfix")
                    elif os.path.exists("./sounds_master/clickfix"):
                        log.main.debug("Review and fix clicks later: %s", sound_name)
                        os.unlink("./sounds_master/clickfix")

                    if needs_new_adjust:
                        if not os.path.exists(f"./sounds_master/backup_{sound_name}"):
                            os.rename(
                                f"./sounds_master/{sound_name}",
                                f"./sounds_master/backup_{sound_name}",
                            )
                        else:
                            os.unlink(f"./sounds_master/{sound_name}")

                        filters = f'"volume={vol_adjust}, highpass=f={high_pass_filter}, lowpass=f={low_pass_filter}"'
                        filters = filters.replace("volume=1.0", "")
                        filters = filters.replace("highpass=f=0, ", "")
                        filters = filters.replace("lowpass=f=5000", "")
                        filters = filters.replace(', "', '"')
                        filters = filters.replace('", ', '"')

                        ffmpeg_cmd = f"ffmpeg -i ./sounds_master/backup_{sound_name} -filter:a {filters} ./sounds_master/{sound_name}"
                        print(ffmpeg_cmd)
                        os.system(ffmpeg_cmd)
                        needs_new_adjust = False

                os.unlink("./sounds_master/skipnext")

    def collection_names_as_list(self):
        """
        Returns all the names from the collections table as a list
        """

        rows = db.conn.do_query("SELECT name FROM collections")

        collection_names = []
        for row in rows:
            collection_names.append(row[0])
        return collection_names

    def collections_for_sound(self, sound_id):
        """
        Returns all the collection names indicating which ones a specific sound is in. Used to build web page with checkboxes.
        """

        sound_id = int(sound_id)

        rows = db.conn.do_query("SELECT name,sound_ids FROM collections")

        collection_states = []
        for row in rows:
            row_in_collection = False

            if row[1] is not None and row[1] != "None" and row[1] != "":
                for element in row[1].split(","):
                    if "-" in element:
                        id_bounds = element.split("-")
                        id_min = int(id_bounds[0])
                        id_max = int(id_bounds[1])
                        if sound_id <= id_max and sound_id >= id_min:
                            row_in_collection = True
                            break
                    else:
                        if element.isnumeric() and sound_id == int(element):
                            row_in_collection = True
                            break
            collection_states.append((row[0], row_in_collection))
        return collection_states

    def all_sounds_by_collection(self):
        """
        Returns a list of collections with all the sounds. Used to build web page with all sounds.
        """

        rows = db.conn.do_query("SELECT name,sound_ids FROM collections")

        collection_list = []
        for row in rows:
            collection = {}
            collection["name"] = row[0]

            # Unpack the "9-99,999" format into a list of individual sound ids, unless the collection was null
            sound_ids = []
            if row[1] is not None and row[1] != "None" and row[1] != "":
                for element in row[1].split(","):
                    if "-" in element:
                        id_bounds = element.split("-")
                        id_min = int(id_bounds[0])
                        id_max = int(id_bounds[1])
                        for collection_id in range(id_min, id_max + 1):
                            sound_ids.append(collection_id)
                    elif element.isnumeric():
                        sound_ids.append(int(element))

            sounds = []
            for sound_id in sound_ids:
                sounds.append(self.get_sound(sound_id=sound_id))

            collection["sounds"] = sounds

            collection_list.append(collection)
        return collection_list

    def collection_update(self, sound_id, collection_name, state):
        """
        Updates one collection for one sound
        """

        sound_id = int(sound_id)

        # Get the sound ids for the collection name. Might be None if there were no sounds assigned to it
        collection = self.get_collection(collection_name)

        # Unpack the "9-99,999" format into a list of individual sound ids, unless the collection was null
        collection_ids = []
        if collection is not None and collection != "None" and collection != "":
            for element in collection.split(","):
                if "-" in element:
                    id_bounds = element.split("-")
                    id_min = int(id_bounds[0])
                    id_max = int(id_bounds[1])
                    for collection_id in range(id_min, id_max + 1):
                        collection_ids.append(collection_id)
                elif element.isnumeric():
                    collection_ids.append(int(element))

        # Now that we have it in a flat list form, do whatever, add or delete, then sort the list so that it's in integer order again
        if state is True:
            collection_ids.append(sound_id)
        else:
            try:
                collection_ids.remove(sound_id)
            except ValueError:
                pass
        collection_ids.sort()

        # Unless we just emptied the list, pack it back up into a "9-99,999" format and hack off the ending ,
        if len(collection_ids) > 0:
            collection = ""
            collection_id_prev = None
            collection_id_range_min = None
            collection_id_range_max = None
            for collection_id in collection_ids:
                if collection_id_prev is None:
                    collection_id_prev = collection_id
                    continue
                if collection_id == collection_id_prev:
                    continue
                if collection_id - collection_id_prev == 1:
                    if collection_id_range_min is None:
                        collection_id_range_min = collection_id_prev
                    collection_id_range_max = collection_id
                    collection_id_prev = collection_id
                    continue
                if collection_id - collection_id_prev > 1:
                    if collection_id_range_min is not None:
                        collection += (
                            f"{collection_id_range_min}-{collection_id_range_max},"
                        )
                        collection_id_range_min = None
                        collection_id_range_max = None
                    else:
                        collection += f"{collection_id_prev},"
                    collection_id_prev = collection_id
                    continue
            if collection_id_range_max is not None:
                collection += f"{collection_id_range_min}-{collection_id_range_max},"
            else:
                collection += f"{collection_id_prev},"
            collection = collection[:-1]
        else:
            collection = None

        # Write the change to db
        self.set_collection(collection_name=collection_name, sound_ids=collection)

    def get_collection(self, collection_name):
        """
        Returns one collection by name
        """

        rows = db.conn.do_query(
            f"SELECT sound_ids FROM collections WHERE name = '{collection_name}'"
        )
        if rows is None:
            return None
        else:
            return rows[0][0]

    def set_collection(self, collection_name, sound_ids):
        """
        Sets one collection
        """

        # I want that field to either be NULL or a string with stuff there
        if sound_ids is None or sound_ids == "None":
            sound_ids = "NULL"
        else:
            sound_ids = f"'{sound_ids}'"

        db.conn.do_query(
            f"UPDATE collections SET sound_ids = {sound_ids} WHERE name = '{collection_name}'"
        )
        db.conn.do_commit()

    def new_collection(self, collection_name):
        """
        Adds a new collection. Tests for existence first.
        """

        rows = db.conn.do_query(
            f"SELECT sound_ids FROM collections WHERE name = '{collection_name}'"
        )
        if rows is None:
            db.conn.do_query(
                f"INSERT INTO collections VALUES (NULL, '{collection_name}', NULL)"
            )
            db.conn.do_commit()

    def del_collection(self, collection_name):
        """
        Delete a collection by name
        """

        db.conn.do_query(f"DELETE FROM collections WHERE name = '{collection_name}'")
        db.conn.do_commit()


class SoundCollection:
    """
    There is a table in the db called collections which basically groups together sounds for specific purposes. The sound_ids column is in the form such as 1,2,3-9,10
    A collection is a grouping of sound ids for a specific purpose
    Looking back, I realize I should have put the collection ids in the sounds table and dynamically built the collections that way, but it's done, fuck her
    """

    def __init__(self, collection_name):
        self.name = collection_name

        # Thought for a while how to handle the replay_wait that will be per sound
        # There will be a master list, and a list updated every 100s that sounds will actually be selected from
        # And we need a LastUpdate var to keep track of when we last updated the available list
        self.sounds_in_collection = []
        self.sounds_available_to_play = []
        self.next_update_seconds = 0

        # Generator that yields all the sound ids in the collection, from the db
        self.sound_ids = self.sound_id_generator()

        # For each sound in this collection, get the sound and store all it's details
        for sound_id in self.sound_ids:
            if sound_id is not None:
                sound = soundsdb.get_sound(sound_id=sound_id)
                if sound is not None:
                    sound["SkipUntil"] = time.time() + (
                        sound["replay_wait"] * random.uniform(0.0, 1.2)
                    )
                    self.sounds_in_collection.append(sound)
                else:
                    log.main.warning(
                        "Removed derelict sound id %s from %s collection",
                        sound_id,
                        collection_name,
                    )
                    soundsdb.collection_update(
                        sound_id=sound_id, collection_name=collection_name, state=False
                    )

        # It used to be that when Christine was restarted it would reset all the skipuntils, so she would suddenly just talk and talk.
        # Like all the seldom used phrases would just come out one after another. She was being a bit weird even for a plastic woman.
        # So I thought about saving state, but really if I were to just initialize it first thing it would still be about the same, fine.
        # So now I have started initializing the skip untils to a random amount of time between now and 1.2 x the replay_wait.
        self.update_available_sounds()

    def sound_id_generator(self):
        """Generator that yields sound ids"""

        row = soundsdb.get_collection(self.name)

        # In case the db row has null in that field, like no sounds in the collection
        if row is None or row == "None":
            yield None
        else:
            for element in row.split(","):
                if "-" in element:
                    id_bounds = element.split("-")
                    id_min = int(id_bounds[0])
                    id_max = int(id_bounds[1])
                    for sound_id in range(id_min, id_max + 1):
                        yield sound_id
                elif element.isnumeric():
                    yield int(element)

    def update_available_sounds(self):
        """Updates the list that keeps track of sounds that are available to play"""

        # Store the time so that we don't have to call time so much
        current_seconds = time.time()

        # Throw this 5s in the future
        self.next_update_seconds = current_seconds + 5

        # Empty the list of available sounds
        self.sounds_available_to_play = []

        # Go through all the sounds and add available ones to the list
        for sound in self.sounds_in_collection:
            if sound["SkipUntil"] < current_seconds:
                self.sounds_available_to_play.append(sound)

    def get_random_sound(self, intensity=None):
        """Returns some weird ass rando sound."""

        # if it's time to update the available list, do it
        if self.next_update_seconds < time.time():
            self.update_available_sounds()

        # There may be times that we run out of available sounds and have to throw a None
        if len(self.sounds_available_to_play) == 0:
            log.sound.warning("No sounds available to play in %s", self.name)
            return None

        # if the desired intensity is specified, we want to only select sounds near that intensity
        if intensity is None:
            rando_sound = random.choice(self.sounds_available_to_play)
        else:
            # it is now possible to get an intensity over 1.0, so we need to clip this
            intensity = float(np.clip(intensity, 0.0, 1.0))

            sounds_near_intensity = []
            for sound in self.sounds_available_to_play:
                if math.isclose(sound["intensity"], intensity, abs_tol=0.25):
                    sounds_near_intensity.append(sound)
            if len(sounds_near_intensity) == 0:
                log.sound.warning(
                    "No sounds near intensity %s in %s", intensity, self.name
                )
                return None
            rando_sound = random.choice(sounds_near_intensity)

        return rando_sound

    def set_skip_until(self, sound_id):
        """It used to be that skipuntil got updated in GetRandomSound. That caused a lot of sounds to become unavailable due to a lot of sounds
        being queued but not played in times of heavy activity, often sexual in nature. So now this is only updated when played. Fuck me.
        """

        for sound in self.sounds_in_collection:
            if sound["id"] == sound_id:
                log.sound.debug("Made unavailable: %s", sound)
                sound["SkipUntil"] = time.time() + (
                    sound["replay_wait"] * random.uniform(0.8, 1.2)
                )
                self.sounds_available_to_play.remove(sound)
                break


# Initialize this class that handles the sound database
soundsdb = SoundsDB()

# Load all the sound collections
collections = {}
for name in soundsdb.collection_names_as_list():
    collections[name] = SoundCollection(name)

# If the script is called directly
if __name__ == "__main__":
    log.main.info("Script called directly")

    if sys.argv[1] == "--reprocess-all":
        log.main.info("Reprocessing all")
        soundsdb.reprocess_all()
    elif sys.argv[1] == "--reprocess-modified":
        log.main.info("Reprocessing modified")
        soundsdb.amplify_master_sounds()
    elif sys.argv[1] == "--amplify-master":
        log.main.info("Amplifying master sounds")
        soundsdb.amplify_master_sounds()
    elif sys.argv[1] == "--play-all":
        log.main.info("Playing all master sounds except for normal breaths")
        soundsdb.play_all()
    elif sys.argv[1] == "--play-volume-adjust":
        log.main.info(
            "Playing all master sounds in a loop and allowing volume up/down and also filtering"
        )
        soundsdb.play_all_volume_adjust()

    log.main.info("Done")

    # print(soundsdb.All())
    # print(collections)

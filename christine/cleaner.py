"""Periodic cleaning of cached files."""

import threading
import os
import time

from christine import log

class Cleaner(threading.Thread):
    """Somebody's gotta clean up this mess."""

    name = "Cleaner"

    def __init__(self):
        super().__init__(daemon=True)

        # how old in seconds should a cached wav file be before it gets deleted
        self.cache_ttl = 60 * 60 * 24 * 5 #days

        # how long in seconds to sleep between runs
        self.sleep_interval = 3600

    def run(self):

        while True:

            time.sleep(self.sleep_interval)

            self.clean_broca_cache()
            self.clean_wernicke_cache()

    def clean_broca_cache(self):
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

    def clean_wernicke_cache(self):
        """An audio-ingesting LLM such as Gemini Audio may cache audio files. Clean them up."""
        
        seconds_below_to_delete = time.time() - self.cache_ttl
        cache_dir = 'sounds/wernicke'
        files_deleted = 0
        for file_name in os.listdir(cache_dir):
            if '.wav' in file_name:
                file_path = os.path.join(cache_dir, file_name)
                if os.path.getmtime(file_path) < seconds_below_to_delete:
                    os.remove(file_path)
                    files_deleted += 1

        log.main.info('Cleaned wernicke cache, deleted %s files.', files_deleted)

cleaner = Cleaner()

# Converse functions as a noun, adjective, and verb, and conversate is synonymous with only one sense of the verb use of converse ("to exchange thoughts and opinions in speech"). 

# Furthermore, conversate is a nonstandard form, and widely frowned upon in formal writing. 

# Ok, then it's perfect. 

import log
import status
import sounds
import breath

class Conversate():

    """
        Handles incoming speech and tries to emulate some sort of intelligent response.
    """

    def __init__ (self):

        pass


    def Words(self, words):

        log.words.info(f'Heard: {words}')

        if 'love' in words:
            breath.thread.QueueSound(FromCollection='iloveyoutoo', CutAllSoundAndPlay=True, Priority=7)


# all the others get to be threads, why not me
thread = Conversate()
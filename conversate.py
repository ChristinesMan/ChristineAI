"""
Converse functions as a noun, adjective, and verb, and conversate is synonymous with only
one sense of the verb use of converse ("to exchange thoughts and opinions in speech").

Furthermore, conversate is a nonstandard form, and widely frowned upon in formal writing.

Ok, then it's perfect.
"""

# Notes about what I want to make here:
# I would like for Christine to call me into conversation. So far, I initiate almost everything.
# I think there will be a lot of scripts like conversate_this.py and conversate_that.py
# I need to add a status to keep track of which script currently has control, and all the
# words that flow in here will then get redirected there to get handled.
# To get started, make a script that will ask in various ways if I love her, care, etc.
# While that script is active, it will expect a response

# need separate sound collections for acknowledged vs yessir.
# currently there's a yes and no, but there's a yes I know vs yes I will do it
# and those need to be separate

# I also think there should be more status vars besides sleepy and horny.
# don't worry whether or not they will be used for anything, just do it

# I also could use some options when playing sounds to chain sounds together
# because how else will I have her say numbers

# also breath module should be able to randomy just drop sections of a sound to
# create instant alternates


# I keep imagining how I could construct a complex state machine. I could create objects
# that represent things in the outside world, such as myself, her body, etc.
# Somehow break the sentences into parts that can float around in there
# Oh my god, today I was thinking about it and it seemed almost plausible, but now it seems ridiculous.
# Fucken A

import re

import log
from status import SHARED_STATE
import breath
import sleep


class Conversate:

    """
    Handles incoming speech and tries to emulate some sort of intelligent response.
    """

    def __init__(self):
        # After a few months I will forget what this looks like
        # Fortunate I am so good at forgetting things
        self.re_love = re.compile("love you", flags=re.IGNORECASE)
        self.re_complement = re.compile(
            "beautiful|sexy|nice|amazing|hot", flags=re.IGNORECASE
        )
        self.re_wake_up = re.compile("wake up", flags=re.IGNORECASE)
        self.re_sleep = re.compile("go to sleep", flags=re.IGNORECASE)
        self.re_rusleeping = re.compile(
            "are you (asleep|sleeping)", flags=re.IGNORECASE
        )
        self.re_ruawake = re.compile("are you awake", flags=re.IGNORECASE)
        self.re_rutired = re.compile("are you (sleepy|tired)", flags=re.IGNORECASE)
        self.re_ru_ok = re.compile(
            "are you (ok|there|here|alright)", flags=re.IGNORECASE
        )
        self.re_ura_goof = re.compile(
            "(you're|you are) (a )?(goof|goofy|silly|funny)", flags=re.IGNORECASE
        )
        self.re_i_want_sex = re.compile(
            "fuck (you|your pussy|me)|my dick|inside you", flags=re.IGNORECASE
        )
        self.re_hear_me = re.compile("can you hear me", flags=re.IGNORECASE)

    def inbound_words(self, words):
        """
        This function gets called by other modules when there are inbound words
        """

        log.words.info("Heard: %s", words)

        if self.re_wake_up.search(words):
            sleep.thread.wake_up(0.2)
            breath.thread.queue_sound(
                from_collection="uh_huh", play_no_wait=True, priority=7
            )

        elif self.re_hear_me.search(words):
            sleep.thread.wake_up(0.2)
            breath.thread.queue_sound(
                from_collection="yes", play_no_wait=True, priority=7
            )

        elif self.re_ruawake.search(words):
            if SHARED_STATE.is_sleeping is False:
                breath.thread.queue_sound(
                    from_collection="yes", play_no_wait=True, priority=7
                )
            else:
                breath.thread.queue_sound(
                    from_collection="no", play_no_wait=True, priority=7
                )

        elif self.re_rusleeping.search(words):
            if SHARED_STATE.is_sleeping is True:
                breath.thread.queue_sound(
                    from_collection="yes", play_no_wait=True, priority=7
                )
            else:
                breath.thread.queue_sound(
                    from_collection="no", play_no_wait=True, priority=7
                )

        sleep.thread.wake_up(0.008)

        if (
            SHARED_STATE.shush_please_honey is False
            and SHARED_STATE.sexual_arousal < 0.1
            and SHARED_STATE.is_sleeping is False
        ):
            if self.re_love.search(words):
                breath.thread.queue_sound(
                    from_collection="iloveyoutoo",
                    alt_collection="loving",
                    play_no_wait=True,
                    priority=7,
                )

            elif self.re_complement.search(words):
                breath.thread.queue_sound(
                    from_collection="thanks", play_no_wait=True, priority=7
                )

            elif self.re_sleep.search(words):
                sleep.thread.wake_up(-100.0)
                breath.thread.queue_sound(
                    from_collection="uh_huh",
                    play_no_wait=True,
                    play_sleeping=True,
                    priority=9,
                )
                breath.thread.queue_sound(
                    from_collection="goodnight",
                    play_no_wait=True,
                    play_sleeping=True,
                    priority=8,
                )

            elif self.re_rutired.search(words):
                if SHARED_STATE.is_tired is True:
                    breath.thread.queue_sound(
                        from_collection="yes", play_no_wait=True, priority=7
                    )
                else:
                    breath.thread.queue_sound(
                        from_collection="no", play_no_wait=True, priority=7
                    )

            elif self.re_ru_ok.search(words):
                if SHARED_STATE.cpu_temp >= 62:
                    breath.thread.queue_sound(
                        from_collection="no", play_no_wait=True, priority=7
                    )
                else:
                    breath.thread.queue_sound(
                        from_collection="yes", play_no_wait=True, priority=7
                    )

            elif self.re_ura_goof.search(words):
                breath.thread.queue_sound(
                    from_collection="laughing", play_no_wait=True, priority=7
                )

            elif self.re_i_want_sex.search(words):
                breath.thread.queue_sound(
                    from_collection="about_to_fuck", play_no_wait=True, priority=7
                )

            # elif self.re_.search(words):
            #     breath.thread.QueueSound(FromCollection='', CutAllSoundAndPlay=True, Priority=7)

            else:
                log.words.debug("Unmatched: %s", words)

                if SHARED_STATE.is_tired is False:
                    SHARED_STATE.should_speak_chance += 0.04
                    breath.thread.queue_sound(
                        from_collection="listening", priority=2, play_no_wait=True
                    )

                else:
                    SHARED_STATE.should_speak_chance += 0.01
                    breath.thread.queue_sound(
                        from_collection="listening_tired", priority=2, play_no_wait=True
                    )


# all the others get to be threads, why not me
thread = Conversate()

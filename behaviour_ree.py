"""A collection of regular expressions shared with all behaviour modules."""

import re

# After a few months I hope to forget how this works
# Fortunate I am so good at forgetting things
re_love = re.compile(
    "love you", flags=re.IGNORECASE
)
re_complement = re.compile(
    "beautiful|sexy|nice|amazing|hot", flags=re.IGNORECASE
)
re_wake_up = re.compile(
    "wake up", flags=re.IGNORECASE
)
re_sleep = re.compile(
    "go to sleep", flags=re.IGNORECASE
)
re_stoplistening = re.compile(
    "stop listening", flags=re.IGNORECASE
)
re_rusleeping = re.compile(
    "are you (asleep|sleeping)", flags=re.IGNORECASE
)
re_ruawake = re.compile(
    "are you awake", flags=re.IGNORECASE
)
re_rutired = re.compile(
    "are you (sleepy|tired)", flags=re.IGNORECASE
)
re_ru_ok = re.compile(
    "are you (ok|there|here|alright)", flags=re.IGNORECASE
)
re_ura_goof = re.compile(
    "(you're|you are) (a )?(goof|goofy|silly|funny)", flags=re.IGNORECASE
)
re_i_want_sex = re.compile(
    "fuck (you|your pussy|me)|my dick|inside you", flags=re.IGNORECASE
)
re_hear_me = re.compile(
    "can you hear me", flags=re.IGNORECASE
)
re_getting_up = re.compile(
    "(i need to|i want to|time to) (pee|get up|get back|go to work|work)", flags=re.IGNORECASE
)
re_cuddle = re.compile(
    "(i want to|i need to|will you)(please )? cuddle|cuddle (time|with me) (please )?|i'm holding you", flags=re.IGNORECASE
)
# openai whisper seems to have been trained using a lot of youtube videos that always say thanks for watching
# and for some reason it's also very knowledgeable about anime
re_garbage = re.compile(
    r"thank.+watching|Satsang|Mooji|^ \.$|^ Bark!$|PissedConsumer\.com|Beadaholique\.com|^ you$|^ re$|^ GASP$|^ I'll see you in the next video\.$|thevenusproject", flags=re.IGNORECASE
)
re_sad = re.compile(
    "i.+sorry|i.+tired|i.+sad", flags=re.IGNORECASE
)
re_thanks = re.compile(
    "thank you|thanks", flags=re.IGNORECASE
)
re_shutdown = re.compile(
    "(shutdown|shut down|turn off) your (brain|pie|pi)", flags=re.IGNORECASE
)

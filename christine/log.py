"""
Handles logging for this whole sexy app
"""
import os
import logging
import sys
# import threading
from traceback import format_tb

# Make sure the logs dir exists
os.makedirs("./logs/", exist_ok=True)

# Setup the main log file
logging.basicConfig(
    filename="./logs/main.log",
    filemode="a",
    format="%(asctime)s - %(levelname)s - %(threadName)s - %(message)s",
    level=logging.INFO,
)


# Based on https://stackoverflow.com/questions/11232230/logging-to-two-files-with-different-settings
def setup_logger(name, level=logging.INFO, msg_format="%(asctime)s - %(levelname)s - %(threadName)s - %(message)s"):
    """Function to setup as many loggers as you want"""

    theformat = logging.Formatter(msg_format)
    handler = logging.FileHandler(f"./logs/{name}.log")
    handler.setFormatter(theformat)
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)
    logger.propagate = False

    return logger


# Lots of separate log files
main = setup_logger(
    "main",
    level=logging.DEBUG,
    msg_format="%(asctime)s - %(levelname)s - %(threadName)s - %(message)s",
)
gyro = setup_logger("gyro")
cputemp = setup_logger("cputemp")
sleep = setup_logger("sleep")
db = setup_logger("db", level=logging.WARNING)
broca_main = setup_logger("broca_main")
broca_shuttlecraft = setup_logger("broca_shuttlecraft")
wernicke = setup_logger("wernicke")
light = setup_logger("light")
touch = setup_logger("touch", level=logging.DEBUG)
sex = setup_logger("sex")
horny = setup_logger("horny")
vagina = setup_logger("vagina")
parietal_lobe = setup_logger("parietal_lobe", level=logging.DEBUG)
llm_stream = setup_logger("llm_stream", level=logging.DEBUG)
neocortex = setup_logger("neocortex", level=logging.DEBUG)
imhere = setup_logger("imhere", level=logging.INFO, msg_format="%(module)s.%(funcName)s.%(created)d")

def play_sound():
    """Function to play an exception sound"""

    os.system('aplay ./sounds/erro.wav')

def log_exception(_, value, trace_back):
    """
    Log exceptions to the main log
    """
    main.exception("Uncaught exception: %s", value)
    main.exception("Detail: %s", format_tb(trace_back))
sys.excepthook = log_exception

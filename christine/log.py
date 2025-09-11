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
    level=logging.DEBUG,
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
gyro = setup_logger("gyro", level=logging.DEBUG)
cputemp = setup_logger("cputemp", level=logging.DEBUG)
sleep = setup_logger("sleep", level=logging.DEBUG)
db = setup_logger("db", level=logging.WARNING)
broca_main = setup_logger("broca_main", level=logging.DEBUG)
broca_shuttlecraft = setup_logger("broca_shuttlecraft", level=logging.DEBUG)
wernicke = setup_logger("wernicke", level=logging.DEBUG)
light = setup_logger("light", level=logging.DEBUG)
touch = setup_logger("touch", level=logging.DEBUG)
sex = setup_logger("sex", level=logging.DEBUG)
horny = setup_logger("horny", level=logging.DEBUG)
vagina = setup_logger("vagina", level=logging.DEBUG)
parietal_lobe = setup_logger("parietal_lobe", level=logging.DEBUG)
llm_stream = setup_logger("llm_stream", level=logging.DEBUG)
neocortex = setup_logger("neocortex", level=logging.DEBUG)

def log_exception(_, value, trace_back):
    """
    Log exceptions to the main log
    """
    main.exception("Uncaught exception: %s", value)
    main.exception("Detail: %s", format_tb(trace_back))
sys.excepthook = log_exception

main.info("Script started")

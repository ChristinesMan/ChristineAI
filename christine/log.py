"""
Handles logging for this whole sexy app
"""
import os
import logging
import sys
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
def setup_logger(name, level=logging.DEBUG, msg_format="%(asctime)s - %(message)s"):
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
battery = setup_logger("battery")
sleep = setup_logger("sleep")
db = setup_logger("db")
broca = setup_logger("broca", level=logging.DEBUG)
wernicke = setup_logger("wernicke", level=logging.DEBUG)
light = setup_logger("light")
http = setup_logger("http", level=logging.DEBUG)
touch = setup_logger("touch")
sex = setup_logger("sex", level=logging.DEBUG)
horny = setup_logger("horny")
cuddles = setup_logger("cuddles")
vagina = setup_logger("vagina", level=logging.DEBUG)
behaviour = setup_logger("behaviour", level=logging.DEBUG)
parietallobe = setup_logger("parietallobe", level=logging.DEBUG)
imhere = setup_logger("imhere", level=logging.INFO, msg_format="%(module)s.%(funcName)s.%(created)d")


def log_exception(_, value, trace_back):
    """
    Log exceptions to the main log
    """
    logging.exception("Uncaught exception: %s", value)
    logging.exception("Detail: %s", format_tb(trace_back))


sys.excepthook = log_exception

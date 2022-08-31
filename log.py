import os
import logging
import sys
from traceback import format_tb

# Make sure the logs dir exists
os.makedirs('./logs/', exist_ok=True)

# Setup the main log file
logging.basicConfig(filename='logs/main.log', filemode='a', format='%(asctime)s - %(levelname)s - %(threadName)s - %(message)s', level=logging.DEBUG)

# Setup logging to multiple files. Based on https://stackoverflow.com/questions/11232230/logging-to-two-files-with-different-settings
def setup_logger(name, level=logging.DEBUG, format='%(asctime)s - %(message)s'):
    """Function to setup as many loggers as you want"""

    theformat = logging.Formatter(format)
    handler = logging.FileHandler(f'./logs/{name}.log')
    handler.setFormatter(theformat)
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)
    logger.propagate = False

    return logger

# Lots of separate log files
main     = setup_logger('main',     level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(threadName)s - %(message)s')
gyro     = setup_logger('gyro',     level=logging.DEBUG)
cputemp  = setup_logger('cputemp',  level=logging.DEBUG)
battery  = setup_logger('battery',  level=logging.DEBUG)
sleep    = setup_logger('sleep',    level=logging.DEBUG)
db       = setup_logger('db',       level=logging.DEBUG)
sound    = setup_logger('sound',    level=logging.DEBUG)
wernicke = setup_logger('wernicke', level=logging.DEBUG)
light    = setup_logger('light',    level=logging.DEBUG)
web      = setup_logger('web',      level=logging.DEBUG)
touch    = setup_logger('touch',    level=logging.DEBUG)
sex      = setup_logger('sex',      level=logging.DEBUG)
horny    = setup_logger('horny',    level=logging.DEBUG)
vagina   = setup_logger('vagina',   level=logging.DEBUG)
words    = setup_logger('words',    level=logging.DEBUG)

# I want to log exceptions to the main log. Because it appears that redirecting stderr from the service is not capturing all the errors
# So it looks like syntax and really batshit crazy stuff goes to journalctl. Softer stuff goes into the main log now. 
def log_exception(type, value, tb):
    logging.exception('Uncaught exception: {0}'.format(value))
    logging.exception('Detail: {0}'.format(format_tb(tb)))
sys.excepthook = log_exception

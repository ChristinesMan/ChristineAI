"""
Basic global configuration settings stored in the config.ini.
"""

import configparser

CONFIG = configparser.ConfigParser()
CONFIG.read('config.ini')

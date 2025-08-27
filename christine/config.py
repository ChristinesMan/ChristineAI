"""
Basic global configuration settings stored in the config.ini.
"""

import configparser

CONFIG = configparser.ConfigParser()
CONFIG.read_dict({
    'wernicke': {
        'enabled': 'no',
        'pv_key': 'None',
        'server': 'auto',
    },
    'broca': {
        'enabled': 'no',
        'server': 'auto',
    },
    'parietal_lobe': {
        'user_name': 'Phantom',
        'char_name': 'Christine',
        'base_url': 'https://inference.chub.ai',
        'api_key': 'None',
    },
    'neocortex': {
        'enabled': 'yes',
        'server': 'localhost',
    },
})
CONFIG.read('config.ini')

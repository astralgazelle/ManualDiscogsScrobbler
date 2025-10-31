# config.py

import configparser
import os

CONFIG_FILE = 'config.ini'

def save_config(username, password):
    config = configparser.ConfigParser()
    
    safe_username = username.replace('%', '%%')
    safe_password = password.replace('%', '%%')

    config['LASTFM_USER'] = {
        'username': safe_username,
        'password': safe_password
    }
    with open(CONFIG_FILE, 'w') as configfile:
        config.write(configfile)

def load_config():
    if not os.path.exists(CONFIG_FILE):
        return None
        
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)
    try:
        username = config['LASTFM_USER']['username']
        password = config['LASTFM_USER']['password']
        return username, password
    except KeyError:
        return None
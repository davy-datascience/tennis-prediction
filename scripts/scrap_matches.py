import sys
import configparser

config = configparser.ConfigParser()
config.read("config.ini")

PROJECT_FOLDER = config['project']['folder']
LOG_FILENAME = '{0}logs/{1}'.format(PROJECT_FOLDER, config['logs']['scrap_matches'])

sys.path.append(PROJECT_FOLDER)

try:
    from managers.match_manager import *

    scrap_matches()

except Exception as ex:
    myFile = open(LOG_FILENAME, 'a')
    myFile.write(str(ex) + "\n")

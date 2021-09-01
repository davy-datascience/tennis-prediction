import sys
import configparser

config = configparser.ConfigParser()
config.read("config.ini")

PROJECT_FOLDER = config['project']['folder']
LOG_FILENAME = '{0}logs/{1}'.format(PROJECT_FOLDER, config['logs']['predict_matches'])

sys.path.append(PROJECT_FOLDER)

try:
    from model_deployment.model_deployment import *

    feature_engineer()
    build_predictions()

except Exception as ex:
    myFile = open(PREDICT_LOGS, 'a')
    myFile.write(str(ex) + "\n")

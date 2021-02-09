from datetime import datetime
import sys
import os

PROJECT_FOLDER = '/home/davy/Documents/tennis-prediction/'
LOG_FILENAME = '{0}src/logs/update_player_ranks.out'.format(PROJECT_FOLDER)

myFile = open(LOG_FILENAME, 'a')

try:
    sys.path.append("/home/davy/Documents/tennis-prediction/")

    from src.managers.player_rank_manager import scrap_all_player_ranks
    from src.log import log_to_file

    scrap_all_player_ranks()
    log_to_file("OK", LOG_FILENAME)


except Exception as ex:
    myFile.write("\n" + str(ex))


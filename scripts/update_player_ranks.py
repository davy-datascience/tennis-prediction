import sys

PROJECT_FOLDER = '/home/davy/Documents/tennis-prediction/'
LOG_FILENAME = '{0}logs/update_player_ranks.out'.format(PROJECT_FOLDER)

try:
    sys.path.append("/home/davy/Documents/tennis-prediction/")

    from managers.player_rank_manager import scrap_all_player_ranks
    from log import log_to_file

    scrap_all_player_ranks(LOG_FILENAME)

except Exception as ex:
    myFile = open(LOG_FILENAME, 'a')
    myFile.write("\n" + str(ex))

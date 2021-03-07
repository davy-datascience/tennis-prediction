import sys
import pickledb
import configparser
from datetime import datetime, date

config = configparser.ConfigParser()
config.read("config.ini")

PROJECT_FOLDER = config['project']['folder']
LOG_FILENAME = '{0}logs/{1}'.format(PROJECT_FOLDER, config['logs']['update_player_ranks'])
PICKLE_DB = '{0}logs/pickle.db'.format(PROJECT_FOLDER)

sys.path.append(PROJECT_FOLDER)

# Check if player ranks have already been updated
db = pickledb.load(PICKLE_DB, False)
last_ranking_date_str = db.get("update_player_ranks_date")
if last_ranking_date_str:
    last_ranking_date = datetime.strptime(last_ranking_date_str, '%Y.%m.%d').date()
    today = date.today()
    if last_ranking_date == today:
        # Player ranks have already been updated today
        sys.exit()

try:
    from managers.player_rank_manager import scrap_all_player_ranks

    scrap_all_player_ranks(LOG_FILENAME, PICKLE_DB)

except Exception as ex:
    myFile = open(LOG_FILENAME, 'a')
    myFile.write(str(ex) + "\n")

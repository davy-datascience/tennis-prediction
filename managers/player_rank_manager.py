import re
from datetime import datetime, date

import pandas as pd
import pickledb

from log import log, log_to_file
from queries.player_rank_queries import record_all_player_ranks, retrieve_all_player_ranks
from utils import get_chrome_driver


def scrap_all_player_ranks(log_file_path, pickle_db_path):
    driver = get_chrome_driver()
    try:
        driver.get("https://www.atptour.com/en/rankings/singles")

        date_str = driver.find_element_by_xpath("//div[@class='dropdown-wrapper']/div[1]/div/div").text

        last_ranking_date = datetime.strptime(date_str, '%Y.%m.%d').date()
        today = date.today()

        if last_ranking_date != today:
            # Check if last ranking date on atptour match current date. If not, do not scrap
            raise ValueError()

        driver = get_chrome_driver(driver)
        driver.get("https://www.atptour.com/en/rankings/singles?rankDate={0}&rankRange=1-5000".format(
            date_str.replace(".", "-")))

        ranks = []
        rank_elems = driver.find_elements_by_class_name("rank-cell")
        for rank_elem in rank_elems:
            rank_str = rank_elem.text
            # Some low-level players has rank suffixed with T because they are ex-aequo
            rank_str = rank_str.replace("T", "")
            rank = int(rank_str)
            ranks.append(rank)

        points_elems = driver.find_elements_by_xpath("//td[@class='points-cell']/a")
        rank_points = [points.text for points in points_elems]
        rank_points = [int(points.replace(",", "")) for points in rank_points]

        player_ids = []
        player_elems = driver.find_elements_by_xpath("//td[@class='player-cell']/span[1]/a[1]")
        for elem in player_elems:
            href = elem.get_attribute("href")
            player_id_regex = re.search("players/.*/(.*)/overview", href)
            player_ids.append(player_id_regex.group(1))

        player_ranks = pd.DataFrame({"rank": ranks, "player_id": player_ids, "rank_points": rank_points})

        if record_all_player_ranks(player_ranks):
            log_to_file("Player ranks successfully updated", log_file_path)
            db = pickledb.load(pickle_db_path, True)
            db.set("update_player_ranks_date", date_str)
        else:
            raise Exception('Player ranks not recorded')

    except ValueError:
        log_to_file("Player ranks not updated on atptour", log_file_path)
        pass
    except Exception as ex:
        log("Player_ranks", str(ex))
        pass

    driver.quit()


def retrieve_player_rank_info(player_id, all_player_ranks=None):
    """Retrieve player rank and rank_points"""
    if all_player_ranks is None:
        all_player_ranks = retrieve_all_player_ranks()

    rank_info = all_player_ranks[all_player_ranks["player_id"] == player_id]

    if len(rank_info.index) == 1:
        return rank_info.iloc[0]["rank"], rank_info.iloc[0]["rank_points"]
    else:
        log("player_rank", "Player rank info not found for player '{0}'".format(player_id))
        return None, None


'''
@DeprecationWarning
def fix_ranks():
    # Fix player rank info if CRON of player ranks didn't work
    collection = get_matches_collection()

    all_player_ranks = retrieve_all_player_ranks()
    players = retrieve_players()

    date_from = datetime(2021, 1, 30)  # Date to specify

    matches = pd.DataFrame(list(collection.find({"datetime": {"$gte": date_from}})))

    matches["p1_atp_id"] = matches["p1_id"].apply(lambda p_id: players[players["flash_id"] == p_id].iloc[0]["atp_id"])
    matches["p2_atp_id"] = matches["p2_id"].apply(lambda p_id: players[players["flash_id"] == p_id].iloc[0]["atp_id"])

    matches["p1_rank"], matches["p1_rank_points"] = zip(
        *matches["p1_atp_id"].apply(retrieve_player_rank_info, args=(all_player_ranks,)))
    matches["p2_rank"], matches["p2_rank_points"] = zip(
        *matches["p2_atp_id"].apply(retrieve_player_rank_info, args=(all_player_ranks,)))

    matches.drop(columns=["p1_atp_id", "p2_atp_id"], inplace=True)

    matches.apply(q_update_match, axis=1)'''

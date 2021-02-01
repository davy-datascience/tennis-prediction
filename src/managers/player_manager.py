import time
import re
import pandas as pd
from datetime import datetime

from src.log import log
from src.data_collection.scrap_players import scrap_player_id, scrap_player
from src.queries.player_queries import find_player_by_id, q_create_player
from src.utils import get_chrome_driver, get_mongo_client


def scrap_all_player_ranks():
    driver = get_chrome_driver()
    try:
        driver.get("https://www.atptour.com/en/rankings/singles")

        date_str = driver.find_element_by_xpath("//div[@class='dropdown-wrapper']/div[1]/div/div").text
        driver = get_chrome_driver(driver)
        driver.get("https://www.atptour.com/en/rankings/singles?rankDate={0}&rankRange=1-5000".format(date_str.replace(".", "-")))

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
        player_elems = driver.find_elements_by_xpath("//td[@class='player-cell']/a")
        for elem in player_elems:
            href = elem.get_attribute("href")
            player_id_regex = re.search("players/.*/(.*)/overview", href)
            player_ids.append(player_id_regex.group(1))

        player_ranks = pd.DataFrame({"rank": ranks, "player_id": player_ids, "rank_points": rank_points})

        record_all_player_ranks(player_ranks)

    except Exception as ex:
        print(ex)
        log("Player_ranks", "Couldn't retrieve player ranks")

    driver.quit()


def record_all_player_ranks(player_ranks):
    mongo_client = get_mongo_client()
    database = mongo_client["tennis"]
    collection = database["player_ranks"]

    # Remove previous ranks
    collection.remove()

    # Insert new ranks
    records = player_ranks.to_dict(orient='records')
    result = collection.insert_many(records)
    return result.acknowledged


def retrieve_all_player_ranks():
    mongo_client = get_mongo_client()
    database = mongo_client["tennis"]
    collection = database["player_ranks"]

    player_ranks = pd.DataFrame(list(collection.find({}, {'_id': False})))
    return player_ranks


def retrieve_player_rank_info(player_id, all_player_ranks=None):
    """Retrieve player rank and rank_points"""
    if all_player_ranks == None:
        all_player_ranks = retrieve_all_player_ranks()

    rank_info = all_player_ranks[all_player_ranks["player_id"] == player_id]

    if len(rank_info.index) == 1:
        return rank_info.iloc[0]["rank"], rank_info.iloc[0]["rank_points"]
    else:
        log("player_rank", "Player rank info not found for player '{0}'".format(player_id))
        return None, None


def get_player(player_id, players):
    player_match = players[players["flash_id"] == player_id]
    return player_match.iloc[0] if len(player_match) > 0 else None


def calculate_age(birth_date):
    days_in_year = 365.2425
    age = (datetime.today() - birth_date).days / days_in_year
    return age


def create_player(player):
    inserted_id = q_create_player(player)

    log("player_created", inserted_id)


def add_player_info(match):
    """Add p1 and p2 attributes to a match series"""
    p1 = find_player_by_id(match["p1_id"])
    if p1 is None:
        p1 = scrap_new_player(match["p1_id"], match["p1_url"])
        create_player(p1)

    p2 = find_player_by_id(match["p2_id"])
    if p2 is None:
        p2 = scrap_new_player(match["p2_id"], match["p2_url"])
        create_player(p2)

    if p1 is None or p2 is None:
        print("Couldn't find nor scrap players for  match '{0}'".format(match["match_id"]))
        return

    match["p1_hand"] = p1["handedness"]
    match["p1_backhand"] = p1["backhand"]
    match["p1_ht"] = p1["height"]
    match["p1_weight"] = p1["weight"]
    match["p1_age"] = calculate_age(p1["birth_date"])
    match["p1_rank"], match["p1_rank_points"] = retrieve_player_rank_info(p1["atp_id"])
    match["p1_birth_country"] = p1["birth_country"]
    match["p1_residence_country"] = p1["residence_country"]

    match["p2_hand"] = p2["handedness"]
    match["p2_backhand"] = p2["backhand"]
    match["p2_ht"] = p2["height"]
    match["p2_weight"] = p2["weight"]
    match["p2_age"] = calculate_age(p2["birth_date"])
    match["p2_rank"], match["p2_rank_points"] = retrieve_player_rank_info(p2["atp_id"])
    match["p2_birth_country"] = p2["birth_country"]
    match["p2_residence_country"] = p2["residence_country"]


def scrap_player_name_flashscore(flash_id, flash_url):
    driver = get_chrome_driver()
    match_url = "https://www.flashscore.com/player/{0}/{1}/".format(flash_url, flash_id)
    driver.get(match_url)
    time.sleep(1)
    player_name = driver.find_element_by_class_name("teamHeader__name").text
    driver.quit()
    return player_name


def scrap_new_player(flash_id, flash_url):
    player_full_name = scrap_player_name_flashscore(flash_id, flash_url)
    player_full_name, atp_id = scrap_player_id(player_full_name)
    player = scrap_player(atp_id)

    if player is None:
        return None

    player["flash_id"] = flash_id
    player["flash_url"] = flash_url
    player["player_name"] = player_full_name
    player["atp_id"] = atp_id

    return player

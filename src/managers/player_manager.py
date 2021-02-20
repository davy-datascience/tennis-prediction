import time

from datetime import datetime

from src.log import log
from src.data_collection.scrap_players import scrap_player_id, scrap_player
from src.managers.player_rank_manager import retrieve_player_rank_info
from src.queries.player_queries import find_player_by_id, q_create_player, q_update_player
from src.utils import get_chrome_driver


def get_player(player_id, players):
    player_match = players[players["flash_id"] == player_id]
    return player_match.iloc[0] if len(player_match) > 0 else None


def calculate_age(birth_date):
    days_in_year = 365.2425
    age = (datetime.today() - birth_date).days / days_in_year
    return age


def create_player(player):
    inserted_id = q_create_player(player.to_dict())

    log("player_created", inserted_id)


def update_player(player):
    return q_update_player(player)


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


def create_player_manual(flash_id, flash_url, player_full_name, atp_id):
    player = scrap_player(atp_id)
    if player is None:
        print("couldn't scrap player")

    player["flash_id"] = flash_id
    player["flash_url"] = flash_url
    player["player_name"] = player_full_name
    player["atp_id"] = atp_id

    create_player(player)

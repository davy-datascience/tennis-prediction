import time
import re
import pandas as pd
import pymongo
import configparser

from datetime import datetime
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException

from src.log import log
from src.scrap_players import scrap_new_player
from src.utils import get_chrome_driver


config = configparser.ConfigParser()
config.read("src/config.ini")
MONGO_CLIENT = config['mongo']['client']


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
    myclient = pymongo.MongoClient(MONGO_CLIENT)
    database = myclient["tennis"]
    collection = database["player_ranks"]

    # Remove previous ranks
    collection.remove()

    # Insert new ranks
    records = player_ranks.to_dict(orient='records')
    result = collection.insert_many(records)
    return result.acknowledged


def retrieve_all_player_ranks():
    myclient = pymongo.MongoClient(MONGO_CLIENT)
    database = myclient["tennis"]
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


def add_player_info(match, players):
    """Add p1 and p2 attributes to a match series"""
    p1 = get_player(match["p1_id"], players)
    if p1 is None:
        p1 = scrap_new_player(match["p1_id"], match["p1_url"])

    p2 = get_player(match["p2_id"], players)
    if p2 is None:
        p2 = scrap_new_player(match["p2_id"], match["p2_url"])

    if p1 is None or p2 is None:
        return

    match["p1_id"] = p1["flash_id"]
    match["p1_hand"] = p1["handedness"]
    match["p1_backhand"] = p1["backhand"]
    match["p1_ht"] = p1["height"]
    match["p1_weight"] = p1["weight"]
    match["p1_age"] = calculate_age(p1["birth_date"])
    match["p1_rank"], match["p1_rank_points"] = retrieve_player_rank_info(p1["atp_id"])
    match["p1_birth_country"] = p1["birth_country"]
    match["p1_residence_country"] = p1["residence_country"]
    
    match["p2_id"] = p2["flash_id"]
    match["p2_hand"] = p2["handedness"]
    match["p2_backhand"] = p2["backhand"]
    match["p2_ht"] = p2["height"]
    match["p2_weight"] = p2["weight"]
    match["p2_age"] = calculate_age(p2["birth_date"])
    match["p2_rank"], match["p2_rank_points"] = retrieve_player_rank_info(p2["atp_id"])
    match["p2_birth_country"] = p2["birth_country"]
    match["p2_residence_country"] = p2["residence_country"]

import time
import re
import pandas as pd
import pymongo
import configparser

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException

from src.log import log
from src.utils import get_chrome_driver


config = configparser.ConfigParser()
config.read("src/config.ini")
MONGO_CLIENT = config['mongo']['client']


def scrap_player_ranks():
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

        record_player_ranks(player_ranks)

    except Exception as ex:
        print(ex)
        log("Player_ranks", "Couldn't retrieve player ranks")

    driver.quit()


def record_player_ranks(player_ranks):
    myclient = pymongo.MongoClient(MONGO_CLIENT)
    database = myclient["tennis"]
    collection = database["player_ranks"]

    # Remove previous ranks
    collection.remove()

    # Insert new ranks
    records = player_ranks.to_dict(orient='records')
    result = collection.insert_many(records)
    return result.acknowledged


def retrieve_player_ranks():
    myclient = pymongo.MongoClient(MONGO_CLIENT)
    database = myclient["tennis"]
    collection = database["player_ranks"]

    player_ranks = pd.DataFrame(list(collection.find({}, {'_id': False})))
    return player_ranks


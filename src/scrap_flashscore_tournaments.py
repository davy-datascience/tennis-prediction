import time
from selenium import webdriver
import re
import configparser
import pymongo
import pandas as pd
from datetime import datetime
from dateutil.tz import UTC

config = configparser.ConfigParser()
config.read("src/config.ini")
MONGO_CLIENT = config['mongo']['client']


def find_id(t_name, t_formatted_name, flash_tournaments):
    result = flash_tournaments[flash_tournaments["formatted_name"] == t_formatted_name]
    if len(result.index) == 1:
        return result.iloc[0]["formatted_name"]

    result = flash_tournaments[flash_tournaments["name"] == t_name]
    if len(result.index) == 1:
        return result.iloc[0]["formatted_name"]

    return None


def scrap_flash_score_tournaments(tournaments):
    driver = webdriver.Chrome('/home/davy/Drivers/chromedriver')
    match_url = 'https://www.flashscore.com/tennis/'
    driver.get(match_url)
    time.sleep(0.5)

    names = []
    formatted_names = []

    el = driver.find_element_by_xpath("//li[@id='lmenu_5724']/a")
    driver.execute_script("arguments[0].click();", el)
    time.sleep(1)

    elements = driver.find_elements_by_xpath("//li[@id='lmenu_5724']/ul/li/a")

    for element in elements:
        names.append(element.get_property("text"))

        link = element.get_attribute("href")
        formatted_name = re.search("atp-singles/(.+)/$", link).group(1)
        formatted_names.append(formatted_name)

    driver.quit()

    not_found = []

    flash_tournaments = pd.DataFrame({"name": names, "formatted_name": formatted_names})

    tournaments["flash_id"] = tournaments.apply(
        lambda row: find_id(row["tourney_name"], row["atp_formatted_name"], flash_tournaments), axis=1)

    tournaments_manual_collect = pd.read_csv("datasets/tournaments_flash_manual_collect.csv")

    '''tournaments['flash_id'] = tournaments.apply(
        lambda row: retrieve_missing_tournaments(row["tourney_name"], row["flash_id"], tournaments_manual_collect), axis=1)'''

    tournaments["flash_id"] = tournaments.apply(lambda row: row["flash_id"] if not row["flash_id"] == None
    else tournaments_manual_collect[tournaments_manual_collect["name"] == row["tourney_name"]].iloc[0]["flash_id"], axis=1)

    # tournament 'London' is renamed milan on flashscore
    tournaments["flash_id"] = tournaments.apply(lambda row: row["flash_id"] if row["tourney_name"] != "London" else "milan", axis=1)

    return tournaments


def find_tournament_attribute(attribute, tourney_name, tournaments):
    tour = tournaments[tournaments["tourney_name"] == tourney_name]
    if len(tour.index) == 1:
        return tour.iloc[0][attribute]
    else:
        return None


def add_tournament_info(dataset, tournaments):
    dataset["tournament_id"] = dataset.apply(lambda row: find_tournament_attribute("flash_id", row["tourney_name"], tournaments), axis=1)
    dataset["country"] = dataset.apply(lambda row: find_tournament_attribute("country", row["tourney_name"], tournaments), axis=1)
    return dataset

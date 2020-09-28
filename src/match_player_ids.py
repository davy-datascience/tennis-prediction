import json

import pandas as pd
import re
import time
import pymongo
from dateutil.tz import UTC
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
import configparser
from datetime import date
from src.Classes.player import Player, get_players_json
from datetime import datetime

config = configparser.ConfigParser()
config.read("src/config.ini")
MONGO_CLIENT = config['mongo']['client']


def scrap_player_id(player_name):
    atptour_name = atptour_id = None
    driver = webdriver.Chrome('/home/davy/Drivers/chromedriver')
    match_url = 'https://www.atptour.com/en/search-results/players?searchTerm={}'.format(player_name)
    driver.get(match_url)
    time.sleep(1)  # Wait 1 sec to avoid IP being banned for scrapping
    try:
        element = driver.find_element_by_xpath("//table[@class='player-results-table']/tbody/tr[1]/td[4]/a")
        atptour_name = element.text
        href = element.get_attribute("href")
        href_regex = re.search(".+/(.*)/overview$", href)
        atptour_id = href_regex.group(1)

    except (NoSuchElementException, AttributeError):
        print("Player not found: {0}".format(player_name))

    driver.quit()

    return atptour_name, atptour_id


def search_player(first_name, last_name, players):
    return players.loc[(players["first_name"] == first_name.lower().replace("-", " ")) &
                       (players["last_name"].str.contains(last_name.lower()))]


def match_player(p_id, full_name, players, player_ids, new_players_to_scrap_ids):
    if p_id not in player_ids:
        my_man = None
        matched = re.search("(.*) (.+)$", full_name)

        if matched:
            my_man = search_player(matched.group(1), matched.group(2), players)
        else:
            print("NO MATCH: {}".format(full_name))

        atp_id = None

        if len(my_man) == 0:
            matched = re.search("(.*) (.+ .+)$", full_name)
            if matched:
                my_man = search_player(matched.group(1), matched.group(2), players)

        if len(my_man) == 0:
            matched = re.search("(.*) (.+ .+ .+)$", full_name)
            if matched:
                my_man = search_player(matched.group(1), matched.group(2), players)

        if len(my_man) == 0:
            atptour_name, atptour_id = scrap_player_id(full_name)
            if atptour_name is not None and atptour_id is not None:
                new_players_to_scrap_ids.append(atptour_id)
                atp_id = atptour_id
            else:
                atp_id = "NO MATCH " + full_name

        elif len(my_man) > 1:
            atp_id = "MULTIPLE MATCH " + full_name
        else:
            atp_id = my_man.iloc[0]["player_id"]

        player_ids[p_id] = atp_id

        return atp_id

    else:
        return player_ids[p_id]


def get_player_ids(players_in_matches_dataset):
    start_time = time.time()

    players = pd.read_csv("datasets/atp_players.csv")
    players["first_name"] = [row.lower().replace("-", " ").replace("'", "") for row in players["first_name"]]
    players["last_name"] = [row.lower().replace("-", " ").replace("'", "") for row in players["last_name"]]

    player_ids = {}
    new_players_to_scrap_ids = []

    winner_atp_ids = [match_player(row[0], row[1], players, player_ids, new_players_to_scrap_ids) for row in
                      players_in_matches_dataset.to_numpy()]
    loser_atp_ids = [match_player(row[2], row[3], players, player_ids, new_players_to_scrap_ids) for row in
                     players_in_matches_dataset.to_numpy()]

    # player_atp_ids = [matchPlayer(row[0], row[1], players, player_ids, new_players_to_scrap_ids)
    # for row in players_in_matches_dataset.to_numpy()]

    print("---getPlayerIds  %s seconds ---" % (time.time() - start_time))
    return winner_atp_ids, loser_atp_ids, new_players_to_scrap_ids
    # return (player_atp_ids, new_players_to_scrap_ids)


def retrieve_missing_id(player_id, atptour_id, player_ids_manual_collect):
    if atptour_id.startswith("NO MATCH") or atptour_id.startswith("MULTIPLE MATCH"):
        new_id = player_ids_manual_collect.loc[player_id][0]
        return new_id
    else:
        return atptour_id


def retrieve_missing_ids(dataset):
    # I manually searched corresponding player on atptour.com and saved their corresponding ids in a csv file 
    # csv file is being imported
    player_ids_manual_collect = pd.read_csv("datasets/player_ids_matching_manual_collect.csv", index_col="id")

    p1_ids_dataframe = dataset.apply(
        lambda row: retrieve_missing_id(row["winner_id"], row["p1_id"], player_ids_manual_collect), axis=1)
    p2_ids_dataframe = dataset.apply(
        lambda row: retrieve_missing_id(row["loser_id"], row["p2_id"], player_ids_manual_collect), axis=1)

    return p1_ids_dataframe, p2_ids_dataframe, player_ids_manual_collect


def scrap_player(player_id):
    driver = webdriver.Chrome('/home/davy/Drivers/chromedriver')
    match_url = 'https://www.atptour.com/en/players/player/{}/overview'.format(player_id)
    driver.get(match_url)
    time.sleep(1)  # Wait 1 sec to avoid IP being banned for scrapping

    player = None
    try:
        first_name = driver.find_element_by_xpath("//div[@class='player-profile-hero-name']/div[1]").text
        last_name = driver.find_element_by_xpath("//div[@class='player-profile-hero-name']/div[2]").text

        birth_date = None
        try:
            birth_date_search = driver.find_element_by_xpath("//span[@class='table-birthday']").text
            birth_regex = re.search(r"^\(([0-9]*)\.([0-9]*)\.([0-9]*)\)$", birth_date_search)
            birth_year = birth_regex.group(1)
            birth_month = birth_regex.group(2)
            birth_day = birth_regex.group(3)
            birth_date = datetime(int(birth_year), int(birth_month), int(birth_day))
        except Exception as exc:
            print("problem date")
            print(type(exc))

        turned_pro = None
        try:
            turned_pro_str = driver.find_element_by_xpath(
                "//div[@class='player-profile-hero-overflow']/div[2]/div[1]/table/tbody/tr[1]/td[2]/div/div[2]").text
            turned_pro = int(turned_pro_str)
        except (NoSuchElementException, ValueError):
            pass

        weight = None
        try:
            weight_str = driver.find_element_by_xpath("//span[@class='table-weight-lbs']").text
            weight = int(weight_str)
        except (NoSuchElementException, ValueError):
            pass

        height = None
        try:
            height_str = driver.find_element_by_xpath("//span[@class='table-height-cm-wrapper']").text
            height_regex = re.search(r"^\(([0-9]*)cm\)$", height_str)
            if height_regex:
                height = int(height_regex.group(1))
        except (NoSuchElementException, ValueError, TypeError):
            pass

        flag_code = driver.find_element_by_xpath("//div[@class='player-flag-code']").text
        b_city = b_country = None
        try:
            birth_place = driver.find_element_by_xpath("//div[@class='player-profile-hero-overflow']/div[2]/div["
                                                       "1]/table/tbody/tr[2]/td[1]/div/div[2]").text
            b_matched_location = birth_place.split(", ")
            if len(b_matched_location) > 1:
                b_city = b_matched_location[0]
                b_country = b_matched_location[-1]
        except NoSuchElementException:
            pass

        r_city = r_country = None
        try:
            residence = driver.find_element_by_xpath("//div[@class='player-profile-hero-overflow']/div[2]/div["
                                                     "1]/table/tbody/tr[2]/td[2]/div/div[2]").text

            r_matched_location = residence.split(", ")
            if len(r_matched_location) > 1:
                r_city = r_matched_location[0]
                r_country = r_matched_location[-1]
        except NoSuchElementException:
            pass

        hand = back_hand = None
        try:
            hands = driver.find_element_by_xpath("//div[@class='player-profile-hero-overflow']/div[2]/div["
                                                 "1]/table/tbody/tr[2]/td[3]/div/div[2]").text
            hands_matched = hands.split(", ")
            if len(hands_matched) > 1:
                hand = hands_matched[0]
                back_hand = hands_matched[-1]
        except NoSuchElementException:
            pass

        player = Player(player_id, first_name, last_name, birth_date, turned_pro, weight, height,
                        flag_code, b_city, b_country, r_city, r_country, hand, back_hand)

    except Exception as ex:
        print("Player not found : id= '{}'".format(player_id))
        print(type(ex))

    driver.quit()

    return player


def scrap_players(players_ids):
    players = []

    for player_id in players_ids:
        player = scrap_player(player_id)
        if player is not None:
            players.append(player)

    return players


def format_player(player):
    residence = player["residence"]
    birth_place = player["birthplace"]
    birth_year = player["birth_year"]
    birth_month = player["birth_month"]
    birth_day = player["birth_day"]

    residence_city = residence_country = None
    try:
        residence_splitted = residence.split(", ")
        if len(residence_splitted) > 1:
            residence_city = residence_splitted[0]
            residence_country = residence_splitted[-1]
    except AttributeError:
        pass

    birth_city = birth_country = None
    try:
        birth_place_splitted = birth_place.split(", ")
        if len(birth_place_splitted) > 1:
            birth_city = birth_place_splitted[0]
            birth_country = birth_place_splitted[-1]
    except AttributeError:
        pass

    birth_date = None
    try:
        birth_date = datetime(int(birth_year), int(birth_month), int(birth_day), tzinfo=UTC)
    except ValueError:
        pass

    player["residence_city"] = residence_city
    player["residence_country"] = residence_country
    player["birth_city"] = birth_city
    player["birth_country"] = birth_country
    player["birth_date"] = birth_date
    return player


def record_players(players):
    # Record scrapped players
    players_json = get_players_json(players)
    myclient = pymongo.MongoClient(MONGO_CLIENT)
    mydb = myclient["tennis"]
    mycol = mydb["players"]
    mycol.insert_many(players_json)

    # Record players from csv file
    players_from_csv = pd.read_csv("datasets/atp_players.csv")
    players_from_csv = players_from_csv.apply(lambda row: format_player(row), axis=1)
    players_from_csv.drop(columns=["first_initial", "full_name", "player_url", "birthdate", "weight_kg", "height_ft",
                                   "height_inches", "residence", "birthplace", "birth_year", "birth_month",
                                   "birth_day"],
                          inplace=True)

    list_of_players = [(Player(row["player_id"], row["first_name"], row["last_name"],
                               row["birth_date"].to_pydatetime(),
                               row["turned_pro"], row["weight_lbs"], row["height_cm"], row["flag_code"],
                               row["birth_city"], row["birth_country"], row["residence_city"], row["residence_country"],
                               row["handedness"], row["backhand"])) for index, row in players_from_csv.iterrows()]

    records = get_players_json(list_of_players)

    myclient = pymongo.MongoClient(MONGO_CLIENT)
    mydb = myclient["tennis"]
    mycol = mydb["players"]
    result = mycol.insert_many(records)
    return result.acknowledged

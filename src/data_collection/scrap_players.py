import json
import pandas as pd
import numpy as np
import re
import time
from selenium.common.exceptions import NoSuchElementException
from datetime import datetime
from src.log import log
from src.utils import get_chrome_driver


def scrap_player_id(player_name):
    atptour_name = atptour_id = None
    driver = get_chrome_driver()
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


def search_player_in_csv(full_name, players_csv):
    player = None
    matched = re.search("(.*) (.+)$", full_name)

    if matched:
        player = search_player(matched.group(1), matched.group(2), players_csv)
    else:
        print("NO MATCH: {}".format(full_name))

    atp_id = None

    if len(player) == 0:
        matched = re.search("(.*) (.+ .+)$", full_name)
        if matched:
            player = search_player(matched.group(1), matched.group(2), players_csv)

    if len(player) == 0:
        matched = re.search("(.*) (.+ .+ .+)$", full_name)
        if matched:
            player = search_player(matched.group(1), matched.group(2), players_csv)

    if len(player) == 0:
        # Player not found in csv, scraping on atptour
        atptour_name, atptour_id = scrap_player_id(full_name)
        if atptour_name is not None and atptour_id is not None:
            atp_id = atptour_id

    elif len(player) == 1:
        atp_id = player.iloc[0]["player_id"]

    return atp_id


def get_player_ids(players):
    start_time = time.time()

    players_csv = pd.read_csv("datasets/atp_players.csv")
    players_csv["first_name"] = [row.lower().replace("-", " ").replace("'", "") for row in players_csv["first_name"]]
    players_csv["last_name"] = [row.lower().replace("-", " ").replace("'", "") for row in players_csv["last_name"]]

    players["atp_id"] = players.apply(lambda row: search_player_in_csv(row["player_name"], players_csv), axis=1)

    # players_not_found = players[players["atp_id"].isna()]
    players_manual_collect = pd.read_csv("datasets/player_ids_atptour_manual_collect.csv")

    players["atp_id"] = players.apply(lambda row: row["atp_id"] if row["atp_id"] is not None
    else players_manual_collect[players_manual_collect["id"] == row["player_id"]].iloc[0]["new_id"], axis=1)

    '''player_ids = {}
    new_players_to_scrap_ids = []
    player_ids_to_keep_csv = []

    winner_atp_ids = [
        match_player(row[0], row[1], players_csv, player_ids, new_players_to_scrap_ids, player_ids_to_keep_csv) for row in
        players.to_numpy()]
    loser_atp_ids = [match_player(row[2], row[3], players_csv, player_ids, new_players_to_scrap_ids, player_ids_to_keep_csv)
                     for row in
                     players.to_numpy()]

    print("---getPlayerIds  %s seconds ---" % (time.time() - start_time))
    return winner_atp_ids, loser_atp_ids, new_players_to_scrap_ids, player_ids_to_keep_csv'''

    return players


def add_flash_info(player):
    player_name = player["player_name"]
    driver = get_chrome_driver()
    match_url = 'https://s.livesport.services/search/?q={}&l=1&s=2&f=1%3B1&pid=2&sid=1'.format(player_name)
    driver.get(match_url)
    time.sleep(1)  # Wait 1 sec to avoid IP being banned for scrapping
    flashscore_id = flashscore_url = None
    try:
        element = driver.find_element_by_xpath("//pre").text
        element_regex = re.search(r'{"results":(\[.+\])}', element)
        element_json = element_regex.group(1)
        players_found = json.loads(element_json)

        if len(players_found) == 1:
            flashscore_id = players_found[0]["id"]
            flashscore_url = players_found[0]["url"]
        elif len(players_found) > 1:
            for player_found in players_found:
                if player_found["url"] == str.lower(player_name).replace(" ", "-"):
                    flashscore_id = player_found["id"]
                    flashscore_url = player_found["url"]
                    break

    except (NoSuchElementException, AttributeError):
        pass

    driver.quit()
    # player["flashscore_id"] = flashscore_id
    # player["flashscore_url"] = flashscore_url
    return [flashscore_id, flashscore_url]


def add_info(player):
    player = scrap_player(player["atp_id"])

    if player is None:
        return pd.Series(np.empty((15),dtype=object))

    return pd.Series((player["first_name"], player["first_initial"], player["last_name"], player["full_name"],
                      player["birth_date"], player["turned_pro"], player["weight"], player["height"],
                      player["flag_code"], player["birth_city"], player["birth_country"], player["residence_city"],
                      player["residence_country"], player["handedness"], player["backhand"]))


def find_player_ids(dataset):
    # Find distinct players from dataset
    players = pd.concat([dataset[["winner_id", "winner_name"]].rename(columns={"winner_id": "player_id",
                                                                               "winner_name": "player_name"}),
                         dataset[["loser_id", "loser_name"]].rename(columns={"loser_id": "player_id",
                                                                             "loser_name": "player_name"})])
    players = players.drop_duplicates()

    players = get_player_ids(players)

    players["id-url"] = players.apply(add_flash_info, axis=1)
    players["flash_id"] = players.apply(lambda row: row["id-url"][0], axis=1)
    players["flash_url"] = players.apply(lambda row: row["id-url"][1], axis=1)
    players.drop(columns=["id-url"], inplace=True)
    # not_found = players[players["flash_id"].isna()]

    players_manual_collect = pd.read_csv("datasets/players_flashscor_manual_collect.csv")

    players["flash_id"] = players.apply(lambda row: row["flash_id"] if row["flash_id"] is not None
    else players_manual_collect[players_manual_collect["atp_id"] == row["atp_id"]].iloc[0]["flash_id"], axis=1)

    players["flash_url"] = players.apply(lambda row: row["flash_url"] if row["flash_url"] is not None
    else players_manual_collect[players_manual_collect["atp_id"] == row["atp_id"]].iloc[0]["flash_url"], axis=1)

    start_time = time.time()
    players[["first_name", "first_initial", "last_name", "full_name", "birth_date", "turned_pro", "weight", "height",
             "flag_code", "birth_city", "birth_country", "residence_city", "residence_country", "handedness", "backhand"
             ]] = players.apply(lambda player: add_info(player), axis=1)

    print("--- %s seconds ---" % (time.time() - start_time))

    return players


def scrap_player(atp_id):
    driver = get_chrome_driver()
    match_url = 'https://www.atptour.com/en/players/player/{}/overview'.format(atp_id)
    driver.get(match_url)
    time.sleep(0.5)  # Wait 1 sec to avoid IP being banned for scrapping

    player = pd.Series(dtype='float64')
    try:
        player["first_name"] = driver.find_element_by_xpath("//div[@class='player-profile-hero-name']/div[1]").text
        player["last_name"] = driver.find_element_by_xpath("//div[@class='player-profile-hero-name']/div[2]").text

        player["first_initial"] = player["first_name"][0] if player["first_name"] is not None \
                                                             and player["first_name"] != "" else None
        player["full_name"] = "{0} {1}".format(player["last_name"], player["first_initial"])

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

        player["birth_date"] = birth_date

        turned_pro = None
        try:
            turned_pro_str = driver.find_element_by_xpath(
                "//div[@class='player-profile-hero-overflow']/div[2]/div[1]/table/tbody/tr[1]/td[2]/div/div[2]").text
            turned_pro = int(turned_pro_str)
        except (NoSuchElementException, ValueError):
            pass
        
        player["turned_pro"] = turned_pro

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

        player["weight"] = weight
        player["height"] = height

        player["flag_code"] = driver.find_element_by_xpath("//div[@class='player-flag-code']").text
        
        birth_city = birth_country = None
        try:
            birth_place = driver.find_element_by_xpath("//div[@class='player-profile-hero-overflow']/div[2]/div["
                                                       "1]/table/tbody/tr[2]/td[1]/div/div[2]").text
            b_matched_location = birth_place.split(", ")
            if len(b_matched_location) > 1:
                birth_city = b_matched_location[0]
                birth_country = b_matched_location[-1]
        except NoSuchElementException:
            pass

        player["birth_city"] = birth_city
        player["birth_country"] = birth_country

        residence_city = residence_country = None
        try:
            residence = driver.find_element_by_xpath("//div[@class='player-profile-hero-overflow']/div[2]/div["
                                                     "1]/table/tbody/tr[2]/td[2]/div/div[2]").text

            r_matched_location = residence.split(", ")
            if len(r_matched_location) > 1:
                residence_city = r_matched_location[0]
                residence_country = r_matched_location[-1]
        except NoSuchElementException:
            pass

        player["residence_city"] = residence_city
        player["residence_country"] = residence_country

        handedness = backhand = None
        try:
            hands = driver.find_element_by_xpath("//div[@class='player-profile-hero-overflow']/div[2]/div["
                                                 "1]/table/tbody/tr[2]/td[3]/div/div[2]").text
            hands_matched = hands.split(", ")
            if len(hands_matched) > 1:
                handedness = hands_matched[0]
                backhand = hands_matched[-1]
        except NoSuchElementException:
            pass

        player["handedness"] = handedness
        player["backhand"] = backhand

    except Exception as ex:
        player = None
        log("player_not_found", "Couldn't scrap player : atp_id= '{}'".format(atp_id))
        print(type(ex))

    driver.quit()

    return player


def set_missing_birth_country(birth_country, flag_code, countries):
    if birth_country is not None:
        return birth_country
    else:
        country = countries[countries["NOC"] == flag_code]
        if len(country.index) == 1:
            return country.iloc[0]["Country"]
        else:
            print("flag code {0} not found".format(flag_code))
            return None


def correct_player_country(players, field):
    players[field] = players.apply(
        lambda row: "U.S.A." if row[field] == "AL" else row[field], axis=1)
    players[field] = players.apply(
        lambda row: "Argentina" if row[field] == "ARG" else row[field], axis=1)
    players[field] = players.apply(
        lambda row: "Argentina" if row[field] == "Argentin" else row[field], axis=1)
    players[field] = players.apply(
        lambda row: "Australia" if row[field] == "AUS" else row[field], axis=1)
    players[field] = players.apply(
        lambda row: "Australia" if row[field] == "Aust.." else row[field], axis=1)
    players[field] = players.apply(
        lambda row: "Spain" if row[field] == "Barcelona" else row[field], axis=1)
    players[field] = players.apply(
        lambda row: "Belgium" if row[field] == "Belgium/Assisi,Italy" else row[field], axis=1)
    players[field] = players.apply(
        lambda row: "Brazil" if row[field] == "BRA" else row[field], axis=1)
    players[field] = players.apply(
        lambda row: "Brazil" if row[field] == "Brasil" else row[field], axis=1)
    players[field] = players.apply(
        lambda row: "Bosnia-Herzegovina" if row[field] == "Bosnia" else row[field], axis=1)
    players[field] = players.apply(
        lambda row: "Bosnia-Herzegovina" if row[field] == "Bosnia & Herzegovina" else row[field],
        axis=1)
    players[field] = players.apply(
        lambda row: "U.S.A." if row[field] == "CA" else row[field], axis=1)
    players[field] = players.apply(
        lambda row: "U.S.A." if row[field] == "CT" else row[field], axis=1)
    players[field] = players.apply(
        lambda row: "U.S.A." if row[field] == "California" else row[field], axis=1)
    players[field] = players.apply(
        lambda row: "Taipei" if row[field] == "Chinese Taipei" else row[field], axis=1)
    players[field] = players.apply(
        lambda row: "U.S.A." if row[field] == "Connecticut" else row[field], axis=1)
    players[field] = players.apply(
        lambda row: "Ivory Coast" if row[field] == "Cote d'Ivoire" else row[field], axis=1)
    players[field] = players.apply(
        lambda row: "Czech Republic" if row[field] == "CZE" else row[field], axis=1)
    players[field] = players.apply(
        lambda row: "Czech Republic" if row[field] == "Cz Republic" else row[field], axis=1)
    players[field] = players.apply(
        lambda row: "Czech Republic" if row[field] == "Czech Republic" else row[field], axis=1)
    players[field] = players.apply(
        lambda row: "Czech Republic" if row[field] == "Czech Rep." else row[field], axis=1)
    players[field] = players.apply(
        lambda row: "Czech Republic" if row[field] == "Czech." else row[field], axis=1)
    players[field] = players.apply(
        lambda row: "Czech Republic" if row[field] == "Czechia" else row[field], axis=1)
    players[field] = players.apply(
        lambda row: "Czech Republic" if row[field] == "Czechoslovakia" else row[field], axis=1)
    players[field] = players.apply(
        lambda row: "U.S.A." if row[field] == "D.C." else row[field], axis=1)
    players[field] = players.apply(
        lambda row: "U.S.A." if row[field] == "FL" else row[field], axis=1)
    players[field] = players.apply(
        lambda row: "U.S.A." if row[field] == "FL USA" else row[field], axis=1)
    players[field] = players.apply(
        lambda row: "U.S.A." if row[field] == "GA" else row[field], axis=1)
    players[field] = players.apply(
        lambda row: "U.S.A." if row[field] == "GA 30022" else row[field], axis=1)
    players[field] = players.apply(
        lambda row: "Germany" if row[field] == "GER" else row[field], axis=1)
    players[field] = players.apply(
        lambda row: "Bahamas" if row[field] == "Grand Bahamas" else row[field], axis=1)
    players[field] = players.apply(
        lambda row: "U.S.A." if row[field] == "HI" else row[field], axis=1)
    players[field] = players.apply(
        lambda row: "U.S.A." if row[field] == "Hawaii" else row[field], axis=1)
    players[field] = players.apply(
        lambda row: "Hong Kong" if row[field] == "Hong Kong*" else row[field], axis=1)
    players[field] = players.apply(
        lambda row: "Netherlands" if row[field] == "Holland" else row[field], axis=1)
    players[field] = players.apply(
        lambda row: "U.S.A." if row[field] == "IA" else row[field], axis=1)
    players[field] = players.apply(
        lambda row: "U.S.A." if row[field] == "IL" else row[field], axis=1)
    players[field] = players.apply(
        lambda row: "U.S.A." if row[field] == "Illinois" else row[field], axis=1)
    players[field] = players.apply(
        lambda row: "U.S.A." if row[field] == "IN" else row[field], axis=1)
    players[field] = players.apply(
        lambda row: "U.S.A." if row[field] == "KS" else row[field], axis=1)
    players[field] = players.apply(
        lambda row: "South Korea" if row[field] == "Korea" else row[field], axis=1)
    players[field] = players.apply(
        lambda row: "South Korea" if row[field] == "Korea, South" else row[field], axis=1)
    players[field] = players.apply(
        lambda row: "South Korea" if row[field] == "Korea Republic of" else row[field], axis=1)
    players[field] = players.apply(
        lambda row: "U.S.A." if row[field] == "MA" else row[field], axis=1)
    players[field] = players.apply(
        lambda row: "U.S.A." if row[field] == "MI" else row[field], axis=1)
    players[field] = players.apply(
        lambda row: "U.S.A." if row[field] == "MN" else row[field], axis=1)
    players[field] = players.apply(
        lambda row: "U.S.A." if row[field] == "MO" else row[field], axis=1)
    players[field] = players.apply(
        lambda row: "U.S.A." if row[field] == "NC" else row[field], axis=1)
    players[field] = players.apply(
        lambda row: "U.S.A." if row[field] == "NJ" else row[field], axis=1)
    players[field] = players.apply(
        lambda row: "U.S.A." if row[field] == "NY" else row[field], axis=1)
    players[field] = players.apply(
        lambda row: "U.S.A." if row[field] == "NV" else row[field], axis=1)
    players[field] = players.apply(
        lambda row: "U.S.A." if row[field] == "New York" else row[field], axis=1)
    players[field] = players.apply(
        lambda row: "Great Britain" if row[field] == "Norfolk" else row[field], axis=1)
    players[field] = players.apply(
        lambda row: "Macedonia" if row[field] == "North Macedonia" else row[field], axis=1)
    players[field] = players.apply(
        lambda row: "Russia" if row[field] == "North-Ossetia" else row[field], axis=1)
    players[field] = players.apply(
        lambda row: "U.S.A." if row[field] == "OH" else row[field], axis=1)
    players[field] = players.apply(
        lambda row: "U.S.A." if row[field] == "OR" else row[field], axis=1)
    players[field] = players.apply(
        lambda row: "U.S.A." if row[field] == "PA" else row[field], axis=1)
    players[field] = players.apply(
        lambda row: "U.S.A." if row[field] == "PA U.S.A." else row[field], axis=1)
    players[field] = players.apply(
        lambda row: "Australia" if row[field] == "Plains,Tasmania,Aust." else row[field], axis=1)
    players[field] = players.apply(
        lambda row: "South Africa" if row[field] == "RSA" else row[field], axis=1)
    players[field] = players.apply(
        lambda row: "Romania" if row[field] == "Rumania" else row[field], axis=1)
    players[field] = players.apply(
        lambda row: "Russia" if row[field] == "Russian Federation" else row[field], axis=1)
    players[field] = players.apply(
        lambda row: "Australia" if row[field] == "S.A. Australia" else row[field], axis=1)
    players[field] = players.apply(
        lambda row: "Canada" if row[field] == "Saskatchewan,Canada" else row[field], axis=1)
    players[field] = players.apply(
        lambda row: "Slovakia" if row[field] == "Slovak" else row[field], axis=1)
    players[field] = players.apply(
        lambda row: "Slovakia" if row[field] == "Slovak Republic" else row[field], axis=1)
    players[field] = players.apply(
        lambda row: "Serbia" if row[field] == "SERBIA" else row[field], axis=1)
    players[field] = players.apply(
        lambda row: "Spain" if row[field] == "Spai" else row[field], axis=1)
    players[field] = players.apply(
        lambda row: "U.S.A." if row[field] == "SC" else row[field], axis=1)
    players[field] = players.apply(
        lambda row: "U.S.A." if row[field] == "TN" else row[field], axis=1)
    players[field] = players.apply(
        lambda row: "U.S.A." if row[field] == "TX" else row[field], axis=1)
    players[field] = players.apply(
        lambda row: "U.S.A." if row[field] == "TX USA" else row[field], axis=1)
    players[field] = players.apply(
        lambda row: "U.S.A." if row[field] == "Texas" else row[field], axis=1)
    players[field] = players.apply(
        lambda row: "Australia" if row[field] == "Tasmania,Australia" else row[field], axis=1)
    players[field] = players.apply(
        lambda row: "U.S.A." if row[field] == "Tennessee" else row[field], axis=1)
    players[field] = players.apply(
        lambda row: "Netherlands" if row[field] == "The Netherlands" else row[field], axis=1)
    players[field] = players.apply(
        lambda row: "U.A.E." if row[field] == "UAE" else row[field], axis=1)
    players[field] = players.apply(
        lambda row: "U.S.A." if row[field] == "USA." else row[field], axis=1)
    players[field] = players.apply(
        lambda row: "U.S.A." if row[field] == "USA/Stockholm" else row[field], axis=1)
    players[field] = players.apply(
        lambda row: "U.S.A." if row[field] == "USA; Grand Bahama" else row[field], axis=1)
    players[field] = players.apply(
        lambda row: "U.S.A." if row[field] == "U.S.A" else row[field], axis=1)
    players[field] = players.apply(
        lambda row: "U.S.A." if row[field] == "US" else row[field], axis=1)
    players[field] = players.apply(
        lambda row: "U.S.A." if row[field] == "USA" else row[field], axis=1)
    players[field] = players.apply(
        lambda row: "U.S.A." if row[field] == "United States" else row[field], axis=1)
    players[field] = players.apply(
        lambda row: "Great Britain" if row[field] == "United Kingdom" else row[field], axis=1)
    players[field] = players.apply(lambda row: "Great Britain" 
        if row[field] == "United Kingdom of Great Britain and Northern Ireland" else row[field], axis=1)
    players[field] = players.apply(
        lambda row: "U.S.A." if row[field] == "United States of America" else row[field], axis=1)
    players[field] = players.apply(
        lambda row: "U.S.A." if row[field] == "VA" else row[field], axis=1)
    players[field] = players.apply(
        lambda row: "U.S.A." if row[field] == "WI" else row[field], axis=1)
    players[field] = players.apply(
        lambda row: "Australia" if row[field] == "Victoria" else row[field], axis=1)

    return players


def clean_players(players):
    countries_iso_codes = pd.read_csv(
        "https://raw.githubusercontent.com/johnashu/datacamp/master/medals/Summer%20Olympic%20medalists%201896%20to%202008%20-%20IOC%20COUNTRY%20CODES.csv")

    players["birth_country"] = players.apply(
        lambda row: set_missing_birth_country(row["birth_country"], row["flag_code"], countries_iso_codes), axis=1)

    players["birth_country"] = players.apply(lambda row: "Romania" if pd.isna(row["birth_country"]) and row["flag_code"] == "ROU" else row["birth_country"], axis=1)
    players["birth_country"] = players.apply(lambda row: "Serbia" if pd.isna(row["birth_country"]) and row["flag_code"] == "SRB" else row["birth_country"], axis=1)

    players = correct_player_country(players, "birth_country")
    players = correct_player_country(players, "residence_country")

    players["backhand"] = players.apply(lambda row: None if row["backhand"] == "Unknown Backhand" else row["backhand"], axis=1)

    return players


def add_player_attribute(attribute, player_id, players):
    play = players[players["player_id"] == player_id]
    if len(play.index) == 1:
        return play.iloc[0][attribute]
    else:
        return None


def add_players_info(dataset, players):
    dataset["p1_id"] = dataset.apply(lambda row: add_player_attribute("flash_id", row["winner_id"], players), axis=1)
    dataset["p2_id"] = dataset.apply(lambda row: add_player_attribute("flash_id", row["loser_id"], players), axis=1)
    dataset["p1_weight"] = dataset.apply(lambda row: add_player_attribute("weight", row["winner_id"], players), axis=1)
    dataset["p2_weight"] = dataset.apply(lambda row: add_player_attribute("weight", row["loser_id"], players), axis=1)
    dataset["p1_birth_country"] = dataset.apply(lambda row: add_player_attribute("birth_country", row["winner_id"], players), axis=1)
    dataset["p2_birth_country"] = dataset.apply(lambda row: add_player_attribute("birth_country", row["loser_id"], players), axis=1)
    dataset["p1_residence_country"] = dataset.apply(lambda row: add_player_attribute("residence_country", row["winner_id"], players), axis=1)
    dataset["p2_residence_country"] = dataset.apply(lambda row: add_player_attribute("residence_country", row["loser_id"], players), axis=1)
    dataset["p1_backhand"] = dataset.apply(lambda row: add_player_attribute("backhand", row["winner_id"], players), axis=1)
    dataset["p2_backhand"] = dataset.apply(lambda row: add_player_attribute("backhand", row["loser_id"], players), axis=1)
    dataset["p1_displayname"] = dataset.apply(lambda row: add_player_attribute("full_name", row["winner_id"], players), axis=1)
    dataset["p2_displayname"] = dataset.apply(lambda row: add_player_attribute("full_name", row["loser_id"], players), axis=1)
    dataset["p1_lastname"] = dataset.apply(lambda row: add_player_attribute("last_name", row["winner_id"], players),axis=1)
    dataset["p2_lastname"] = dataset.apply(lambda row: add_player_attribute("last_name", row["loser_id"], players),axis=1)

    return dataset

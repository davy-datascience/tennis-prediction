from selenium import webdriver
import pandas as pd
import re
import time
from datetime import datetime
from dateutil.tz import UTC
from selenium.common.exceptions import NoSuchElementException

from src.Classes.tournament import Tournament


def find_tournament(tour_id, tour_category, year):
    suffixe = "atp" if tour_category == "atp" else tour_category + "-men"

    driver = webdriver.Chrome('/home/davy/Drivers/chromedriver')
    try:
        match_url = "https://www.flashscore.com/tennis/{0}-singles/{1}-{2}/results/".format(suffixe, tour_id, year)
        driver.get(match_url)
        time.sleep(1)
        driver.find_element_by_class_name("container__mainInner")
        return driver
    except NoSuchElementException:
        pass

    tour_categories = ["atp", "challenger", "itf"]
    tour_categories.remove(tour_category)
    tour_category = tour_categories[0]
    suffixe = "atp" if tour_category == "atp" else tour_category + "-men"
    try:
        match_url = "https://www.flashscore.com/tennis/{0}-singles/{1}-{2}/results/".format(suffixe, tour_id, year)
        driver.get(match_url)
        time.sleep(1)
        driver.find_element_by_class_name("container__mainInner")
        return driver
    except NoSuchElementException:
        pass

    tour_categories.remove(tour_category)
    tour_category = tour_categories[0]
    suffixe = "atp" if tour_category == "atp" else tour_category + "-men"
    try:
        match_url = "https://www.flashscore.com/tennis/{0}-singles/{1}-{2}/results/".format(suffixe, tour_id, year)
        driver.get(match_url)
        time.sleep(1)
        driver.find_element_by_class_name("container__mainInner")
        return driver
    except NoSuchElementException:
        driver.quit()
        return None


def find_matches_in_tournament(tour_id, tour_category, year):
    matches_dataframe = None
    driver = find_tournament(tour_id, tour_category, year)
    if driver is not None:
        elements = driver.find_elements_by_xpath(
            "//div[contains(@class, 'event__match event__match--static event__match--')]/div[1]")
        datetimes = []
        for element in elements:
            datetimes.append(element.text)

        elements = driver.find_elements_by_xpath(
            "//div[contains(@class, 'event__match event__match--static event__match--')]/div[2]")
        players1 = []
        for element in elements:
            name_regex = re.search(r"^(.+) .\.", element.text)
            players1.append(name_regex[1])

        elements = driver.find_elements_by_xpath(
            "//div[contains(@class, 'event__match event__match--static event__match--')]/div[3]")
        players2 = []
        for element in elements:
            name_regex = re.search(r"^(.+) .\.", element.text)
            players2.append(name_regex[1])

        dic = {"datetime": datetimes, "p1": players1, "p2": players2}
        matches_dataframe = pd.DataFrame(dic)
        driver.quit()
    else:
        print("Error while retrieving {0} {1} matches".format(year, tour_id))

    return matches_dataframe


def get_lastname(p_id, players_df):
    player_found = players_df[players_df["atptour_id"] == p_id]
    return player_found.iloc[0]["last_name"]


def get_tour_category(tour_id, tournaments_df):
    tour_found = tournaments_df[tournaments_df["atptour_id"] == tour_id]
    return tour_found.iloc[0]["category"]


def find_match_datetime(p1_lastname, p2_lastname, matches, tour_f_id, year):
    """Find match datetime, given matches in the correct tournament and correct year"""
    retrieved_datetime = None

    result = matches[((matches["p1"] == p1_lastname) & (matches["p2"] == p2_lastname))
                     | ((matches["p1"] == p2_lastname) & (matches["p2"] == p1_lastname))]

    if len(result.index) == 1:
        match_dt_str = result.iloc[0]["datetime"]
        match_dt_regex = re.search("^([0-9]+).([0-9]+). ([0-9]+):([0-9]+)$", match_dt_str)
        if match_dt_regex:
            day = match_dt_regex.group(1)
            month = match_dt_regex.group(2)
            hour = match_dt_regex.group(3)
            minute = match_dt_regex.group(4)
            retrieved_datetime = datetime(year, int(month), int(day), int(hour), int(minute))
        else:
            print("Can't retrieve datetime from string '{}'".format(match_dt_str))

    elif len(result.index) == 0:
        my_file = open('/home/davy/Documents/Log_scrap_datetime.txt', 'a')
        my_file.write("\n{0},{1},{2},{3}".format(tour_f_id, year, p1_lastname, p2_lastname))
        '''print("Match not found: tournament '{0}' year {1} '{2}' vs '{3} ".format(tour_f_id, year, p1_lastname,
                                                                                 p2_lastname))'''
    else:
        print("Several matches found: tournament '{0}' year {1} '{0}' vs '{1}".format(tour_f_id, year, p1_lastname,
                                                                                      p2_lastname))

    return retrieved_datetime


def find_matches_datetimes(p1_lastname, p2_lastname, tour_f_id, tour_category, year, tour_matches):
    key = (tour_f_id, year)
    if key not in tour_matches:
        tour_matches[key] = find_matches_in_tournament(tour_f_id, tour_category, year)

    matches = tour_matches[key]
    if matches is not None:
        return find_match_datetime(p1_lastname, p2_lastname, matches, tour_f_id, year)
    else:
        return None


def get_tour_date(date_str):
    year = date_str[:4]
    month = date_str[4:6]
    day = date_str[6:]
    return datetime(int(year), int(month), int(day), tzinfo=UTC)


def correct_wrong_year(tour_f_id, year):
    if (tour_f_id, year) in [("adelaide", 1990), ("wellington", 1990), ("adelaide", 1991), ("wellington", 1991),
                             ("adelaide", 1996), ("doha", 1996), ("adelaide", 2001), ("doha", 2001), ("pune", 2001),
                             ("adelaide", 2002), ("doha", 2002), ("pune", 2002), ("adelaide", 2007), ("doha", 2007),
                             ("pune", 2007), ("brisbane", 2012), ("pune", 2012), ("doha", 2012), ("brisbane", 2013),
                             ("pune", 2013), ("doha", 2013), ("brisbane", 2018), ("pune", 2018), ("doha", 2018)]:
        return year + 1
    else:
        return year

def add_matches_datetime(dataset, tournaments, players):
    players_df = pd.DataFrame.from_records([p.to_dict() for p in players])
    tournaments_df = pd.DataFrame()
    for i in range(len(tournaments)):
        tournaments_df = pd.concat([tournaments_df, pd.DataFrame({"atptour_id": tournaments[i].atptour_id,
                                                                  "category": tournaments[i].category}, index=[i])])

    dataset_full = dataset.copy()
    dataset_full["p1_lastname"] = dataset_full.apply(lambda row: get_lastname(row["p1_id"], players_df), axis=1)
    dataset_full["p2_lastname"] = dataset_full.apply(lambda row: get_lastname(row["p2_id"], players_df), axis=1)

    dataset_full["tour_category"] = dataset_full.apply(lambda row: get_tour_category(row["tournament_id"],
                                                                                     tournaments_df), axis=1)

    dataset_full["tour_date"] = dataset_full.apply(lambda row: get_tour_date(str(row["tourney_date"])), axis=1)

    dataset_full["year"] = dataset_full.apply(lambda row: correct_wrong_year(
        row["tournament_flashscore_id"], row["year"]), axis=1)

    tour_matches = {}

    datetimes = dataset_full.apply(
        lambda match: find_matches_datetimes(match["p1_lastname"], match["p2_lastname"],
                                             match["tournament_flashscore_id"], match["tour_category"],
                                             match["year"], tour_matches), axis=1)

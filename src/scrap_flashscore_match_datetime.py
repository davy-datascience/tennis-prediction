from selenium import webdriver
import pandas as pd
import re
import time
from datetime import datetime
from dateutil.tz import UTC
from selenium.common.exceptions import NoSuchElementException

from src.Classes.tournament import Tournament


def find_tournament_in_category(tour_id, category, year):
    driver = webdriver.Chrome('/home/davy/Drivers/chromedriver')

    try:
        match_url = "https://www.flashscore.com/tennis/{0}-singles/{1}-{2}/results/".format(category, tour_id, year)
        driver.get(match_url)
        time.sleep(1)
        driver.find_element_by_class_name("container__mainInner")
        return driver
    except NoSuchElementException:
        driver.quit()
        return None


def find_tournament_bis(tour_id, tour_category, year):
    suffixe = "atp" if tour_category == "atp" else tour_category + "-men"

    driver = find_tournament_in_category(tour_id, suffixe, year)

    if driver is not None:
        return driver

    suffixes = ["atp", "itf-men", "challenger-men"]
    suffixes.remove(suffixe)
    suffixe = suffixes[0]

    driver = find_tournament_in_category(tour_id, suffixe, year)

    if driver is not None:
        return driver

    suffixes.remove(suffixe)
    suffixe = suffixes[0]

    driver = find_tournament_in_category(tour_id, suffixe, year)

    if driver is not None:
        return driver
    else:
        return None


def find_tournament(tour_id, tour_category, year):
    driver = find_tournament_bis(tour_id, tour_category, year)
    if driver is not None:
        return driver

    name_links = pd.read_csv("datasets/tournaments_name_has_changed.csv")
    new_names_result = name_links[name_links["name"] == tour_id]
    if len(new_names_result.index) > 0:
        new_names = new_names_result.iloc[0]["new_name"]
        new_names = new_names.split(";")
        for new_name in new_names:
            driver = find_tournament_bis(new_name, tour_category, year)
            if driver is not None:
                return driver

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
        p1_lastnames = []
        p1_displaynames = []
        for element in elements:
            name_regex = re.search(r"^(.+) .+\.+ \(", element.text)
            if not name_regex:
                # Retrieve the last name without initial when there are 2 initials in first name
                name_regex = re.search(r"^(.+)( .\.){2} \(", element.text)

            if name_regex:
                p1_lastnames.append(name_regex.group(1))
            else:
                # some names without initial
                name_regex = re.search(r"^(.+) \(", element.text)
                p1_lastnames.append(name_regex.group(1))

            displayname_regex = re.search(r"^(.+ .\.) \(", element.text)
            if displayname_regex:
                p1_displaynames.append(displayname_regex.group(1))
            else:
                p1_displaynames.append(None)

        elements = driver.find_elements_by_xpath(
            "//div[contains(@class, 'event__match event__match--static event__match--')]/div[3]")
        p2_lastnames = []
        p2_displaynames = []
        for element in elements:
            name_regex = re.search(r"^(.+) .+\.+ \(", element.text)
            if not name_regex:
                # Retrieve the last name without initial when there are 2 initials in first name
                name_regex = re.search(r"^(.+)( .\.){2} \(", element.text)

            if name_regex:
                p2_lastnames.append(name_regex.group(1))
            else:
                # some names without initial
                name_regex = re.search(r"^(.+) \(", element.text)
                p2_lastnames.append(name_regex.group(1))

            displayname_regex = re.search(r"^(.+ .\.) \(", element.text)
            if displayname_regex:
                p2_displaynames.append(displayname_regex.group(1))
            else:
                p2_displaynames.append(None)

        dic = {"datetime": datetimes, "p1_lastname": p1_lastnames, "p1_displayname": p1_displaynames,
               "p2_lastname": p2_lastnames, "p2_displayname": p2_displaynames}
        matches_dataframe = pd.DataFrame(dic)
        driver.quit()
    else:
        print("Error while retrieving {0} {1} matches".format(year, tour_id))

    return matches_dataframe


def get_lastname(p_id, players_df):
    player_found = players_df[players_df["atptour_id"] == p_id]
    return player_found.iloc[0]["last_name"]


def get_displayname(p_id, players_df):
    player_found = players_df[players_df["atptour_id"] == p_id]
    last_name = player_found.iloc[0]["last_name"]
    first_name = player_found.iloc[0]["first_name"]
    return "{0} {1}.".format(last_name, first_name[0])


def get_tour_category(tour_id, tournaments_df):
    tour_found = tournaments_df[tournaments_df["atptour_id"] == tour_id]
    return tour_found.iloc[0]["category"]


def find_match_datetime(p1_lastname, p2_lastname, p1_displayname, p2_displayname, matches, tour_f_id, year):
    """Find match datetime, given matches in the correct tournament and correct year"""
    retrieved_datetime = None

    result = matches[((matches["p1_lastname"] == p1_lastname) & (matches["p2_lastname"] == p2_lastname))
                     | ((matches["p1_lastname"] == p2_lastname) & (matches["p2_lastname"] == p1_lastname))]

    if len(result.index) != 1:
        result = matches[((matches["p1_displayname"] == p1_displayname) & (matches["p2_displayname"] == p2_displayname))
                         | ((matches["p1_displayname"] == p2_displayname) & (matches["p2_displayname"] == p1_displayname))]

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
            print("Can't retrieve datetime from string '{0}' tournament '{1}' year '{2}'"
                  .format(match_dt_str, tour_f_id, year))

    elif len(result.index) == 0:
        my_file = open('/home/davy/Documents/Log_scrap_datetime.txt', 'a')
        my_file.write("\n{0},{1},{2},{3}".format(tour_f_id, year, p1_lastname, p2_lastname))
        '''print("Match not found: tournament '{0}' year {1} '{2}' vs '{3} ".format(tour_f_id, year, p1_lastname,
                                                                                 p2_lastname))'''
    else:
        print("Several matches found: tournament '{0}' year {1} '{2}' vs '{3}".format(tour_f_id, year, p1_lastname,
                                                                                      p2_lastname))

    return retrieved_datetime


def find_matches_datetimes(p1_lastname, p2_lastname, p1_displayname, p2_displayname, tour_f_id, tour_category, year, match_dt, tour_matches):
    if not pd.isna(match_dt):
        return match_dt

    key = (tour_f_id, year)
    if key not in tour_matches:
        tour_matches[key] = find_matches_in_tournament(tour_f_id, tour_category, year)

    matches = tour_matches[key]
    if matches is not None:
        return find_match_datetime(p1_lastname, p2_lastname, p1_displayname, p2_displayname, matches, tour_f_id, year)
    else:
        return None


def get_tour_date(date_str):
    year = date_str[:4]
    month = date_str[4:6]
    day = date_str[6:]
    return datetime(int(year), int(month), int(day), tzinfo=UTC)


def correct_wrong_year(tour_f_id, year):
    if (tour_f_id, year) in [("adelaide", 1990), ("wellington", 1990), ("adelaide", 1991), ("wellington", 1991),
                             ("doha", 1996), ("adelaide", 2001), ("doha", 2001), ("pune", 2001),
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

    dataset_full["p1_displayname"] = dataset_full.apply(lambda row: get_displayname(row["p1_id"], players_df), axis=1)
    dataset_full["p2_displayname"] = dataset_full.apply(lambda row: get_displayname(row["p2_id"], players_df), axis=1)

    dataset_full["tour_category"] = dataset_full.apply(lambda row: get_tour_category(row["tournament_id"],
                                                                                     tournaments_df), axis=1)

    dataset_full["tour_date"] = dataset_full.apply(lambda row: get_tour_date(str(row["tourney_date"])), axis=1)

    '''dataset_full["year"] = dataset_full.apply(lambda row: correct_wrong_year(
        row["tournament_flashscore_id"], row["year"]), axis=1)'''

    tour_matches = {}

    dataset_full["datetime2"] = dataset_full.apply(
        lambda match: find_matches_datetimes(match["p1_lastname"], match["p2_lastname"], match["p1_displayname"],
                                             match["p2_displayname"], match["tournament_flashscore_id"],
                                             match["tour_category"], match["year"], match["datetime"], tour_matches)
        , axis=1)  # TODO delete match.datetime param

    ###################
    todelete = []
    for key, value in tour_matches.items():
        if value is None:
            todelete.append(key)

    '''for key in [("indianapolis", 1991), ("schenectady", 1991), ("sydney", 1992), ("rotterdam", 1992), ("estoril", 1992),
                ("us-open", 1992), ("sydney", 1993), ("hong-kong", 1993), ("genova", 1993), ("beijing", 1993),
                ("beijing", 1994), ("finals-londres", 1994), ("estoril", 1995), ("beijing", 1995), ("estoril", 1996),
                ("finals-londres", 1996), ("australian-open", 1997), ("", ), ("", ), ("", ), ("", ), ("", ), ("", )]:'''





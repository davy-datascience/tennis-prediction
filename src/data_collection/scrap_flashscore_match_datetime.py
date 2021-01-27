import pandas as pd
import numpy as np
import re
import time
from datetime import datetime
from pytz import timezone
from selenium.common.exceptions import NoSuchElementException

from src.utils import get_chrome_driver, element_has_class


def extract_lastname_and_displayname(player_str):
    lastname = None
    displayname = None

    name_regex = re.search(r"^([^.]+) .+(\. )+\(", player_str)
    if name_regex:
        lastname = str.lower(name_regex.group(1))
    else:
        # some names without initial
        name_regex = re.search(r"^(.+) \(", player_str)
        lastname = str.lower(name_regex.group(1))

    lastname_tiny = str.lower(re.split(r'[- ]', player_str)[0])

    displayname_regex = re.search(r"^(.+ .\.) \(", player_str)
    if displayname_regex:
        displayname = str.lower(displayname_regex.group(1))

    return displayname, lastname, lastname_tiny


def find_matches_in_tournament(tour_id, year):
    driver = get_chrome_driver()

    try:
        match_url = "https://www.flashscore.com/tennis/atp-singles/{0}-{1}/results/".format(tour_id, year)
        driver.get(match_url)
        time.sleep(1)
        driver.find_element_by_class_name("container__mainInner")
    except NoSuchElementException:
        print("Error while retrieving {0} {1} matches".format(year, tour_id))
        driver.quit()
        return None

    try:
        # Expand all matches
        link_more_matches = driver.find_element_by_xpath("//div[@class='sportName tennis']/a")
        time.sleep(2)
        link_more_matches.click()
        time.sleep(2)

    except Exception:
        pass

    match_ids = []
    datetimes = []
    match_rounds = []
    p1_lastnames = []
    p1_lastnames_tiny = []
    p1_displaynames = []
    p2_lastnames = []
    p2_lastnames_tiny = []
    p2_displaynames = []
    p1_s1_gms = []
    p2_s1_gms = []
    p1_s2_gms = []
    p2_s2_gms = []
    p1_s3_gms = []
    p2_s3_gms = []

    is_qualif = False
    match_round = None

    elements = driver.find_elements_by_xpath("//div[@class='sportName tennis']/div")
    for elem in elements:
        # Tournament name row
        if element_has_class(elem, "event__header"):
            match_round = None
            name = elem.find_element_by_class_name("event__title--name").text
            qualification_regex = re.search("Qualification", name)
            is_qualif = True if qualification_regex else False
            continue
        elif element_has_class(elem, "event__round"):
            # Round row
            match_round = elem.text
        else:
            # Match row
            if is_qualif:
                # Ignore qualif
                continue

            match_id_regex = re.search("^._._(.*)$", elem.get_attribute("id"))
            match_id = match_id_regex.group(1)
            match_ids.append(match_id)

            match_datetime = elem.find_element_by_xpath("div[1]").text.split("\n")[0]
            datetimes.append(match_datetime)

            if match_round is None:
                match_round = "Group"
            match_rounds.append(match_round)

            displayname, lastname, lastname_tiny = extract_lastname_and_displayname(
                elem.find_element_by_xpath("div[2]").text)
            p1_lastnames.append(lastname)
            p1_lastnames_tiny.append(lastname_tiny)
            p1_displaynames.append(displayname)

            displayname, lastname, lastname_tiny = extract_lastname_and_displayname(
                elem.find_element_by_xpath("div[3]").text)
            p2_lastnames.append(lastname)
            p2_lastnames_tiny.append(lastname_tiny)
            p2_displaynames.append(displayname)

            try:
                p1_s1_gms.append(int(elem.find_element_by_xpath("div[6]").text.split("\n")[0]))
                p2_s1_gms.append(int(elem.find_element_by_xpath("div[7]").text.split("\n")[0]))
            except NoSuchElementException:
                p1_s1_gms.append(np.nan)
                p2_s1_gms.append(np.nan)

            try:
                p1_s2_gms.append(int(elem.find_element_by_xpath("div[8]").text.split("\n")[0]))
                p2_s2_gms.append(int(elem.find_element_by_xpath("div[9]").text.split("\n")[0]))
            except NoSuchElementException:
                p1_s2_gms.append(np.nan)
                p2_s2_gms.append(np.nan)
                
            try:
                p1_s3_gms.append(int(elem.find_element_by_xpath("div[10]").text.split("\n")[0]))
                p2_s3_gms.append(int(elem.find_element_by_xpath("div[11]").text.split("\n")[0]))
            except NoSuchElementException:
                p1_s3_gms.append(np.nan)
                p2_s3_gms.append(np.nan)

    dic = {"match_id": match_ids, "datetime": datetimes, "round": match_rounds, "p1_lastname": p1_lastnames,
           "p1_lastname_tiny": p1_lastnames_tiny, "p1_displayname": p1_displaynames,
           "p2_lastname": p2_lastnames, "p2_lastname_tiny": p2_lastnames_tiny, "p2_displayname": p2_displaynames,
           "p1_s1_gms": p1_s1_gms, "p2_s1_gms": p2_s1_gms, "p1_s2_gms": p1_s2_gms, "p2_s2_gms": p2_s2_gms,
           "p1_s3_gms": p1_s3_gms, "p2_s3_gms": p2_s3_gms}
    matches_dataframe = pd.DataFrame(dic)

    matches_dataframe = matches_dataframe.astype({"p1_s1_gms": "Int16", "p2_s1_gms": "Int16", "p1_s2_gms": "Int16",
                                                  "p2_s2_gms": "Int16", "p1_s3_gms": "Int16", "p2_s3_gms": "Int16"})

    driver.quit()

    return matches_dataframe


def find_match_in_retrieved_matches(p1_lastname, p2_lastname, p1_displayname, p2_displayname, match_round, p1_s1_gms,
                                    p2_s1_gms, p1_s2_gms, p2_s2_gms, p1_s3_gms, p2_s3_gms, matches):
    result = matches[((matches["p1_displayname"] == p1_displayname) & (matches["p2_displayname"] == p2_displayname))
                     | ((matches["p1_displayname"] == p2_displayname) & (matches["p2_displayname"] == p1_displayname))]

    if len(result.index) != 1:
        result = matches[((matches["p1_lastname"] == p1_lastname) & (matches["p2_lastname"] == p2_lastname))
                         | ((matches["p1_lastname"] == p2_lastname) & (matches["p2_lastname"] == p1_lastname))]

    if len(result.index) > 1:
        result = matches[(matches["round"] == match_round) & (((matches["p1_lastname"] == p1_lastname) & (matches["p2_lastname"] == p2_lastname))
                         | ((matches["p1_lastname"] == p2_lastname) & (matches["p2_lastname"] == p1_lastname)))]

    if len(result.index) != 1:
        p1_lastname_tiny = re.split(r'[- ]', p1_lastname)[0]
        p2_lastname_tiny = re.split(r'[- ]', p2_lastname)[0]
        result = matches[
            ((matches["p1_lastname_tiny"] == p1_lastname_tiny) & (matches["p2_lastname_tiny"] == p2_lastname_tiny))
            | ((matches["p1_lastname_tiny"] == p2_lastname_tiny) & (matches["p2_lastname_tiny"] == p1_lastname_tiny))
            ]

    if len(result.index) != 1:
        result = matches[(matches["round"] == match_round)
                         & (((matches["p1_s1_gms"] == p1_s1_gms) & (matches["p2_s1_gms"] == p2_s1_gms)
                             & (matches["p1_s2_gms"] == p1_s2_gms) & (matches["p2_s2_gms"] == p2_s2_gms)
                             & ((pd.isna(matches["p1_s3_gms"]))
                                |
                                ((matches["p1_s3_gms"] == p1_s3_gms) & (matches["p2_s3_gms"] == p2_s3_gms))))
                            | ((matches["p1_s1_gms"] == p2_s1_gms) & (matches["p2_s1_gms"] == p1_s1_gms)
                               & (matches["p1_s2_gms"] == p2_s2_gms) & (matches["p2_s2_gms"] == p1_s2_gms)
                               & ((pd.isna(matches["p1_s3_gms"]))
                                  |
                                  ((matches["p1_s3_gms"] == p2_s3_gms) & (matches["p2_s3_gms"] == p1_s3_gms))))
                            )]

    return result


def find_match_datetime(match_id, tour_f_id, year, matches):
    """Find match datetime, given matches in the correct tournament and correct year"""
    retrieved_datetime = None

    result = matches[matches["match_id"] == match_id]

    if len(result.index) == 1:
        match_dt_str = result.iloc[0]["datetime"]
        match_dt_regex = re.search("^([0-9]+).([0-9]+). ([0-9]+):([0-9]+)", match_dt_str)
        if match_dt_regex:
            day = match_dt_regex.group(1)
            month = match_dt_regex.group(2)
            hour = match_dt_regex.group(3)
            minute = match_dt_regex.group(4)
            retrieved_datetime = datetime(year, int(month), int(day), int(hour), int(minute))
        else:
            print("Can't retrieve datetime from string '{0}' tournament '{1}' year '{2}'"
                  .format(match_dt_str, tour_f_id, year))

    return retrieved_datetime


def find_match_id(p1_lastname, p2_lastname, p1_displayname, p2_displayname, match_round, p1_s1_gms, p2_s1_gms,
                  p1_s2_gms, p2_s2_gms, p1_s3_gms, p2_s3_gms, matches, tour_f_id, year):
    match_id = None
    """Find match id, given matches in the correct tournament and correct year"""
    result = find_match_in_retrieved_matches(p1_lastname, p2_lastname, p1_displayname, p2_displayname, match_round,
                                             p1_s1_gms, p2_s1_gms, p1_s2_gms, p2_s2_gms, p1_s3_gms, p2_s3_gms, matches)

    if len(result.index) == 1:
        match_id = result.iloc[0]["match_id"]
    elif len(result.index) == 0:
        my_file = open('/home/davy/Documents/Log_scrap_datetime.txt', 'a')
        my_file.write("\n{0},{1},{2},{3}".format(tour_f_id, year, p1_lastname, p2_lastname))
        print("Match not found: tournament '{0}' year {1} '{2}' vs '{3} ".format(tour_f_id, year, p1_displayname,
                                                                                 p2_displayname))
    else:
        print("Several matches found: tournament '{0}' year {1} '{2}' vs '{3}".format(tour_f_id, year, p1_lastname,
                                                                                      p2_lastname))

    return match_id


def find_matches_datetimes(match_id, tour_f_id, year, tour_matches):
    key = (tour_f_id, year)

    matches = tour_matches[key]
    if matches is not None:
        return find_match_datetime(match_id, tour_f_id, year, matches)
    else:
        return None


def find_matches_ids(p1_lastname, p2_lastname, p1_displayname, p2_displayname, match_round, p1_s1_gms, p2_s1_gms,
                     p1_s2_gms, p2_s2_gms, p1_s3_gms, p2_s3_gms, tour_f_id, year, tour_matches):
    key = (tour_f_id, year)
    if key not in tour_matches:
        tour_matches[key] = find_matches_in_tournament(tour_f_id, year)

    matches = tour_matches[key]
    if matches is not None:
        return find_match_id(str.lower(p1_lastname), str.lower(p2_lastname), str.lower(p1_displayname),
                             str.lower(p2_displayname), match_round, p1_s1_gms, p2_s1_gms, p1_s2_gms,
                             p2_s2_gms, p1_s3_gms, p2_s3_gms, matches, tour_f_id, year)
    else:
        return None


def add_matches_datetime(dataset):
    tour_matches = {}

    dataset["match_id"] = dataset.apply(
        lambda match: find_matches_ids(match["p1_lastname"], match["p2_lastname"], match["p1_displayname"],
                                       match["p2_displayname"], match["round"], match["p1_s1_gms"], match["p2_s1_gms"],
                                       match["p1_s2_gms"], match["p2_s2_gms"], match["p1_s3_gms"], match["p2_s3_gms"],
                                       match["tournament_id"], match["year"], tour_matches)
        , axis=1)

    dataset["datetime"] = dataset.apply(
        lambda match: find_matches_datetimes(match["match_id"], match["tournament_id"],
                                             match["year"], tour_matches)
        , axis=1)

    dataset["datetime"] = dataset.apply(lambda row: row["datetime"].replace(tzinfo=timezone('Europe/Paris')), axis=1)


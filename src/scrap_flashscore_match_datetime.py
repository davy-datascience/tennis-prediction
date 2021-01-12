from selenium import webdriver
import pandas as pd
import re
import time
from datetime import datetime
from dateutil.tz import UTC
from selenium.common.exceptions import NoSuchElementException


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
        name_regex = re.search(r"^([^.]+) .+(\. )+\(", element.text)

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

    return matches_dataframe


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


def find_matches_datetimes(p1_lastname, p2_lastname, p1_displayname, p2_displayname, tour_f_id, year, datetime, tour_matches):
    if not pd.isna(datetime):
        return datetime

    key = (tour_f_id, year)
    if key not in tour_matches:
        tour_matches[key] = find_matches_in_tournament(tour_f_id, year)

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


def add_matches_datetime(dataset):
    dataset["tour_date"] = dataset.apply(lambda row: get_tour_date(str(row["tourney_date"])), axis=1)

    '''dataset_full["year"] = dataset_full.apply(lambda row: correct_wrong_year(
        row["tournament_flashscore_id"], row["year"]), axis=1)'''

    start_time = time.time()

    tour_matches = {}

    dataset["datetime"] = dataset.apply(
        lambda match: find_matches_datetimes(match["p1_lastname"], match["p2_lastname"], match["p1_displayname"],
                                             match["p2_displayname"], match["tournament_id"],
                                             match["year"], match["datetime"], tour_matches)
        , axis=1)
    # TODO remove match["datetime"]

    print("--- %s seconds ---" % (time.time() - start_time))

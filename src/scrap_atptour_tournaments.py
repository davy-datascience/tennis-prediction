import time
from selenium import webdriver
import pandas as pd
import re
import pymongo
import configparser
from selenium.common.exceptions import NoSuchElementException
from src.Classes.tournament import *

config = configparser.ConfigParser()
config.read("src/config.ini")
MONGO_CLIENT = config['mongo']['client']


def scrap_tournaments_by_year(year):
    driver = webdriver.Chrome('/home/davy/Drivers/chromedriver')
    match_url = 'https://www.atptour.com/en/scores/results-archive?year={}'.format(year)
    driver.get(match_url)
    time.sleep(1)  # Wait 1 sec to avoid IP being banned for scrapping

    levels = []
    elements = driver.find_elements_by_xpath("//tr[@class='tourney-result']/td[2]/img")
    for element in elements:
        img_src = element.get_attribute("src")
        level = re.search(r"categorystamps_(.+)\.", img_src)
        if level is None:
            print("tournament level not found from {0}".format(img_src))
        else:
            levels.append(level.group(1))

    names = []
    elements = driver.find_elements_by_xpath("//tr[@class='tourney-result']/td[3]/span[1]")
    for element in elements:
        names.append(element.text)

    cities = []
    countries = []
    elements = driver.find_elements_by_xpath("//tr[@class='tourney-result']/td[3]/span[2]")
    for element in elements:
        location_regex = re.search("(.+), (.+)", element.text)
        cities.append(location_regex.group(1))
        countries.append(location_regex.group(2))

    number_of_competitors = []
    elements = driver.find_elements_by_xpath("//tr[@class='tourney-result']/td[4]/div/div/a[1]")
    for element in elements:
        number_of_competitors.append(int(element.text))

    surfaces = []
    elements = driver.find_elements_by_xpath("//tr[@class='tourney-result']/td[5]/div/div")
    for element in elements:
        surfaces.append(element.text)

    ids = []
    formatted_names = []  # name need to access tournament info link on atptour
    elements = driver.find_elements_by_xpath("//tr[@class='tourney-result']/td[8]/a")
    for element in elements:
        href = element.get_attribute("href")
        link_info = re.search("/(.+)/([0-9]+)/[0-9]+/results$", href)
        if link_info is None:
            print("tournament id not found from {0}".format(href))
        else:
            formatted_names.append(link_info.group(1))
            ids.append(int(link_info.group(2)))

    driver.quit()

    tournaments = pd.concat(
        [pd.Series(ids), pd.Series(names), pd.Series(formatted_names), pd.Series(cities), pd.Series(countries),
         pd.Series(levels), pd.Series(number_of_competitors),
         pd.Series(surfaces)], axis=1)
    tournaments.columns = ["id", "name", "formatted_name", "city", "country", "level", "number_of_competitors",
                           "surface"]

    return tournaments


def record_tournaments_by_year(year):
    tournaments = scrap_tournaments_by_year(year)

    records = json.loads(tournaments.T.to_json()).values()

    myclient = pymongo.MongoClient(MONGO_CLIENT)
    mydb = myclient["tennis"]
    mycol = mydb["tournaments"]
    mycol.insert_many(records)


def scrap_tournament_id(name, year, tournaments, new_tournaments_to_scrap):
    driver = webdriver.Chrome('/home/davy/Drivers/chromedriver')
    url = 'https://www.atptour.com/-/ajax/Scores/GetTournamentArchiveForYear/{}'.format(year)
    driver.get(url)
    time.sleep(1)
    tournaments_scrapped = None
    try:
        content = driver.find_element_by_xpath("//pre").text
        tournaments_scrapped = json.loads(content)
    except NoSuchElementException:
        print("Couldn't scrap tournaments for year {}".format(year))

    if tournaments_scrapped is None:
        url = 'https://www.atptour.com/-/ajax/Scores/GetTournamentArchiveForYear/{}'.format(int(year) - 1)
        driver.get(url)
        time.sleep(1)
        try:
            content = driver.find_element_by_xpath("//pre").text
            tournaments_scrapped = json.loads(content)
        except NoSuchElementException:
            print("Couldn't scrap tournaments for year {}".format(int(year) - 1))

    driver.quit()

    tourn_id = None
    if tournaments_scrapped is not None:
        for tournament in tournaments_scrapped:
            if tournament["Key"] == name:
                tourn_id = int(tournament["Value"])
                tourn_formatted_name = tournament["DataAttributes"]["descriptor"]
                new_tournaments_to_scrap.append([tourn_id, tourn_formatted_name, year])
                break

    if tourn_id is None:
        tourn_id = -1

    tournaments[name] = tourn_id

    return tourn_id


def match_tournament(name, year, tournaments, new_tournaments_to_scrap):
    if name.startswith("Davis Cup"):
        name = "Davis Cup"
    if name not in tournaments:
        tourn_id = scrap_tournament_id(name, year, tournaments, new_tournaments_to_scrap)
        return tourn_id
    else:
        return tournaments[name]


def get_tournaments_ids(dataset):
    start_time = time.time()
    
    tournaments = {}
    new_tournaments_to_scrap = []

    '''myclient = pymongo.MongoClient(MONGO_CLIENT)
    mydb = myclient["tennis"]
    mycol = mydb["tournaments"]
    tours = mycol.find({})
    for tour in tours:
        tournaments[tour["name"]] = [tour["id"], tour["formatted_name"]]'''

    tournaments_ids = [match_tournament(row[0], str(row[1])[:4], tournaments, new_tournaments_to_scrap) for row in
                       dataset.reindex(index=dataset.index[::-1]).to_numpy()]

    print("---getTournamentsIds  %s seconds ---" % (time.time() - start_time))
    return tournaments_ids[::-1], new_tournaments_to_scrap


def retrieve_missing_tournament_id(tournament_name, atptour_id, tournament_ids):
    if atptour_id == -1:
        if tournament_name.startswith("Davis Cup"):
            tournament_name = "Davis Cup"
        new_id = None
        try:
            new_id = tournament_ids.loc[tournament_name][0]
        except KeyError:
            print("Couldn't find tournament '{}'".format(tournament_name))
        return new_id
    else:
        return atptour_id


def retrieve_missing_tournament_ids(dataset):
    tournament_ids_manual_collect = pd.read_csv("datasets/tournament_ids_matching_manual_collect.csv",
                                                index_col="name")

    tournament_ids_dataframe = dataset.apply(lambda row: retrieve_missing_tournament_id(row["tourney_name"],
                                                                                        row["tournament_id"],
                                                                                        tournament_ids_manual_collect),
                                             axis=1)

    return tournament_ids_dataframe, tournament_ids_manual_collect.values.tolist()


def scrap_tournament(tournament_id, tournament_formatted_name, year):
    driver = webdriver.Chrome('/home/davy/Drivers/chromedriver')
    match_url = 'https://www.atptour.com/en/tournaments/{0}/{1}/overview'.format(tournament_formatted_name,
                                                                                 tournament_id)
    driver.get(match_url)
    time.sleep(1)  # Wait 1 sec to avoid IP being banned for scrapping

    tournament = None
    try:
        name = driver.find_element_by_xpath("//div[@class='player-profile-hero-name']/div[1]").text
        if name == "":
            name = tournament_formatted_name

        location = driver.find_element_by_xpath("//div[@class='player-profile-hero-dash']/div/div[2]").text
        matched_location = location.split(", ")
        city = matched_location[0]
        country = matched_location[-1]

        img = driver.find_element_by_xpath("//div[@class='tournmanet-logo']/img")
        img_src = img.get_attribute("src")
        level_matched = re.search("categorystamps_(.+)_", img_src)
        level = level_matched.group(1) if level_matched else None

        number_of_competitors = None
        try:
            number_of_competitors = int(driver.find_element_by_xpath("//div[@class='bracket-sgl']/div[2]").text)
        except ValueError:
            pass

        surface = driver.find_element_by_xpath("//div[@class='surface-bottom']/div[2]").text

        tournament = Tournament(tournament_id, name, tournament_formatted_name, city, country, surface,
                                number_of_competitors, level)
    except NoSuchElementException:
        match_url = 'https://www.atptour.com/en/scores/archive/{0}/{1}/{2}/results'.format(tournament_formatted_name,
                                                                                           tournament_id, year)
        driver.get(match_url)
        time.sleep(1)  # Wait 1 sec to avoid IP being banned for scrapping
        try:
            name = driver.find_element_by_xpath("//tr[@class='tourney-result with-icons']/td[2]/a").text

            location = driver.find_element_by_xpath("//tr[@class='tourney-result with-icons']/td[2]/span[1]").text
            matched_location = location.split(", ")
            city = matched_location[0] if len(matched_location) > 0 else None
            country = matched_location[-1] if len(matched_location) > 1 else None

            level = None
            try:
                img = driver.find_element_by_xpath("//tr[@class='tourney-result with-icons']/td[1]/img")
                img_src = img.get_attribute("src")
                level = re.search(r"categorystamps_(.+)\.", img_src).group(1)
            except NoSuchElementException:
                pass

            number_of_competitors = int(driver.find_element_by_xpath(
                "//td[@class='tourney-details-table-wrapper']/table/tbody/tr/td[1]/div[2]/div/a[1]/span").text)

            surface = driver.find_element_by_xpath(
                "//td[@class='tourney-details-table-wrapper']/table/tbody/tr/td[2]/div[2]/div/span").text

            tournament = Tournament(tournament_id, name, tournament_formatted_name, city, country, surface,
                                    number_of_competitors, level)

        except NoSuchElementException:
            print("Couldn't find tournament '{0}' with id {1} in {2}".format(tournament_formatted_name, tournament_id,
                                                                             year))

    driver.quit()

    return tournament


def scrap_tournaments(tournaments_info):
    tournaments = []
    for tournament_info in tournaments_info:
        tournament = scrap_tournament(tournament_info[0], tournament_info[1],
                                      tournament_info[2] if len(tournament_info) > 2 else None)
        if tournament is not None:
            tournaments.append(tournament)

    return tournaments


def record_tournaments(tournaments):
    tournaments_json = get_tournaments_json(tournaments)
    myclient = pymongo.MongoClient(MONGO_CLIENT)
    mydb = myclient["tennis"]
    mycol = mydb["tournaments"]
    result = mycol.insert_many(tournaments_json)
    return result.acknowledged

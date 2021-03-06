import json
import time
import pandas as pd
from selenium.common.exceptions import NoSuchElementException
from datetime import datetime
import random

from src.utils import get_chrome_driver


def get_tournaments_by_year(year_from, year_to):
    tournaments_by_year = {}
    tour_ids = []
    tour_names = []
    tour_formatted_names = []
    tour_years = []
    for year in range(year_from, year_to + 1):
        url = 'https://www.atptour.com/-/ajax/Scores/GetTournamentArchiveForYear/{}'.format(year)
        driver = get_chrome_driver()
        driver.get(url)
        time.sleep(random.uniform(2, 5))
        tournaments_scrapped = None
        try:
            content = driver.find_element_by_xpath("//pre").text
            tournaments_scrapped = json.loads(content)
        except NoSuchElementException:
            print("Couldn't scrap tournaments for year {}".format(year))

        if tournaments_scrapped is not None:
            tournaments_by_year[year] = {tournament["Key"]: {"id": int(tournament["Value"]),
                                                             "formatted_name": tournament["DataAttributes"][
                                                                 "descriptor"]}
                                         for tournament in tournaments_scrapped}

            for tournament in tournaments_scrapped:
                tour_ids.append(int(tournament["Value"]))
                tour_names.append(tournament["Key"])
                tour_formatted_names.append(tournament["DataAttributes"]["descriptor"])
                tour_years.append(year)
        driver.quit()
    # return tournaments_by_year
    return pd.DataFrame({"name": tour_names, "formatted_name": tour_formatted_names, "atp_id": tour_ids,
                         "year": tour_years})


def get_tournaments_ids(dataset):
    tournaments_by_year = get_tournaments_by_year(1990, datetime.today().year)

    tour_distinct_names = dataset[["tourney_name", "year"]].drop_duplicates(subset=["tourney_name"], keep="last")

    tour_distinct_names["atp_formatted_name"] = tour_distinct_names.apply(
        lambda row: tournaments_by_year[tournaments_by_year["name"] == row["tourney_name"]]["formatted_name"].iloc[0]
        if len(tournaments_by_year[tournaments_by_year["name"] == row["tourney_name"]].index) > 0 else None, axis=1)

    tour_distinct_names["atp_id"] = tour_distinct_names.apply(
        lambda row: tournaments_by_year[tournaments_by_year["name"] == row["tourney_name"]]["atp_id"].iloc[0]
        if len(tournaments_by_year[tournaments_by_year["name"] == row["tourney_name"]].index) > 0 else -1, axis=1)

    '''tour_not_found = tour_distinct_names[tour_distinct_names.apply(
        lambda row: len(tournaments_by_year[tournaments_by_year["name"] == row["tourney_name"]].index) == 0, axis=1)]'''

    tourn_manual = pd.read_csv("datasets/tournaments_manual_collect.csv")

    #tour_distinct_names['atp_formatted_name2'] = tour_distinct_names.apply(lambda row: retrieve_missing_tournaments(row["tourney_name"], row["atp_formatted_name"], row["atp_id"], tourn_manual), axis=1)


    tour_distinct_names['atp_formatted_name'] = tour_distinct_names.apply(
        lambda row: tourn_manual[tourn_manual["name"] == row["tourney_name"]]["formatted_name"].iloc[0]
        if row["atp_id"] == -1 else row["atp_formatted_name"], axis=1)

    tour_distinct_names["atp_id"] = tour_distinct_names.apply(
        lambda row: tourn_manual[tourn_manual["name"] == row["tourney_name"]]["id"].iloc[0]
        if row["atp_id"] == -1 else row["atp_id"], axis=1)

    return tour_distinct_names


def correct_names(name):
    if name == "St Petersburg":
        return "St. Petersburg"
    elif name == "Us Open":
        return "US Open"
    elif name == "Rio De Janeiro":
        return "Rio de Janeiro"
    elif name == "Stuttgart Outdoor":
        return "Stuttgart"
    elif name == "Stuttgart Masters":
        return "Stuttgart Indoor"
    elif name == "Hamburg Masters":
        return "Hamburg"
    elif name == "Stockholm Masters":
        return "Stockholm"
    elif name == "Tokyo Indoor":
        return "Tokyo"
    elif name == "Tokyo Outdoor":
        return "Tokyo"
    elif name == "Sydney Indoor":
        return "Sydney"
    elif name == "Sydney Outdoor":
        return "Sydney"

    else:
        return name


def find_atp_tournaments(dataset):
    dataset["tourney_name"] = dataset.apply(lambda row: correct_names(row["tourney_name"]), axis=1)
    dataset["year"] = dataset.apply(lambda row: int(row["tourney_id"][:4]), axis=1)
    tournaments = get_tournaments_ids(dataset)
    return tournaments


def scrap_tournament(tournament):
    tournament_id = tournament["atp_id"]
    tournament_formatted_name = tournament["atp_formatted_name"]
    year = tournament["year"]
    url = None

    driver = get_chrome_driver()
    driver.maximize_window()
    match_url = 'https://www.atptour.com/en/tournaments/{0}/{1}/overview'.format(tournament_formatted_name,
                                                                                 tournament_id) if url is None else url
    driver.get(match_url)
    time.sleep(1)  # Wait 1 sec to avoid IP being banned for scrapping

    try:
        location = driver.find_element_by_xpath("//div[@class='player-profile-hero-dash']/div/div[2]").text
        matched_location = location.split(", ")
        tournament["city"] = matched_location[0]
        tournament["country"] = matched_location[-1]

        try:
            number_of_competitors = int(driver.find_element_by_xpath("//div[@class='bracket-sgl']/div[2]").text)
            tournament["number_of_competitors"] = number_of_competitors
        except ValueError:
            pass

        tournament["surface"] = driver.find_element_by_xpath("//div[@class='surface-bottom']/div[2]").text

        tournament["year"] = datetime.now().year

    except NoSuchElementException:
        match_url = 'https://www.atptour.com/en/scores/archive/{0}/{1}/{2}/results' \
            .format(tournament_formatted_name, tournament_id, year) if url is None else url
        driver.quit()
        driver = get_chrome_driver()
        driver.maximize_window()
        driver.get(match_url)
        time.sleep(1)  # Wait 1 sec to avoid IP being banned for scrapping
        try:
            location = driver.find_element_by_xpath("//tr[@class='tourney-result with-icons']/td[2]/span[1]").text
            matched_location = location.split(", ")
            city = matched_location[0] if len(matched_location) > 0 else None
            country = matched_location[-1] if len(matched_location) > 1 else None

            number_of_competitors = int(driver.find_element_by_xpath(
                "//td[@class='tourney-details-table-wrapper']/table/tbody/tr/td[1]/div[2]/div/a[1]/span").text)

            surface = driver.find_element_by_xpath(
                "//td[@class='tourney-details-table-wrapper']/table/tbody/tr/td[2]/div[2]/div/span").text

            tournament["city"] = city
            tournament["country"] = country
            tournament["surface"] = surface
            tournament["number_of_competitors"] = number_of_competitors

        except NoSuchElementException:
            pass

    driver.quit()

    return tournament


def scrap_atp_tournaments(tournaments):
    tournaments = tournaments.apply(scrap_tournament, axis=1)

    return tournaments


def clean_tournaments(tournaments):
    tournaments["country"] = tournaments.apply(lambda tour: "U.S.A." if tour["country"] == "U.S.A" else tour["country"],
                                               axis=1)

    tournaments["city"] = tournaments.apply(
        lambda tour: "Johannesburg" if tour["flash_id"] == "johannesburg" else tour["city"], axis=1)
    tournaments["country"] = tournaments.apply(
        lambda tour: "South Africa" if tour["flash_id"] == "johannesburg" else tour["country"], axis=1)

    tournaments["city"] = tournaments.apply(lambda tour: "Nice" if tour["flash_id"] == "nice" else tour["city"], axis=1)
    tournaments["country"] = tournaments.apply(lambda tour: "France" if tour["flash_id"] == "nice" else tour["country"],
                                               axis=1)

    tournaments["city"] = tournaments.apply(
        lambda tour: "St. Poelten" if tour["flash_id"] == "poertschach" else tour["city"], axis=1)
    tournaments["country"] = tournaments.apply(
        lambda tour: "Austria" if tour["flash_id"] == "poertschach" else tour["country"], axis=1)

    tournaments["city"] = tournaments.apply(lambda tour: "Memphis" if tour["flash_id"] == "memphis" else tour["city"],
                                            axis=1)
    tournaments["country"] = tournaments.apply(
        lambda tour: "U.S.A." if tour["flash_id"] == "memphis" else tour["country"], axis=1)

    '''tour = tournaments[tournaments["flash_id"] == "shanghai"].iloc[-1]
    tour["flash_id"] = "shanghai-2"
    tournaments = pd.concat([tournaments, pd.DataFrame(tour).T])

    tournaments.drop_duplicates(subset=["flash_id"], keep="last", inplace=True)'''

    return tournaments

import time
import locale
import pandas as pd
import re
from datetime import datetime, timedelta

from log import log
from queries.tournament_queries import find_tournament_by_id, q_update_tournament, q_create_tournament
from utils import get_chrome_driver, get_dataframe_json


def search_all_tournaments_atptour():
    tournaments_atptour = None
    driver = get_chrome_driver()
    driver.get("https://www.atptour.com/en/tournaments")
    time.sleep(3)
    try:
        atp_names = []
        atp_formatted_names = []
        atp_ids = []
        elements = driver.find_elements_by_xpath("//tr[@class='tourney-result']/td[2]/a")

        for elem in elements:
            try:
                url = elem.get_attribute("href")
                url_regex = re.search("/tournaments/(.*)/(.*)/overview$", url)
                atp_formatted_name = url_regex.group(1)
                atp_id = int(url_regex.group(2))
                atp_name = elem.text

                atp_formatted_names.append(atp_formatted_name)
                atp_ids.append(atp_id)
                atp_names.append(atp_name)
            except Exception as ex:
                atp_formatted_names.append(None)
                atp_ids.append(None)
                atp_names.append(None)
                print(type(ex).__name__)
                print("atp tournaments retrieval error, tournament '{0}'".format(elem.text))

        cities = []
        countries = []
        elements = driver.find_elements_by_xpath("//tr[@class='tourney-result']/td[2]/span[1]")

        for elem in elements:
            location = elem.text
            try:
                matched_location = location.split(", ")
                city = matched_location[0]
                country = matched_location[-1]

                cities.append(city)
                countries.append(country)
            except Exception as ex:
                cities.append(None)
                countries.append(None)
                print(type(ex).__name__)
                print("atp tournaments retrieval error, location '{0}'".format(location))

        start_dates = []
        end_dates = []
        elements = driver.find_elements_by_xpath("//tr[@class='tourney-result']/td[2]/span[2]")

        for elem in elements:
            date_elem = elem.text
            try:
                date_regex = re.search("^(.*) - (.*)$", date_elem)
                start_date_str = date_regex.group(1)
                start_date = datetime.strptime(start_date_str, '%Y.%m.%d')

                end_date_str = date_regex.group(2)
                end_date = datetime.strptime(end_date_str, '%Y.%m.%d')
                end_date += timedelta(days=1)

                start_dates.append(start_date)
                end_dates.append(end_date)
            except Exception as ex:
                start_dates.append(None)
                end_dates.append(None)
                #print(type(ex).__name__)
                #print("atp tournaments retrieval error, date_elem: '{0}'".format(date_elem))

        tournaments_atptour = pd.DataFrame({"atp_id": atp_ids, "atp_name": atp_names,
                                            "atp_formatted_name": atp_formatted_names, "city": cities,
                                            "country": countries, "start_date": start_dates, "end_date": end_dates})

    except Exception as ex:
        log("tournaments", "Tournament header retrieval error")
        print(ex)
        print(type(ex).__name__)

    driver.quit()
    return tournaments_atptour


def get_tournament_name(flash_name):
    """ Get tournament name from flashscore tournament name. Some tournaments name are between brackets
    ex: 'Melbourne (Great Ocean Road Open)' -> 'Great Ocean Road Open' """

    name_regex = re.search(r"\((.*)\)", flash_name)
    if name_regex:
        return name_regex.group(1)
    else:
        return flash_name


def search_tournament_atptour(tournament, date_of_matches):
    flash_id = tournament["flash_id"]

    tournaments_atptour = search_all_tournaments_atptour()

    # Tournament already exists - Checking if it has kept same references on atptour
    if "atp_id" in tournament.index and "atp_formatted_name" in tournament.index:
        atp_id = tournament["atp_id"]
        atp_formatted_name = tournament["atp_formatted_name"]
        tour_matched = tournaments_atptour[(tournaments_atptour["atp_id"] == atp_id) & (
                tournaments_atptour["atp_formatted_name"] == atp_formatted_name)]

        # Tournament has kept same references
        if len(tour_matched.index) == 1:
            return tournament

        # Tournament has new references (changed atp_id)
        tour_matched = tournaments_atptour[tournaments_atptour["atp_formatted_name"] == atp_formatted_name]
        if len(tour_matched.index) == 1:
            # New tournament kept same formatted_name but new atp_id
            new_atp_id = tour_matched.iloc[0]["atp_id"]
            log("tournament_updated", "Tournament '{0}' changed atp_id from '{1}' to '{2}'"
                .format(flash_id, atp_id, new_atp_id))
            tournament["atp_id"] = new_atp_id
            return tournament

        # Tournament has new references (changed atp_id and atp_formatted_name)
        tournament_name = get_tournament_name(tournament["flash_name"])
        tour_matched = tournaments_atptour[tournaments_atptour["atp_name"] == tournament_name]
        if len(tour_matched.index) == 1:
            # New tournament kept same formatted_name but new atp_id
            new_atp_id = tour_matched.iloc[0]["atp_id"]
            new_formatted_name = tour_matched.iloc[0]["atp_formatted_name"]
            log("tournament_updated", "Tournament '{0}' changed atp_id from '{1}' to '{2}'"
                .format(flash_id, atp_id, new_atp_id))
            log("tournament_updated", "Tournament '{0}' changed atp_formatted_name from '{1}' to '{2}'"
                .format(flash_id, atp_formatted_name, new_formatted_name))
            tournament["atp_id"] = new_atp_id
            tournament["atp_formatted_name"] = new_formatted_name
            return tournament

        # Tournament new references not found
        else:
            log("tournament_not_found", "Tournament '{0}' not found, atp_id: '{1}' and atp_formatted_name: '{2}'"
                .format(flash_id, atp_id, atp_formatted_name))
            return None

    # New tournament
    else:
        tournament_name = get_tournament_name(tournament["flash_name"])
        country = tournament["country"]

        tour_matched = tournaments_atptour[tournaments_atptour["atp_name"] == tournament_name]

        if len(tour_matched.index) != 1:
            # Tournament not found by name. Try to find tournament by start date, end date and country
            tour_matched = tournaments_atptour[(tournaments_atptour["start_date"] <= pd.Timestamp(date_of_matches))
                                               & (tournaments_atptour["end_date"] >= pd.Timestamp(date_of_matches))
                                               & (tournaments_atptour["country"] == country)
                                               ]

        # New tournament references found
        if len(tour_matched.index) == 1:
            tournament["atp_id"] = tour_matched.iloc[0]["atp_id"]
            tournament["atp_formatted_name"] = tour_matched.iloc[0]["atp_formatted_name"]

            '''log("tournament_created", "Tournament '{0}' created"
                .format(flash_id))'''
            return tournament

        # New tournament references not found
        else:
            log("tournament_not_found", "Tournament '{0}' not found"
                .format(flash_id))
            return None


def scrap_tournament(tournament, date):
    tournament = search_tournament_atptour(tournament, date)
    if tournament is None:
        return None

    tournament_id = tournament["atp_id"]
    tournament_formatted_name = tournament["atp_formatted_name"]

    url = None

    driver = get_chrome_driver()
    driver.maximize_window()
    match_url = 'https://www.atptour.com/en/tournaments/{0}/{1}/overview'.format(tournament_formatted_name,
                                                                                 tournament_id) if url is None else url
    driver.get(match_url)
    time.sleep(1)  # Wait 1 sec to avoid IP being banned for scrapping

    try:
        name = driver.find_element_by_xpath("//div[@class='player-profile-hero-name']/div[1]").text
        if name == "":
            name = tournament_formatted_name
        tournament["tourney_name"] = name

        location = driver.find_element_by_xpath("//div[@class='player-profile-hero-dash']/div/div[2]").text
        matched_location = location.split(", ")
        tournament["city"] = matched_location[0]
        tournament["country"] = matched_location[-1]

        date_elem = driver.find_element_by_xpath("//div[@class='player-profile-hero-dash']/div/div[3]").text
        date_regex = re.search("^(.*) - .* (.*)$", date_elem)
        try:
            locale.setlocale(locale.LC_ALL, 'en_US.utf8')
            full_date = "{0} {1}".format(date_regex.group(1), date_regex.group(2))
            tournament["start_date"] = pd.to_datetime(full_date, format='%B %d %Y', utc=True)
        except Exception as ex:
            print(ex)
            pass

        if "tourney_level" not in tournament.index:
            # Find tourney level from image
            img = driver.find_element_by_xpath("//div[@class='tournmanet-logo']/img")
            img_src = img.get_attribute("src")
            level_matched = re.search("categorystamps_(.+)_", img_src)
            level = level_matched.group(1) if level_matched else None
            tournament["tourney_level"] = "M" if level == "1000" else "A"

        # maximum number of sets
        if "best_of" not in tournament.index:
            tournament["best_of"] = 3

        try:
            number_of_competitors = int(driver.find_element_by_xpath("//div[@class='bracket-sgl']/div[2]").text)
            tournament["number_of_competitors"] = number_of_competitors
        except ValueError:
            pass

        tournament["surface"] = driver.find_element_by_xpath("//div[@class='surface-bottom']/div[2]").text

    except Exception:
        pass

    driver.quit()

    return tournament


def update_tournament(tournament):
    try:
        tournaments_json = get_dataframe_json(pd.DataFrame(tournament).T)
        q_update_tournament(tournaments_json[0])

        print("tournament '{0}' has been updated".format(tournament["_id"]))
    except Exception as ex:
        log("tournament_update", "tournament '{0}' couldn't be updated".format(tournament["flash_id"])
            , type(ex).__name__)


def get_tournament(tournament_id, tournaments):
    tournament = tournaments[tournaments["flash_id"] == tournament_id]
    return tournament.iloc[0] if len(tournament) > 0 else None


def add_tournament_info(match):
    """Add tournament attributes to a match series"""
    tour = find_tournament_by_id(match["tournament_id"])

    if tour is None:
        print("Couldn't find tournament '{0}' match '{1}'".format(match["tournament_id"], match["match_id"]))
        return

    match["surface"] = tour["surface"]
    match["tour_date"] = tour["start_date"]
    match["draw_size"] = tour["number_of_competitors"]
    match["tourney_level"] = tour["tourney_level"]
    match["best_of"] = tour["best_of"]
    match["country"] = tour["country"]


def create_tournament(tournament):
    result = q_create_tournament(tournament.to_dict())
    if result is None:
        log("create_tournament", "couldn't create tournament '{0}'".format(tournament["flash_id"]))
    else:
        print("tournament '{0}' has been created".format(tournament["flash_id"]))

import time
import locale
from selenium import webdriver
import pandas as pd
import re
from datetime import datetime, timedelta

from src.log import log
from src.utils import get_chrome_driver


def search_all_tournaments_atptour():
    tournaments_atptour = None
    driver = get_chrome_driver()
    driver.get("https://www.atptour.com/en/tournaments")
    time.sleep(1)  # Wait 1 sec to avoid IP being banned for scrapping
    try:
        atp_formatted_names = []
        atp_ids = []
        elements = driver.find_elements_by_xpath("//tr[@class='tourney-result']/td[2]/a")

        for elem in elements:
            url = elem.get_attribute("href")
            url_regex = re.search("/tournaments/(.*)/(.*)/overview$", url)
            atp_formatted_names.append(url_regex.group(1))
            atp_ids.append(int(url_regex.group(2)))

        cities = []
        countries = []
        elements = driver.find_elements_by_xpath("//tr[@class='tourney-result']/td[2]/span[1]")

        for elem in elements:
            location = elem.text
            matched_location = location.split(", ")
            cities.append(matched_location[0])
            countries.append(matched_location[-1])

        start_dates = []
        end_dates = []
        elements = driver.find_elements_by_xpath("//tr[@class='tourney-result']/td[2]/span[2]")

        for elem in elements:
            date_elem = elem.text
            date_regex = re.search("^(.*) - (.*)$", date_elem)
            start_date = date_regex.group(1)
            start_dates.append(datetime.strptime(start_date, '%Y.%m.%d'))
            end_date_str = date_regex.group(2)
            end_date = datetime.strptime(end_date_str, '%Y.%m.%d')
            end_date += timedelta(days=1)
            end_dates.append(end_date)


        tournaments_atptour = pd.DataFrame({"atp_id": atp_ids, "atp_formatted_name": atp_formatted_names,
                                            "city": cities, "country": countries,
                                            "start_date": start_dates, "end_date": end_dates})

    except Exception as ex:
        log("tournaments", "Tournament header retrieval error")
        print("Tournament header retrieval error")
        print(ex)

    driver.quit()
    return tournaments_atptour


def search_tournament_atptour(tournament, date):
    flash_id = tournament["flash_id"]

    tournaments_atptour = search_all_tournaments_atptour()

    # Tournament already exists - Checking if it has kept same references on atptour
    if "atp_id" in tournament.index and "atp_formatted_name" in tournament.index:
        atp_id = tournament["atp_id"]
        atp_formatted_name = tournament["atp_formatted_name"]
        tour_matched = tournaments_atptour[(tournaments_atptour["atp_id"] == atp_id)&(tournaments_atptour["atp_formatted_name"] == atp_formatted_name)]

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
        tour_matched = tournaments_atptour[tournaments_atptour["city"] == tournament["flash_name"]]
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
        name = tournament["flash_name"]
        country = tournament["country"]

        tour_matched = tournaments_atptour[(tournaments_atptour["start_date"] <= date)
                                           &(tournaments_atptour["end_date"] >= date)
                                           &((tournaments_atptour["city"] == name)
                                             | tournaments_atptour["country"] == country)]

        # New tournament references found
        if len(tour_matched.index) == 1:
            new_atp_id = tour_matched.iloc[0]["atp_id"]
            new_formatted_name = tour_matched.iloc[0]["atp_formatted_name"]

            log("tournament_created", "Tournament '{0}' created"
                .format(flash_id))

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


def update_tournaments(tournaments, tournament):
    '''Update tournaments dataframe with updated tournament series'''
    indexes = tournaments.index[tournaments["flash_id"] == tournament["flash_id"]].tolist()
    if len(indexes) > 0:
        index = indexes[0]
        for elem in tournaments.columns:
            tournaments.at[index, elem] = tournament[elem]

    else:
        # Create tournament
        pass


def get_tournament(tournament_id, tournaments):
    tournament = tournaments[tournaments["flash_id"] == tournament_id]
    return tournament.iloc[0] if len(tournament) > 0 else None


def add_tournament_info(match, tournaments):
    """Add tournament attributes to a match series"""
    tour = get_tournament(match["tournament_id"], tournaments)

    match["surface"] = tour["surface"]
    match["tour_date"] = tour["start_date"]
    match["draw_size"] = tour["number_of_competitors"]
    match["tourney_level"] = tour["tourney_level"]
    match["best_of"] = tour["best_of"]
    match["country"] = tour["country"]


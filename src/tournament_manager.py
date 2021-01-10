import time
from selenium import webdriver
import pandas as pd
import re
from datetime import datetime


def search_all_tournaments_atptour():
    driver = webdriver.Chrome('/home/davy/Drivers/chromedriver')
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
            atp_ids.append(url_regex.group(2))

        cities = []
        elements = driver.find_elements_by_xpath("//tr[@class='tourney-result']/td[2]/span[1]")

        for elem in elements:
            location = elem.text
            matched_location = location.split(", ")
            cities.append(matched_location[0])

        tournaments_atptour = pd.DataFrame({"atp_id": atp_ids, "atp_formatted_name": atp_formatted_names, "city": cities})
        return tournaments_atptour

    except Exception as ex:
        print("Tournament header retrieval error")
        print(ex)
        return None


def search_tournament_atptour(tournament):
    tournaments_atptour = search_all_tournaments_atptour()


def scrap_tournament(tournament):
    tournament_id = tournament["atp_id"]
    tournament_formatted_name = tournament["atp_formatted_name"]
    year = tournament["year"]
    url = None

    driver = webdriver.Chrome('/home/davy/Drivers/chromedriver')
    driver.maximize_window()
    match_url = 'https://www.atptour.com/en/tournaments/{0}/{1}/overview'.format(tournament_formatted_name,
                                                                                 tournament_id) if url is None else url
    print(match_url)
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
            full_date = "{0} {1}".format(date_regex.group(1), date_regex.group(2))
            tournament["date"] = datetime.strptime(full_date, '%B %d %Y')
        except Exception:
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

        tournament["year"] = datetime.now().year

    except Exception:
        pass

    driver.quit()

    return tournament
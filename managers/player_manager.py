import time
import re
import pandas as pd

from datetime import datetime
from selenium.common.exceptions import NoSuchElementException

from log import log
from managers.player_rank_manager import retrieve_player_rank_info
from queries.country_queries import country_exists, find_country_with_flag_code
from queries.player_queries import find_player_by_id, q_create_player, q_update_player
from utils import get_chrome_driver


def scrap_player_id(player_name):
    atptour_name = atptour_id = None
    driver = get_chrome_driver()
    match_url = 'https://www.atptour.com/en/search-results/players?searchTerm={}'.format(player_name)
    driver.get(match_url)
    time.sleep(1)

    elements = driver.find_elements_by_xpath("//table[@class='player-results-table']/tbody/tr/td[4]/a")
    player_element = None

    if len(elements) == 0:
        log("player_not_found", "'{0}' not found on atptour website".format(player_name))
    else:
        for element in elements:
            if str.lower(element.text) == str.lower(player_name):
                player_element = element
                break

        if player_element is None:
            player_element = elements[0]

        atptour_name = player_element.text
        href = player_element.get_attribute("href")
        href_regex = re.search(".+/(.*)/overview$", href)
        atptour_id = href_regex.group(1)

    driver.quit()

    return atptour_name, atptour_id


def scrap_player(atp_id):
    driver = get_chrome_driver()
    match_url = 'https://www.atptour.com/en/players/player/{}/overview'.format(atp_id)
    driver.get(match_url)
    time.sleep(0.5)

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

        flag_code = driver.find_element_by_xpath("//div[@class='player-flag-code']").text
        player["flag_code"] = flag_code

        birth_city = birth_country = None
        try:
            birth_place = driver.find_element_by_xpath("//div[@class='player-profile-hero-overflow']/div[2]/div["
                                                       "1]/table/tbody/tr[2]/td[1]/div/div[2]").text
            b_matched_location = birth_place.split(", ")
            if len(b_matched_location) > 1:
                birth_city = b_matched_location[0]
                birth_country = b_matched_location[-1]

                if not country_exists(birth_country):
                    raise NoSuchElementException("birth_country_not_found")
            else:
                raise NoSuchElementException("birth_country_not_found")

        except NoSuchElementException:
            pass
            # Couldn't find player birth place, Setting birth_country with flag_code
            birth_country = find_country_with_flag_code(flag_code)
            if birth_country is None:
                log("scrap_player", "Couldn't find birth country for player '{0}'".format(atp_id))

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


def get_player(player_id, players):
    player_match = players[players["flash_id"] == player_id]
    return player_match.iloc[0] if len(player_match) > 0 else None


def calculate_age(birth_date):
    days_in_year = 365.2425
    age = (datetime.today() - birth_date).days / days_in_year
    return age


def create_player(player):
    q_create_player(player.to_dict())


def update_player(player):
    return q_update_player(player)


def add_player_info(match):
    """Add p1 and p2 attributes to a match series"""
    p1 = find_player_by_id(match["p1_id"])
    if p1 is None:
        p1 = scrap_new_player(match["p1_id"], match["p1_url"])
        create_player(p1)

    p2 = find_player_by_id(match["p2_id"])
    if p2 is None:
        p2 = scrap_new_player(match["p2_id"], match["p2_url"])
        create_player(p2)

    if p1 is None or p2 is None:
        print("Couldn't find nor scrap players for  match '{0}'".format(match["match_id"]))
        return

    match["p1_hand"] = p1["handedness"]
    match["p1_backhand"] = p1["backhand"]
    match["p1_ht"] = p1["height"]
    match["p1_weight"] = p1["weight"]
    match["p1_age"] = calculate_age(p1["birth_date"])
    match["p1_rank"], match["p1_rank_points"] = retrieve_player_rank_info(p1["atp_id"])
    match["p1_birth_country"] = p1["birth_country"]
    match["p1_residence_country"] = p1["residence_country"]

    match["p2_hand"] = p2["handedness"]
    match["p2_backhand"] = p2["backhand"]
    match["p2_ht"] = p2["height"]
    match["p2_weight"] = p2["weight"]
    match["p2_age"] = calculate_age(p2["birth_date"])
    match["p2_rank"], match["p2_rank_points"] = retrieve_player_rank_info(p2["atp_id"])
    match["p2_birth_country"] = p2["birth_country"]
    match["p2_residence_country"] = p2["residence_country"]


def scrap_player_name_flashscore(flash_id, flash_url):
    driver = get_chrome_driver()
    match_url = "https://www.flashscore.com/player/{0}/{1}/".format(flash_url, flash_id)
    driver.get(match_url)
    time.sleep(1)
    player_name = driver.find_element_by_class_name("teamHeader__name").text
    driver.quit()
    return player_name


def scrap_new_player(flash_id, flash_url):
    player_full_name = scrap_player_name_flashscore(flash_id, flash_url)
    player_full_name, atp_id = scrap_player_id(player_full_name)
    player = scrap_player(atp_id)

    if player is None:
        return None

    player["flash_id"] = flash_id
    player["flash_url"] = flash_url
    player["player_name"] = player_full_name
    player["atp_id"] = atp_id

    return player


def create_player_manual(flash_id, flash_url, player_full_name, atp_id):
    player = scrap_player(atp_id)
    if player is None:
        print("couldn't scrap player")

    player["flash_id"] = flash_id
    player["flash_url"] = flash_url
    player["player_name"] = player_full_name
    player["atp_id"] = atp_id

    create_player(player)

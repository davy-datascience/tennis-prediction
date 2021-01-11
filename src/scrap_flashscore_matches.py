from selenium import webdriver
import re
import time
from selenium.common.exceptions import NoSuchElementException
from datetime import datetime
from dateutil.tz import UTC
from src.Classes.match import Match
from src.log import log
import pandas as pd

from src.tournament_manager import scrap_tournament, update_tournaments


def find_by_class(class_name, driver):
    try:
        return driver.find_element_by_class_name(class_name).text
    except NoSuchElementException:
        pass


def find_by_xpath(xpath, driver):
    try:
        return driver.find_element_by_xpath(xpath).text
    except NoSuchElementException:
        pass


def find_gms_value(player, set_nb, driver):
    suffix = "home" if player == 1 else "away"
    games = find_by_class("p{0}_{1}".format(set_nb, suffix), driver)
    return int(games) if games else None


def find_tb_score(player, set_nb, driver):
    suffix = "odd" if player == 1 else "even"
    score = find_by_xpath("//tr[@class='{0}']/td[{1}]/sup".format(suffix, set_nb + 3), driver)
    return int(score) if score else None


def scrap_match_flashscore(match_id):
    try:
        match_id = "GIecNDAM"  # TODO DELETE LINE
        driver = webdriver.Chrome('/home/davy/Drivers/chromedriver')
        match_url = "https://www.flashscore.com/match/" + match_id
        driver.get(match_url)
        time.sleep(1)

        p1_elem = driver.find_element_by_xpath("//div[@class='team-text tname-home']/div/div/a") \
            .get_attribute("onclick")
        p1_regex = re.search("/player/(.+)/(.+)\'", p1_elem)
        p1_url = p1_regex.group(1)
        p1_id = p1_regex.group(2)

        p2_elem = driver.find_element_by_xpath("//div[@class='team-text tname-away']/div/div/a") \
            .get_attribute("onclick")
        p2_regex = re.search("/player/(.+)/(.+)\'", p2_elem)
        p2_url = p2_regex.group(1)
        p2_id = p2_regex.group(2)

        match_date = None
        try:
            match_date_elem = driver.find_element_by_id("utime").text
            match_date_regex = re.search(r"^([0-9]+)\.([0-9]+)\.([0-9]+) ([0-9]+):([0-9]+)$", match_date_elem)
            day = int(match_date_regex.group(1))
            month = int(match_date_regex.group(2))
            year = int(match_date_regex.group(3))
            hour = int(match_date_regex.group(4))
            minute = int(match_date_regex.group(5))

            match_date = datetime(year, month, day, hour, minute, tzinfo=UTC)
        except Exception:
            msg = "Error with date format - scraping match '{}'".format(match_id)
            print(msg)
            log("scrap_match_flashscore", msg)
            raise Exception

        duration_elem = driver.find_element_by_xpath("//tr[1]/td[@class='score'][1]").text
        duration_regex = re.search("([0-9]+):([0-9]+)", duration_elem)
        duration = int(duration_regex.group(1)) * 60 + int(duration_regex.group(2))

        status_elem = driver.find_element_by_xpath("//div[@class='info-status mstat']").text

        p1_s1_gms = find_gms_value(1, 1, driver)
        p1_s2_gms = find_gms_value(1, 2, driver)
        p1_s3_gms = find_gms_value(1, 3, driver)
        p1_s4_gms = find_gms_value(1, 4, driver)
        p1_s5_gms = find_gms_value(1, 5, driver)

        p1_tb1_score = find_tb_score(1, 1, driver)
        p1_tb2_score = find_tb_score(1, 2, driver)
        p1_tb3_score = find_tb_score(1, 3, driver)
        p1_tb4_score = find_tb_score(1, 4, driver)
        p1_tb5_score = find_tb_score(1, 5, driver)

        p2_s1_gms = find_gms_value(1, 1, driver)
        p2_s2_gms = find_gms_value(1, 2, driver)
        p2_s3_gms = find_gms_value(1, 3, driver)
        p2_s4_gms = find_gms_value(1, 4, driver)
        p2_s5_gms = find_gms_value(1, 5, driver)

        p2_tb1_score = find_tb_score(1, 1, driver)
        p2_tb2_score = find_tb_score(1, 2, driver)
        p2_tb3_score = find_tb_score(1, 3, driver)
        p2_tb4_score = find_tb_score(1, 4, driver)
        p2_tb5_score = find_tb_score(1, 5, driver)

        driver.find_element_by_id("a-match-statistics").click()

        root = "//div[@id='tab-statistics-0-statistic']/"
        if (driver.find_element_by_xpath(root + "div[2]/div[1]/div[2]").text != "Aces"
                and driver.find_element_by_xpath(root + "div[3]/div[1]/div[2]").text != "Double Faults"
                and driver.find_element_by_xpath(root + "div[4]/div[1]/div[2]").text != "1st Serve Percentage"
                and driver.find_element_by_xpath(root + "div[5]/div[1]/div[2]").text != "1st Serve Points Won"
                and driver.find_element_by_xpath(root + "div[6]/div[1]/div[2]").text != "2nd Serve Points Won"
                and driver.find_element_by_xpath(root + "div[7]/div[1]/div[2]").text != "Break Points Saved"
                and driver.find_element_by_xpath(root + "div[9]/div[1]/div[2]").text != "1st Return Points Won"
                and driver.find_element_by_xpath(root + "div[10]/div[1]/div[2]").text != "2nd Return Points Won"
                and driver.find_element_by_xpath(root + "div[11]/div[1]/div[2]").text != "Break Points Converted"
                and driver.find_element_by_xpath(root + "div[13]/div[1]/div[2]").text != "Winners"
                and driver.find_element_by_xpath(root + "div[14]/div[1]/div[2]").text != "Unforced Errors"
                and driver.find_element_by_xpath(root + "div[15]/div[1]/div[2]").text != "Net Points Won"):
            print("Structure corrupted, match id '{}'".format(match_id))
            # return None

        p1_ace = int(driver.find_element_by_xpath(root + "div[2]/div[1]/div[1]").text)
        p1_df = int(driver.find_element_by_xpath(root + "div[3]/div[1]/div[1]").text)

        p1_svpt_elem = driver.find_element_by_xpath(root + "div[17]/div[1]/div[1]").text
        p1_svpt_regex = re.search(r"([0-9]+)% \(([0-9]+)/([0-9]+)", p1_svpt_elem)
        p1_svpt = p1_svpt_regex.group(3)
        p1_svpt_won = p1_svpt_regex.group(2)
        p1_svpt_ratio = int(p1_svpt_regex.group(1)) / 100

        p1_1st_elem = driver.find_element_by_xpath(root + "div[5]/div[1]/div[1]").text
        p1_1st_regex = re.search(r"([0-9]+)% \(([0-9]+)/([0-9]+)", p1_1st_elem)
        p1_1st_in = p1_1st_regex.group(3)
        p1_1st_won = p1_1st_regex.group(2)
        p1_1st_won_ratio = int(p1_1st_regex.group(1)) / 100

        p1_2nd_elem = driver.find_element_by_xpath(root + "div[6]/div[1]/div[1]").text
        p1_2nd_regex = re.search(r"([0-9]+)% \(([0-9]+)/([0-9]+)", p1_2nd_elem)
        p1_2nd_pts = p1_2nd_regex.group(3)
        p1_2nd_won = p1_2nd_regex.group(2)
        p1_2nd_won_ratio = int(p1_2nd_regex.group(1)) / 100

        p1_bp_elem = driver.find_element_by_xpath(root + "div[7]/div[1]/div[1]").text
        p1_bp_regex = re.search(r"([0-9]+)% \(([0-9]+)/([0-9]+)", p1_bp_elem)
        p1_bp_faced = p1_bp_regex.group(3)
        p1_bp_saved = p1_bp_regex.group(2)
        p1_bp_saved_ratio = int(p1_bp_regex.group(1)) / 100

        p1_bp_saved = int(driver.find_element_by_xpath(root + "div[2]/div[1]/div[1]").text)
        p1_bp_faced = int(driver.find_element_by_xpath(root + "div[2]/div[1]/div[1]").text)

        p2_ace = int(driver.find_element_by_xpath(root + "div[2]/div[1]/div[3]").text)
        p2_df = int(driver.find_element_by_xpath(root + "div[3]/div[1]/div[3]").text)

        p2_svpt_elem = driver.find_element_by_xpath(root + "div[17]/div[1]/div[3]").text
        p2_svpt_regex = re.search(r"([0-9]+)% \(([0-9]+)/([0-9]+)", p2_svpt_elem)
        p2_svpt = p2_svpt_regex.group(3)
        p2_svpt_won = p2_svpt_regex.group(2)
        p2_svpt_ratio = int(p2_svpt_regex.group(1)) / 100

        p2_1st_elem = driver.find_element_by_xpath(root + "div[5]/div[1]/div[3]").text
        p2_1st_regex = re.search(r"([0-9]+)% \(([0-9]+)/([0-9]+)", p2_1st_elem)
        p2_1st_in = p2_1st_regex.group(3)
        p2_1st_won = p2_1st_regex.group(2)
        p2_1st_won_ratio = int(p2_1st_regex.group(1)) / 100

        p2_2nd_elem = driver.find_element_by_xpath(root + "div[6]/div[1]/div[3]").text
        p2_2nd_regex = re.search(r"([0-9]+)% \(([0-9]+)/([0-9]+)", p2_2nd_elem)
        p2_2nd_pts = p2_2nd_regex.group(3)
        p2_2nd_won = p2_2nd_regex.group(2)
        p2_2nd_won_ratio = int(p2_2nd_regex.group(1)) / 100

        p2_bp_elem = driver.find_element_by_xpath(root + "div[7]/div[1]/div[3]").text
        p2_bp_regex = re.search(r"([0-9]+)% \(([0-9]+)/([0-9]+)", p2_bp_elem)
        p2_bp_faced = p2_bp_regex.group(3)
        p2_bp_saved = p2_bp_regex.group(2)
        p2_bp_saved_ratio = int(p2_bp_regex.group(1)) / 100

        p2_bp_saved = int(driver.find_element_by_xpath(root + "div[2]/div[1]/div[3]").text)
        p2_bp_faced = int(driver.find_element_by_xpath(root + "div[2]/div[1]/div[3]").text)

        # match = pd.DataFrame([[match_id, status, tournament_id, p1_id, p2_id, surface, match_date, tour_date, draw_size, tourney_level, best_of, round, duration, year, country, ret, p1_hand, p1_backhand, p1_ht, p1_weight, p1_age, p1_ace, p1_df, p1_svpt, p1_1stIn, p1_1stWon, p1_2ndWon, p1_SvGms, p1_bpSaved, p1_bpFaced, p1_rank, p1_rank_points, p1_birth_country, p1_residence_country, p2_hand, p2_backhand, p2_ht, p2_weight, p2_age, p2_ace, p2_df, p2_svpt, p2_1stIn, p2_1stWon, p2_2ndWon, p2_SvGms, p2_bpSaved, p2_bpFaced, p2_rank, p2_rank_points, p2_birth_country, p2_residence_country, p1_s1_gms, p2_s1_gms, p1_tb1_score, p2_tb1_score, p1_s2_gms, p2_s2_gms, p1_tb2_score, p2_tb2_score, p1_s3_gms, p2_s3_gms, p1_tb3_score, p2_tb3_score, p1_s4_gms, p2_s4_gms, p1_tb4_score, p2_tb4_score, p1_s5_gms, p2_s5_gms, p1_tb5_score, p2_tb5_score, p1_2nd_pts, p2_2nd_pts, p1_svpt_won, p2_svpt_won, p1_svpt_ratio, p2_svpt_ratio, p1_1stWon_ratio, p2_1stWon_ratio, p1_2ndWon_ratio, p2_2ndWon_ratio, p1_SvGmsWon, p2_SvGmsWon, p1_SvGmsWon_ratio, p2_SvGmsWon_ratio, p1_1st_serve_ratio, p2_1st_serve_ratio, p1_bpSaved_ratio, p2_bpSaved_ratio, p1_wins, prediction, prediction_version]])

    except Exception as ex:
        print("Error while scraping match id '{}'".format(match_id))
        print(type(ex))
        return None


def scrap_matches(driver, tournaments, date):
    date = datetime.now()
    driver = webdriver.Chrome('/home/davy/Drivers/chromedriver')
    match_url = "https://www.flashscore.com/tennis"
    driver.get(match_url)
    # TODO delete prev lines

    tournament = None
    names = []
    elements = driver.find_elements_by_xpath("//div[@class='sportName tennis']/div")
    for elem in elements:
        if elem.get_attribute("class") in ["event__header", "event__header top"]:
            # Tournament header

            # Look for atp-singles tournaments only -> ignore others
            category = elem.find_element_by_class_name("event__title--type").text
            if category != "ATP - SINGLES":
                tournament = None
                continue

            name = elem.find_element_by_class_name("event__title--name").text

            # Check if tournament matches are in qualification stage -> ignore qualifications
            qualification_regex = re.search("Qualification", name)
            if qualification_regex:
                tournament = None
                continue

            names.append(name)

            tournament_name_regex = re.search(r"^(.*) \(", name)
            tournament_name = tournament_name_regex.group(1)
            tournament_search = tournaments[tournaments["flash_name"] == tournament_name].copy()

            if len(tournament_search.index) > 0:
                # Tournament exists
                tournament_matched = tournament_search.iloc[0].copy()

                if tournament_matched["start_date"].year != datetime.now().year:
                    # Tournament to be updated
                    tournament = scrap_tournament(tournament_matched, date)
                    if tournament is not None:
                        print("updating tournament {0}".format(tournament["flash_id"]))
                        update_tournaments(tournaments, tournament)

            else:
                # New tournament to be scrapped

                # TODO scrap new tournament
                # create_tournament(tournament_name)
                tournament = None
                continue

        else:
            # Match row
            if tournament is None:
                # Match is not to be retrieved
                continue



    driver.quit()

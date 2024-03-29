import pandas as pd
import re
import time

from selenium.common.exceptions import NoSuchElementException
from datetime import datetime, timedelta
from log import log, log_to_file, get_file_log

from classes.match_status import MatchStatus
from managers.player_manager import add_player_info
from managers.tournament_manager import scrap_tournament, add_tournament_info, update_tournament, create_tournament
from queries.match_queries import q_find_match_by_id, q_update_match, q_create_match, q_delete_match, \
    get_embedded_matches_json
from queries.tournament_queries import find_tournament_by_name
from utils import element_has_class, get_chrome_driver

MATCHES_LOGS = get_file_log("scrap_matches")
MATCHES_ERROR_LOGS = get_file_log("scrap_matches_error")
TOURNAMENT_LOGS = get_file_log("tournament_updates")


def get_match_dtypes(matches):
    all_dtypes = {
        "draw_size": "Int16", "best_of": "object", "minutes": "Int16", "p1_ht": "Int16", "p2_ht": "Int16",
        "p1_weight": "Int16",
        "p2_weight": "Int16", "p1_ace": "Int16", "p2_ace": "Int16", "p1_df": "Int16", "p2_df": "Int16",
        "p1_svpt": "Int16", "p2_svpt": "Int16", "p1_1st_in": "Int16", "p2_1st_in": "Int16", "p1_1st_won": "Int16",
        "p2_1st_won": "Int16", "p1_2nd_won": "Int16", "p2_2nd_won": "Int16", "p1_sv_gms": "Int16",
        "p2_sv_gms": "Int16", "p1_bp_saved": "Int16", "p2_bp_saved": "Int16", "p1_bp_faced": "Int16",
        "p2_bp_faced": "Int16", "p1_rank": "Int16", "p2_rank": "Int16", "p1_rank_points": "Int16",
        "p2_rank_points": "Int16", "p1_s1_gms": "Int16", "p2_s1_gms": "Int16", "p1_tb1_score": "Int16",
        "p2_tb1_score": "Int16", "p1_s2_gms": "Int16", "p2_s2_gms": "Int16", "p1_tb2_score": "Int16",
        "p2_tb2_score": "Int16", "p1_s3_gms": "Int16", "p2_s3_gms": "Int16", "p1_tb3_score": "Int16",
        "p2_tb3_score": "Int16", "p1_s4_gms": "Int16", "p2_s4_gms": "Int16", "p1_tb4_score": "Int16",
        "p2_tb4_score": "Int16", "p1_s5_gms": "Int16", "p2_s5_gms": "Int16", "p1_tb5_score": "Int16",
        "p2_tb5_score": "Int16", "p1_2nd_pts": "Int16", "p2_2nd_pts": "Int16", "p1_svpt_won": "Int16",
        "p2_svpt_won": "Int16", "p1_age": "float", "p2_age": "float", "p1_1st_serve_ratio": "float",
        "p2_1st_serve_ratio": "float", "p1_svpt_ratio": "float", "p2_svpt_ratio": "float",
        "p1_1st_won_ratio": "float", "p2_1st_won_ratio": "float", "p1_2nd_won_ratio": "float",
        "p2_2nd_won_ratio": "float", "p1_sv_gms_won": "Int16", "p2_sv_gms_won": "Int16",
        "p1_sv_gms_won_ratio": "float", "p2_sv_gms_won_ratio": "float", "p1_bp_saved_ratio": "float",
        "p2_bp_saved_ratio": "float", "p1_wins": "bool", "datetime": "datetime64[ns, utc]",
        "tour_date": "datetime64[ns, utc]", "created": "datetime64[ns, utc]", "updated": "datetime64[ns, utc]"
    }

    dtypes = {}

    for key in all_dtypes.keys():
        if key in matches.columns.to_list():
            dtypes[key] = all_dtypes[key]

    return dtypes


def find_by_xpath(xpath, driver):
    try:
        return driver.find_element_by_xpath(xpath).text
    except NoSuchElementException:
        pass


def get_text_excluding_children(driver, element):

    return driver.execute_script("""

    var parent = arguments[0];

    var child = parent.firstChild; 

    var ret = ""; while(child) { 

          if(child.nodeType === Node.TEXT_NODE) 

             ret += child.textContent;

             child = child.nextSibling; 

    } 

    return ret;

     """, element)


def find_gms_value(player, set_nb, driver):
    gms_value = None
    tb_score = None

    suffix = "home___" if player == 1 else "away___"
    elements = driver.find_elements_by_xpath("//div[contains(@class, 'part--{0}') and contains(@class, '{1}')]"
                                             .format(set_nb, suffix))
    for elem in elements:
        if element_has_class(elem, "part--{0}".format(set_nb)) and elem.text != "":
            gms_value = int(get_text_excluding_children(driver, elem))
            if elem.find_element_by_xpath("sup").text != "":
                tb_score = int(elem.find_element_by_xpath("sup").text)
            break

    return gms_value, tb_score


def find_tb_score(player, set_nb, driver):
    suffix = "odd" if player == 1 else "even"
    score = find_by_xpath("//tr[@class='{0}']/td[{1}]/sup".format(suffix, set_nb + 3), driver)
    return int(score) if score else None


def scrap_player_ids(driver):
    p1_elem = driver.find_element_by_xpath("//div[@id='detail']/div[4]/div[2]/div[4]/div[2]/a") \
        .get_attribute("href")
    p1_regex = re.search("/player/(.+)/(.+)$", p1_elem)
    p1_url = p1_regex.group(1)
    p1_id = p1_regex.group(2)

    p2_elem = driver.find_element_by_xpath("//div[@id='detail']/div[4]/div[4]/div[4]/div[1]/a") \
        .get_attribute("href")
    p2_regex = re.search("/player/(.+)/(.+)$", p2_elem)
    p2_url = p2_regex.group(1)
    p2_id = p2_regex.group(2)

    return p1_id, p1_url, p2_id, p2_url


def scrap_match_flashscore(match_id, status):
    match = pd.Series([match_id], index=["match_id"])
    driver = get_chrome_driver()

    try:
        match["match_id"] = match_id
        match_url = "https://www.flashscore.com/match/" + match_id
        driver.get(match_url)
        time.sleep(1)

        tournament_elem = driver.find_element_by_xpath(
            "//div[contains(@class, 'tournamentHeaderDescription')]/div[1]/span[3]/a"
        )

        tournament_regex = re.search("atp-singles/(.*)/", tournament_elem.get_attribute("href"))
        match["tournament_id"] = tournament_regex.group(1)
        add_tournament_info(match)

        round_regex = re.search(",.*- (.*)$", tournament_elem.text)
        if round_regex:
            match["round"] = round_regex.group(1)
        else:
            match["round"] = "Group"

        match["p1_id"], match["p1_url"], match["p2_id"], match["p2_url"] = scrap_player_ids(driver)
        add_player_info(match)
        match.drop(columns=["p1_url", "p2_url"], inplace=True)

        match_date = None
        try:
            match_date_elem = driver.find_element_by_xpath("//div[@id='detail']/div[4]/div[1]").text
            match_date_regex = re.search(r"^([0-9]+)\.([0-9]+)\.([0-9]+) ([0-9]+):([0-9]+)$", match_date_elem)
            day = int(match_date_regex.group(1))
            month = int(match_date_regex.group(2))
            year = int(match_date_regex.group(3))
            hour = int(match_date_regex.group(4))
            minute = int(match_date_regex.group(5))

            match_date = pd.to_datetime("{0} {1} {2} {3} {4}".format(year, month, day, hour, minute)
                                        , format='%Y %m %d %H %M', utc=True)

        except Exception as ex:
            msg = "Error with date format - scraping match '{}'".format(match_id)
            log_to_file(msg, MATCHES_ERROR_LOGS)
            log("scrap_match", msg, type(ex).__name__)
            raise Exception

        match["datetime"] = match_date

        '''
        Section usefull for scrap_tournament_matches()
        
        if status is None:
            status_elem = driver.find_element_by_xpath("//div[@id='detail']/div[4]/div[3]/div[1]/div[2]/span[1]").text
            if status_elem == "Finished":
                status = MatchStatus.Finished
            else:
                retired_regex = re.search("retired", status_elem)
                if retired_regex:
                    status = MatchStatus.Retired
                else:
                    msg = "status_error - match '{}'".format(match_id)
                    log_to_file(msg, MATCHES_ERROR_LOGS)
                    log("scrap_match", msg)
                    driver.quit()
                    return None
        '''

        match["status"] = status.name

        if status in [MatchStatus.Finished, MatchStatus.Retired, MatchStatus.Live, MatchStatus.Awarded,
                      MatchStatus.Interrupted]:

            if status != MatchStatus.Live:
                # Set match winner only if match has already finished
                participant_elems = driver.find_elements_by_xpath("//a[starts-with(@class, 'participantName___')]")

                if len(participant_elems[-1].find_elements_by_xpath("strong")) == 1:
                    match["p1_wins"] = False
                else:
                    match["p1_wins"] = True

            duration_elem = driver.find_element_by_xpath("//div[contains(@class, 'time--overall')]").text
            duration_regex = re.search("([0-9]+):([0-9]+)", duration_elem)
            match["minutes"] = int(duration_regex.group(1)) * 60 + int(duration_regex.group(2))

            match["p1_s1_gms"], match["p1_tb1_score"] = find_gms_value(1, 1, driver)
            match["p1_s2_gms"], match["p1_tb2_score"] = find_gms_value(1, 2, driver)
            match["p1_s3_gms"], match["p1_tb3_score"] = find_gms_value(1, 3, driver)
            match["p1_s4_gms"], match["p1_tb4_score"] = find_gms_value(1, 4, driver)
            match["p1_s5_gms"], match["p1_tb5_score"] = find_gms_value(1, 5, driver)

            match["p2_s1_gms"], match["p2_tb1_score"] = find_gms_value(2, 1, driver)
            match["p2_s2_gms"], match["p2_tb2_score"] = find_gms_value(2, 2, driver)
            match["p2_s3_gms"], match["p2_tb3_score"] = find_gms_value(2, 3, driver)
            match["p2_s4_gms"], match["p2_tb4_score"] = find_gms_value(2, 4, driver)
            match["p2_s5_gms"], match["p2_tb5_score"] = find_gms_value(2, 5, driver)

            driver.find_element_by_link_text("Statistics").click()
            time.sleep(0.5)

            row_elements = driver.find_elements_by_xpath("//div[starts-with(@class, 'statRow___')]") # stat_elem.find_elements_by_class_name("statRow")

            stat_labels = []
            p1_stats = []
            p2_stats = []
            for row_elem in row_elements:
                stat_labels.append(row_elem.find_element_by_xpath("div[1]/div[2]").text)
                p1_stats.append(row_elem.find_element_by_xpath("div[1]/div[1]").text)
                p2_stats.append(row_elem.find_element_by_xpath("div[1]/div[3]").text)

            stats_dataframe = pd.DataFrame({"label": stat_labels, "p1": p1_stats, "p2": p2_stats})

            match["p1_ace"] = int(stats_dataframe[stats_dataframe["label"] == "Aces"].iloc[0]["p1"])
            match["p1_df"] = int(stats_dataframe[stats_dataframe["label"] == "Double Faults"].iloc[0]["p1"])

            p1_svpt_elem = stats_dataframe[stats_dataframe["label"] == "Service Points Won"].iloc[0]["p1"]
            p1_svpt_regex = re.search(r"([0-9]+)% \(([0-9]+)/([0-9]+)", p1_svpt_elem)
            match["p1_svpt"] = int(p1_svpt_regex.group(3))
            match["p1_svpt_won"] = int(p1_svpt_regex.group(2))
            match["p1_svpt_ratio"] = int(p1_svpt_regex.group(1)) / 100

            p1_1st_elem = stats_dataframe[stats_dataframe["label"] == "1st Serve Points Won"].iloc[0]["p1"]
            p1_1st_regex = re.search(r"([0-9]+)% \(([0-9]+)/([0-9]+)", p1_1st_elem)
            match["p1_1st_in"] = int(p1_1st_regex.group(3))
            match["p1_1st_won"] = int(p1_1st_regex.group(2))
            match["p1_1st_won_ratio"] = int(p1_1st_regex.group(1)) / 100

            p1_2nd_elem = stats_dataframe[stats_dataframe["label"] == "2nd Serve Points Won"].iloc[0]["p1"]
            p1_2nd_regex = re.search(r"([0-9]+)% \(([0-9]+)/([0-9]+)", p1_2nd_elem)
            match["p1_2nd_pts"] = int(p1_2nd_regex.group(3))
            match["p1_2nd_won"] = int(p1_2nd_regex.group(2))
            match["p1_2nd_won_ratio"] = int(p1_2nd_regex.group(1)) / 100

            p1_bp_elem = stats_dataframe[stats_dataframe["label"] == "Break Points Saved"].iloc[0]["p1"]
            p1_bp_regex = re.search(r"([0-9]+)% \(([0-9]+)/([0-9]+)", p1_bp_elem)
            match["p1_bp_faced"] = int(p1_bp_regex.group(3))
            match["p1_bp_saved"] = int(p1_bp_regex.group(2))
            match["p1_bp_saved_ratio"] = int(p1_bp_regex.group(1)) / 100

            match["p2_ace"] = int(stats_dataframe[stats_dataframe["label"] == "Aces"].iloc[0]["p2"])
            match["p2_df"] = int(stats_dataframe[stats_dataframe["label"] == "Double Faults"].iloc[0]["p2"])

            p2_svpt_elem = stats_dataframe[stats_dataframe["label"] == "Service Points Won"].iloc[0]["p2"]
            p2_svpt_regex = re.search(r"([0-9]+)% \(([0-9]+)/([0-9]+)", p2_svpt_elem)
            match["p2_svpt"] = int(p2_svpt_regex.group(3))
            match["p2_svpt_won"] = int(p2_svpt_regex.group(2))
            match["p2_svpt_ratio"] = int(p2_svpt_regex.group(1)) / 100

            p2_1st_elem = stats_dataframe[stats_dataframe["label"] == "1st Serve Points Won"].iloc[0]["p2"]
            p2_1st_regex = re.search(r"([0-9]+)% \(([0-9]+)/([0-9]+)", p2_1st_elem)
            match["p2_1st_in"] = int(p2_1st_regex.group(3))
            match["p2_1st_won"] = int(p2_1st_regex.group(2))
            match["p2_1st_won_ratio"] = int(p2_1st_regex.group(1)) / 100

            p2_2nd_elem = stats_dataframe[stats_dataframe["label"] == "2nd Serve Points Won"].iloc[0]["p2"]
            p2_2nd_regex = re.search(r"([0-9]+)% \(([0-9]+)/([0-9]+)", p2_2nd_elem)
            match["p2_2nd_pts"] = int(p2_2nd_regex.group(3))
            match["p2_2nd_won"] = int(p2_2nd_regex.group(2))
            match["p2_2nd_won_ratio"] = int(p2_2nd_regex.group(1)) / 100

            p2_bp_elem = stats_dataframe[stats_dataframe["label"] == "Break Points Saved"].iloc[0]["p2"]
            p2_bp_regex = re.search(r"([0-9]+)% \(([0-9]+)/([0-9]+)", p2_bp_elem)
            match["p2_bp_faced"] = int(p2_bp_regex.group(3))
            match["p2_bp_saved"] = int(p2_bp_regex.group(2))
            match["p2_bp_saved_ratio"] = int(p2_bp_regex.group(1)) / 100

            p1_sv_gms_elem = stats_dataframe[stats_dataframe["label"] == "Service Games Won"].iloc[0]["p1"]
            p1_sv_gms_rgx = re.search(r"([0-9]+)% \(([0-9]+)/([0-9]+)", p1_sv_gms_elem)
            match["p1_sv_gms"] = int(p1_sv_gms_rgx.group(3))
            match["p1_sv_gms_won"] = int(p1_sv_gms_rgx.group(2))
            match["p1_sv_gms_won_ratio"] = int(p1_sv_gms_rgx.group(1)) / 100

            p2_sv_gms_elem = stats_dataframe[stats_dataframe["label"] == "Service Games Won"].iloc[0]["p2"]
            p2_sv_gms_rgx = re.search(r"([0-9]+)% \(([0-9]+)/([0-9]+)", p2_sv_gms_elem)
            match["p2_sv_gms"] = int(p2_sv_gms_rgx.group(3))
            match["p2_sv_gms_won"] = int(p2_sv_gms_rgx.group(2))
            match["p2_sv_gms_won_ratio"] = int(p2_sv_gms_rgx.group(1)) / 100

            match["p1_1st_serve_ratio"] = match["p1_1st_in"] / match["p1_svpt"] if match["p1_svpt"] > 0 else None
            match["p2_1st_serve_ratio"] = match["p2_1st_in"] / match["p2_svpt"] if match["p2_svpt"] > 0 else None

    except Exception as ex:
        msg = "Error while scraping match id '{}'".format(match_id)
        log_to_file(msg, MATCHES_ERROR_LOGS)
        log("scrap_match", msg, type(ex).__name__)
        match = None

    driver.quit()
    return match


def create_match(match):
    try:
        matches_json = get_embedded_matches_json(pd.DataFrame(match).T)
        result = q_create_match(matches_json[0])
        if not result:
            raise Exception("Match not created")
        log_to_file("match '{0}' has been created".format(match["match_id"]), MATCHES_LOGS)

    except Exception as ex:
        log_to_file("match '{0}' couldn't be created".format(match["match_id"]), MATCHES_ERROR_LOGS)
        log("scrap_match", "match '{0}' couldn't be created".format(match["match_id"]), type(ex).__name__)


def update_match(match):
    try:
        matches_json = get_embedded_matches_json(pd.DataFrame(match).T)
        q_update_match(matches_json[0])
        log_to_file("match '{0}' has been updated".format(match["_id"]), MATCHES_LOGS)
    except Exception as ex:
        log_to_file("match '{0}' couldn't be updated".format(match["match_id"]), MATCHES_ERROR_LOGS)
        log("scrap_match", "match '{0}' couldn't be updated".format(match["match_id"]), type(ex).__name__)


def delete_match(_id):
    result = q_delete_match(_id)

    if result is None:
        log_to_file("match '{0}' not deleted".format(_id), MATCHES_ERROR_LOGS)
        log("match_delete", "match '{0}' not deleted".format(_id))


def navigate_to_date(driver, matches_date):
    now = datetime.now()
    today = now.date()

    time_delta = (matches_date - today).days

    nav_elements = driver.find_elements_by_class_name('calendar__nav')

    if time_delta < 0:
        for i in range(-time_delta):
            yesterday = nav_elements[0]
            yesterday.click()
            time.sleep(2)
    elif time_delta > 0:
        for i in range(time_delta):
            tomorrow = nav_elements[1]
            tomorrow.click()
            time.sleep(2)


def get_flash_tournaments_from_menu(driver):
    el = driver.find_element_by_xpath("//a[@id='lmenu_5724']")
    driver.execute_script("arguments[0].click();", el)
    time.sleep(1)

    flash_names = []
    flash_ids = []
    tournaments_info = driver.find_elements_by_xpath("//div[@id='category-left-menu']/div/div/span/a")

    for tournament_info in tournaments_info:
        link = tournament_info.get_attribute("href")
        tournament_regex = re.search("atp-singles/(.+)$", link)
        if tournament_regex:
            flash_names.append(tournament_info.get_property("text"))
            flash_id = tournament_regex.group(1)
            flash_ids.append(flash_id)

    flash_tournaments = pd.DataFrame({"name": flash_names, "flash_id": flash_ids})

    return flash_tournaments


def get_tournament_from_row(driver, elem, matches_date):
    tournament = None
    # Look for atp-singles tournaments only -> ignore others
    category = elem.find_element_by_class_name("event__title--type").text
    if category != "ATP - SINGLES":
        return None

    name = elem.find_element_by_class_name("event__title--name").text

    # Check if tournament matches are in qualification stage -> ignore qualifications
    qualification_regex = re.search("Qualification", name)
    if qualification_regex:
        return None

    tournament_name_regex = re.search(r"^([^(]*) \(([^)]*)\)", name)
    tournament_name = tournament_name_regex.group(1)
    tournament_country = tournament_name_regex.group(2)
    tournament_found = find_tournament_by_name(tournament_name)

    if tournament_found is not None:
        # Tournament exists
        if tournament_found["start_date"].year != datetime.now().year:
            # Tournament to be updated
            tournament = scrap_tournament(tournament_found, matches_date)
            if tournament is not None:
                log_to_file("updating tournament {0}".format(tournament["flash_id"]), TOURNAMENT_LOGS)
                update_tournament(tournament)
        else:
            # Tournament exists and is up-to-date
            tournament = tournament_found

    else:
        # New tournament to be scrapped

        if tournament_name.startswith("Davis Cup"):
            # print("Ignoring Davis Cup")
            return None

        # Look for tournament id in tournaments menu
        flash_tournaments = get_flash_tournaments_from_menu(driver)

        tournament_matched = flash_tournaments[flash_tournaments["name"] == tournament_name]

        if len(tournament_matched.index) != 1:
            msg = "Couldn't find flashscore tournament id for '{0}'".format(tournament_name)
            log_to_file(msg, TOURNAMENT_LOGS)
            log("tournaments", msg)
            return None

        tournament_id = tournament_matched.iloc[0]["flash_id"]

        tournament_scrapped = scrap_tournament(pd.Series(
            {"flash_id": tournament_id,
             "flash_name": tournament_name,
             "country": tournament_country
             }
        ), matches_date)

        if tournament_scrapped is not None:
            create_tournament(tournament_scrapped)
            tournament = tournament_scrapped

    return tournament


def find_match_status(elem):
    match_status = None
    if element_has_class(elem, "event__match--live"):
        match_status = MatchStatus.Live
    else:
        try:
            elem.find_element_by_class_name("event__time")
            # Match is scheduled
            match_status = MatchStatus.Scheduled
        except NoSuchElementException:
            # Match is not scheduled
            pass

    if match_status is None:
        status_str = elem.find_element_by_class_name("event__stage--block").text
        if status_str == "Finished":
            match_status = MatchStatus.Finished
        elif status_str == "Walkover":
            match_status = MatchStatus.Walkover
        elif status_str == "Cancelled":
            match_status = MatchStatus.Cancelled
        elif "retired" in status_str:
            match_status = MatchStatus.Retired

        if match_status is None:
            msg = "Status '{0}' Not Found".format(status_str)
            log_to_file(msg, MATCHES_ERROR_LOGS)
            log("status", msg)

    return match_status


def process_match_row(elem, matches_date):
    elem_id = elem.get_attribute("id")
    match_id_regex = re.search("^._._(.*)$", elem_id)
    match_id = match_id_regex.group(1)

    match_status = find_match_status(elem)

    if match_status is None:
        msg = "Status not found for match '{0}'".format(match_id)
        log_to_file(msg, MATCHES_ERROR_LOGS)
        log("status", MATCHES_ERROR_LOGS)
        return

    match_found = q_find_match_by_id(match_id)

    if match_found is not None:
        # Match exists
        if MatchStatus[match_found["status"]] not in [MatchStatus.Finished, MatchStatus.Retired, MatchStatus.Awarded]:
            # Match is not recorded as 'finished' in database
            if match_status in [MatchStatus.Finished, MatchStatus.Retired, MatchStatus.Live, MatchStatus.Awarded]\
                    or (match_status == MatchStatus.Interrupted
                        and MatchStatus[match_found["status"]] != MatchStatus.Interrupted):
                # Match is finished or live
                match = scrap_match_flashscore(match_id, match_status)
                match["_id"] = match_found["_id"]
                update_match(match)

            elif match_status in [MatchStatus.Walkover, MatchStatus.Cancelled]:
                # Match has been canceled
                delete_match(match_found["_id"])
                print("Delete match '{0}'".format(match_id))
                pass

            elif match_status == MatchStatus.Scheduled:
                # Updating match datetime if changed
                time_elem = elem.find_element_by_class_name("event__time").text
                time_regex = re.search(r"(\d{2}):(\d{2})$", time_elem)
                hour = int(time_regex.group(1))
                minute = int(time_regex.group(2))
                match_date = datetime(matches_date.year, matches_date.month, matches_date.day, hour, minute)

                if match_found["datetime"] != match_date:
                    match_dict = {'datetime': match_date, '_id': match_found["_id"]}
                    match = pd.Series(match_dict)
                    update_match(match)
    else:
        # Match doesn't exist
        match = None
        if match_status not in [MatchStatus.Walkover, MatchStatus.Cancelled]:
            # Scrap match preview
            match = scrap_match_flashscore(match_id, match_status)

            if match is None:
                return

            create_match(match)


def scrap_matches_at_date(matches_date):
    driver = get_chrome_driver()
    match_url = "https://www.flashscore.com/tennis"
    driver.get(match_url)

    navigate_to_date(driver, matches_date)

    tournament = None
    elements = driver.find_elements_by_xpath("//div[@class='sportName tennis']/div")
    for elem in elements:
        if element_has_class(elem, "event__header"):
            # Tournament header
            tournament = get_tournament_from_row(driver, elem, matches_date)
        else:
            # Match row
            if tournament is None:
                # Match is not to be retrieved
                continue

            process_match_row(elem, matches_date)

    driver.quit()


def scrap_matches():
    # ATTENTION UTC !!!!
    today = datetime.now().date()

    # Scrap matches from yesterday to D+3
    for delta in range(-1, 4):
        scrap_matches_at_date(today + timedelta(days=delta))


'''
def scrap_tournament_matches(tournament_id, matches_date):
    driver = get_chrome_driver()
    match_url = "https://www.flashscore.com/tennis/atp-singles/{0}/results/".format(tournament_id)
    driver.get(match_url)

    tournament = None
    elements = driver.find_elements_by_xpath("//div[@class='sportName tennis']/div")

    for elem in elements:
        if element_has_class(elem, "event__header"):
            tournament = get_tournament_from_row(driver, elem, matches_date)
        elif element_has_class(elem, "event__round"):
            continue
        else:
            if tournament is not None:
                elem_id = elem.get_attribute("id")
                match_id_regex = re.search("^._._(.*)$", elem_id)
                match_id = match_id_regex.group(1)

                match = scrap_match_flashscore(match_id, None)

                if match is not None:
                    create_match(match)

    driver.quit()


def scrap_mutliple_tournament_matches():
    date_str = "2021.08.30"
    scrap_all_player_ranks(date_str)

    tournament_ids = ["winston-salem"]
    matches_date = datetime(2021, 8, 24)
    for tournament_id in tournament_ids:
        scrap_tournament_matches(tournament_id, matches_date)
'''

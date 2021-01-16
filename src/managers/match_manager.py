import configparser
from json import JSONEncoder
from bson.json_util import loads
import pymongo
from pytz import timezone
from selenium.common.exceptions import NoSuchElementException
import re
import time
from datetime import datetime
from src.log import log
import pandas as pd
import numpy as np

from src.classes.match_status import MatchStatus
from src.managers.player_manager import add_player_info
from src.managers.tournament_manager import scrap_tournament, add_tournament_info
from src.utils import element_has_class, get_chrome_driver

config = configparser.ConfigParser()
config.read("src/config.ini")
MONGO_CLIENT = config['mongo']['client']


def get_match_dtypes():
    return {"draw_size": "Int16", "best_of": "object", "minutes": "Int16", "p1_ht": "Int16", "p2_ht": "Int16",
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
            "tour_date": "datetime64[ns, utc]"}


def get_match_ordered_attributes():
    return ['match_id', 'status', 'tournament_id', 'p1_id', 'p1_url', 'p2_id', 'p2_url', 'surface', 'datetime',
            'tour_date', 'draw_size', 'tourney_level', 'best_of', 'round', 'minutes', 'country',
            'p1_hand', 'p1_backhand', 'p1_ht', 'p1_weight', 'p1_age', 'p1_ace', 'p1_df', 'p1_svpt', 'p1_1st_in',
            'p1_1st_won', 'p1_2nd_won', 'p1_sv_gms', 'p1_bp_saved', 'p1_bp_faced', 'p1_rank', 'p1_rank_points',
            'p1_birth_country', 'p1_residence_country', 'p2_hand', 'p2_backhand', 'p2_ht', 'p2_weight', 'p2_age',
            'p2_ace', 'p2_df', 'p2_svpt', 'p2_1st_in', 'p2_1st_won', 'p2_2nd_won', 'p2_sv_gms', 'p2_bp_saved',
            'p2_bp_faced', 'p2_rank', 'p2_rank_points', 'p2_birth_country', 'p2_residence_country', 'p1_s1_gms',
            'p2_s1_gms', 'p1_tb1_score', 'p2_tb1_score', 'p1_s2_gms', 'p2_s2_gms', 'p1_tb2_score',
            'p2_tb2_score', 'p1_s3_gms', 'p2_s3_gms', 'p1_tb3_score', 'p2_tb3_score', 'p1_s4_gms', 'p2_s4_gms',
            'p1_tb4_score', 'p2_tb4_score', 'p1_s5_gms', 'p2_s5_gms', 'p1_tb5_score', 'p2_tb5_score',
            'p1_2nd_pts', 'p2_2nd_pts', 'p1_svpt_won', 'p2_svpt_won', 'p1_1st_serve_ratio', 'p2_1st_serve_ratio',
            'p1_svpt_ratio', 'p2_svpt_ratio', 'p1_1st_won_ratio', 'p2_1st_won_ratio', 'p1_2nd_won_ratio',
            'p2_2nd_won_ratio', 'p1_sv_gms_won', 'p2_sv_gms_won', 'p1_sv_gms_won_ratio', 'p2_sv_gms_won_ratio',
            'p1_bp_saved_ratio', 'p2_bp_saved_ratio', 'p1_wins', 'prediction', 'prediction_version']


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


def scrap_player_ids(driver):
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

    return p1_id, p1_url, p2_id, p2_url


def scrap_match_flashscore(match_id, status, players, tournaments):
    match = pd.Series([match_id], index=["match_id"])
    driver = get_chrome_driver()

    try:
        match["match_id"] = match_id
        match_url = "https://www.flashscore.com/match/" + match_id
        driver.get(match_url)
        time.sleep(1)

        tournament_elem = driver.find_element_by_xpath("//span[@class='description__country']/a") \
            .get_attribute("onclick")
        tournament_regex = re.search("atp-singles/(.*)/", tournament_elem)
        match["tournament_id"] = tournament_regex.group(1)
        add_tournament_info(match, tournaments)

        match["p1_id"], match["p1_url"], match["p2_id"], match["p2_url"] = scrap_player_ids(driver)
        add_player_info(match, players)

        match_date = None
        try:
            match_date_elem = driver.find_element_by_id("utime").text
            match_date_regex = re.search(r"^([0-9]+)\.([0-9]+)\.([0-9]+) ([0-9]+):([0-9]+)$", match_date_elem)
            day = int(match_date_regex.group(1))
            month = int(match_date_regex.group(2))
            year = int(match_date_regex.group(3))
            hour = int(match_date_regex.group(4))
            minute = int(match_date_regex.group(5))

            match_date = pd.to_datetime("{0} {1} {2} {3} {4}".format(year, month, day, hour, minute)
                                        , format='%Y %m %d %H %M', utc=True).replace(tzinfo=timezone('Europe/Paris'))

        except Exception:
            msg = "Error with date format - scraping match '{}'".format(match_id)
            print(msg)
            log("scrap_match_flashscore", msg)
            raise Exception

        match["datetime"] = match_date

        description = driver.find_element_by_xpath("//span[@class='description__country']/a").text
        round_regex = re.search(",.*- (.*)$", description)
        match["round"] = round_regex.group(1)

        match["status"] = status.name

        if status in [MatchStatus.Finished, MatchStatus.Retired]:
            if len(driver.find_elements_by_xpath("//table[@id='parts']/tbody/tr[2]/td[2]/strong")) == 1:
                match["p1_wins"] = True
            elif len(driver.find_elements_by_xpath("//table[@id='parts']/tbody/tr[3]/td[2]/strong")) == 1:
                match["p1_wins"] = False

            duration_elem = driver.find_element_by_xpath("//tr[1]/td[@class='score'][1]").text
            duration_regex = re.search("([0-9]+):([0-9]+)", duration_elem)
            match["minutes"] = int(duration_regex.group(1)) * 60 + int(duration_regex.group(2))

            match["p1_s1_gms"] = find_gms_value(1, 1, driver)
            match["p1_s2_gms"] = find_gms_value(1, 2, driver)
            match["p1_s3_gms"] = find_gms_value(1, 3, driver)
            match["p1_s4_gms"] = find_gms_value(1, 4, driver)
            match["p1_s5_gms"] = find_gms_value(1, 5, driver)

            match["p1_tb1_score"] = find_tb_score(1, 1, driver)
            match["p1_tb2_score"] = find_tb_score(1, 2, driver)
            match["p1_tb3_score"] = find_tb_score(1, 3, driver)
            match["p1_tb4_score"] = find_tb_score(1, 4, driver)
            match["p1_tb5_score"] = find_tb_score(1, 5, driver)

            match["p2_s1_gms"] = find_gms_value(2, 1, driver)
            match["p2_s2_gms"] = find_gms_value(2, 2, driver)
            match["p2_s3_gms"] = find_gms_value(2, 3, driver)
            match["p2_s4_gms"] = find_gms_value(2, 4, driver)
            match["p2_s5_gms"] = find_gms_value(2, 5, driver)

            match["p2_tb1_score"] = find_tb_score(2, 1, driver)
            match["p2_tb2_score"] = find_tb_score(2, 2, driver)
            match["p2_tb3_score"] = find_tb_score(2, 3, driver)
            match["p2_tb4_score"] = find_tb_score(2, 4, driver)
            match["p2_tb5_score"] = find_tb_score(2, 5, driver)

            driver.find_element_by_id("a-match-statistics").click()
            time.sleep(0.5)

            stat_elem = driver.find_element_by_id("tab-statistics-0-statistic")
            row_elements = stat_elem.find_elements_by_class_name("statRow")

            stat_labels = []
            p1_stats = []
            p2_stats = []
            for row_elem in row_elements:
                stat_label = row_elem.find_element_by_class_name("statText--titleValue").text
                stat_labels.append(stat_label)
                p1_stats.append(row_elem.find_element_by_class_name("statText--homeValue").text)
                p2_stats.append(row_elem.find_element_by_class_name("statText--awayValue").text)

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
        log("scrap_match", "Error while scraping match id '{}'".format(match_id))
        print(type(ex))
        match = None

    driver.quit()
    return match


def create_match(match, matches):
    for attribute in get_match_ordered_attributes():
        if attribute not in match.index:
            match[attribute] = None

    match = match[get_match_ordered_attributes()]

    match_df = pd.DataFrame(match).T
    match_df = match_df.astype(get_match_dtypes())

    matches = pd.concat([matches, match_df])
    matches.reset_index(drop=True, inplace=True)

    return matches


def update_match(match, matches):
    for attribute in get_match_ordered_attributes():
        if attribute not in match.index:
            match[attribute] = None

    match = match[get_match_ordered_attributes()]

    """match_df = pd.DataFrame(match).T
    match_df = match_df.astype(get_match_dtypes)"""

    index_match = matches.index[matches["match_id"] == match["match_id"]].tolist()[0]
    for elem in matches.columns:
        matches.at[index_match, elem] = match[elem]

    return matches


def delete_match(match_id, matches):
    index_match = matches.index[matches["match_id"] == match_id].tolist()[0]


def scrap_matches(driver, players, tournaments, matches, matches_date):
    matches_date = datetime.now()
    driver = get_chrome_driver()
    match_url = "https://www.flashscore.com/tennis"
    driver.get(match_url)
    # time.sleep(1)
    datepick = driver.find_element_by_class_name('calendar__datepicker')
    datepickdate = driver.find_element_by_xpath("//div[@class='calendar__datepicker--dates']/div[2]")
    yesterday = driver.find_element_by_class_name('calendar__nav')
    # yesterday.click()
    # TODO delete prev lines

    tournament = None
    names = []
    elements = driver.find_elements_by_xpath("//div[@class='sportName tennis']/div")
    for elem in elements:
        if element_has_class(elem, "event__header"):
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
                    tournament = scrap_tournament(tournament_matched, matches_date)
                    if tournament is not None:
                        print("updating tournament {0}".format(tournament["flash_id"]))
                        # update_tournaments(tournaments, tournament)
                else:
                    # Tournament exists and is up-to-date
                    tournament = tournament_matched

            else:
                # New tournament to be scrapped
                print("Should scrap new tournament '{0}'".format(tournament_name))
                # TODO scrap new tournament
                # create_tournament(tournament_name)
                tournament = None
                continue

        else:
            # Match row
            if tournament is None:
                # Match is not to be retrieved
                continue

            elem_id = elem.get_attribute("id")
            match_id_regex = re.search("^._._(.*)$", elem_id)
            match_id = match_id_regex.group(1)

            match_status = None
            if element_has_class(elem, "event__match--live"):
                match_status = MatchStatus.LIVE
            else:
                try:
                    elem.find_element_by_class_name("event__time")
                    # Match is scheduled
                    match_status = MatchStatus.SCHEDULED
                except NoSuchElementException:
                    # Match is not scheduled
                    pass

            if match_status is None:
                status_str = elem.find_element_by_class_name("event__stage--block").text
                if status_str == "Finished":
                    match_status = MatchStatus.Finished
                elif status_str == "Finished\n(retired)":
                    match_status = MatchStatus.Retired
                elif status_str == "Walkover)":
                    match_status = MatchStatus.Walkover

            if match_status is None:
                print("Status not found for match '{0}'".format(match_id))
                continue

            match_search = matches[matches["match_id"] == match_id]

            if len(match_search) == 1:
                # Match exists
                match_found = match_search.iloc[0]

                if MatchStatus[match_found["status"]] not in [MatchStatus.Finished, MatchStatus.Retired]:
                    # Match is not recorded as 'finished'
                    if match_status in [MatchStatus.Finished, MatchStatus.Retired]:
                        # Match is truely finished
                        match = scrap_match_flashscore(match_id, match_status, players, tournaments)
                        matches = update_match(match, matches)
                    elif match_status == MatchStatus.Walkover:
                        # Match has been canceled
                        matches = delete_match(match_id, matches)
                        pass
                    elif match_status == MatchStatus.Scheduled:
                        # Updating match datetime if changed
                        time_elem = elem.find_element_by_class_name("event__time").text
                        time_regex = re.search(r"(\d{2}):(\d{2})$", time_elem)
                        hour = int(time_regex.group(1))
                        minute = int(time_regex.group(2))
                        match_date = datetime(matches_date.year, matches_date.month, matches_date.day, hour, minute)

                        if match_found["datetime"] != match_date:
                            match_found["datetime"] = match_date
                            matches = update_match(match_found, matches)

                    else:
                        # TODO (pas prioritaire) gérer update match live
                        pass

            else:
                # Match doesn't exist
                match = None
                if match_status in [MatchStatus.Scheduled, MatchStatus.Finished, MatchStatus.Retired]:
                    # Scrap match preview
                    match = scrap_match_flashscore(match_id, match_status, players, tournaments)
                    matches = create_match(match, matches)

    driver.quit()


class MatchEncoder(JSONEncoder):
    def default(self, obj):
        # print(type(obj))
        if pd.isna(obj):
            return None
        elif isinstance(obj, datetime):
            return {"$date": obj.timestamp() * 1000}
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, np.object):
            print("is_np_obj")
            return str(obj)
        else:
            print("is_else")
            return obj.__dict__


def get_matches_json(matches):
    return loads(MatchEncoder().encode(matches.to_dict('records')))


def record_matches(matches):
    mongo_cli = pymongo.MongoClient(MONGO_CLIENT)
    database = mongo_cli["tennis"]
    collection = database["matches"]

    matches_json = get_matches_json(matches)
    result = collection.insert_many(matches_json)

    return result.acknowledged


def retrieve_matches():
    mongo_cli = pymongo.MongoClient(MONGO_CLIENT)
    database = mongo_cli["tennis"]
    collection = database["matches"]

    matches = pd.DataFrame(list(collection.find({}, {'_id': False})))

    return matches

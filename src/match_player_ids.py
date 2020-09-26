import pandas as pd
import re
import time
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException


def scrap_player_id(player_name):
    atptour_name = atptour_id = None
    driver = webdriver.Chrome('/home/davy/Drivers/chromedriver')
    match_url = 'https://www.atptour.com/en/search-results/players?searchTerm={}'.format(player_name)
    driver.get(match_url)
    time.sleep(1)  # Wait 1 sec to avoid IP being banned for scrapping
    try:
        element = driver.find_element_by_xpath("//table[@class='player-results-table']/tbody/tr[1]/td[4]/a")
        atptour_name = element.text
        href = element.get_attribute("href")
        href_regex = re.search(".+/(.*)/overview$", href)
        atptour_id = href_regex.group(1)

    except NoSuchElementException:
        print("Player not found: {0}".format(player_name))

    driver.quit()

    return atptour_name, atptour_id


def search_player(first_name, last_name, players):
    return players.loc[(players["first_name"] == first_name.lower().replace("-", " ")) &
                       (players["last_name"].str.contains(last_name.lower()))]


def match_player(p_id, full_name, players, player_ids, new_players_to_scrap_ids):
    if p_id not in player_ids:
        my_man = None
        matched = re.search("(.*) (.+)$", full_name)

        if matched:
            my_man = search_player(matched.group(1), matched.group(2), players)
        else:
            print("NO MATCH: {}".format(full_name))

        atp_id = None

        if len(my_man) == 0:
            matched = re.search("(.*) (.+ .+)$", full_name)
            if matched:
                my_man = search_player(matched.group(1), matched.group(2), players)

        if len(my_man) == 0:
            matched = re.search("(.*) (.+ .+ .+)$", full_name)
            if matched:
                my_man = search_player(matched.group(1), matched.group(2), players)

        if len(my_man) == 0:
            atptour_name, atptour_id = scrap_player_id(full_name)
            if atptour_name is not None and atptour_id is not None:
                new_players_to_scrap_ids.append(atptour_id)
                atp_id = atptour_id
            else:
                atp_id = "NO MATCH " + full_name

        elif len(my_man) > 1:
            atp_id = "MULTIPLE MATCH " + full_name
        else:
            atp_id = my_man.iloc[0]["player_id"]

        player_ids[p_id] = atp_id

        return atp_id

    else:
        return player_ids[p_id]


def get_player_ids(players_in_matches_dataset):
    start_time = time.time()

    players = pd.read_csv("../datasets/atp_players.csv")
    players["first_name"] = [row.lower().replace("-", " ").replace("'", "") for row in players["first_name"]]
    players["last_name"] = [row.lower().replace("-", " ").replace("'", "") for row in players["last_name"]]

    player_ids = {}
    new_players_to_scrap_ids = []

    winner_atp_ids = [match_player(row[0], row[1], players, player_ids, new_players_to_scrap_ids) for row in
                      players_in_matches_dataset.to_numpy()]
    loser_atp_ids = [match_player(row[2], row[3], players, player_ids, new_players_to_scrap_ids) for row in
                     players_in_matches_dataset.to_numpy()]

    # player_atp_ids = [matchPlayer(row[0], row[1], players, player_ids, new_players_to_scrap_ids)
    # for row in players_in_matches_dataset.to_numpy()]

    print("---getPlayerIds  %s seconds ---" % (time.time() - start_time))
    return winner_atp_ids, loser_atp_ids, new_players_to_scrap_ids
    # return (player_atp_ids, new_players_to_scrap_ids)


def retrieve_missing_id(player_id, atptour_id, player_ids_manual_collect):
    if atptour_id.startswith("NO MATCH") or atptour_id.startswith("MULTIPLE MATCH"):
        new_id = player_ids_manual_collect.loc[player_id][0]
        return new_id
    else:
        return atptour_id


def retrieve_missing_ids(dataset):
    # I manually searched corresponding player on atptour.com and saved their corresponding ids in a csv file 
    # csv file is being imported
    player_ids_manual_collect = pd.read_csv("../datasets/player_ids_matching_manual_collect.csv", index_col="id")

    p1_ids_dataframe = dataset.apply(
        lambda row: retrieve_missing_id(row["winner_id"], row["p1_id"], player_ids_manual_collect), axis=1)
    p2_ids_dataframe = dataset.apply(
        lambda row: retrieve_missing_id(row["loser_id"], row["p2_id"], player_ids_manual_collect), axis=1)

    return p1_ids_dataframe, p2_ids_dataframe, player_ids_manual_collect


def scrap_players(players_ids):
    # TODO
    return

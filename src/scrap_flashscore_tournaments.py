import time
from selenium import webdriver
import re
import configparser
import pymongo
import pandas as pd

config = configparser.ConfigParser()
config.read("src/config.ini")
MONGO_CLIENT = config['mongo']['client']


def scrap_flash_score_tournaments(tournaments):
    driver = webdriver.Chrome('/home/davy/Drivers/chromedriver')
    match_url = 'https://www.flashscore.com/tennis/'
    driver.get(match_url)
    time.sleep(0.5)
    
    # ATP
    names = []
    formatted_names = []
    categories = []
    
    el = driver.find_element_by_xpath("//li[@id='lmenu_5724']/a")
    driver.execute_script("arguments[0].click();", el)
    time.sleep(1)
    
    elements = driver.find_elements_by_xpath("//li[@id='lmenu_5724']/ul/li/a")
      
    for element in elements:
        names.append(str.lower(element.get_property("text")))
        
        link = element.get_attribute("href")
        formatted_name = re.search("atp-singles/(.+)/$", link).group(1)
        formatted_names.append(formatted_name)

    categories += ["atp"] * len(elements)
        
    # ITF
    el = driver.find_element_by_xpath("//li[@id='lmenu_5733']/a")
    driver.execute_script("arguments[0].click();", el)
    time.sleep(1)
    
    elements = driver.find_elements_by_xpath("//li[@id='lmenu_5733']/ul/li/a")
    
    for element in elements:
        names.append(element.get_property("text"))
        
        link = element.get_attribute("href")
        formatted_name = re.search("itf-men-singles/(.+)/$", link).group(1)
        formatted_names.append(formatted_name)

    categories += ["itf"] * len(elements)

    # Challenger
    el = driver.find_element_by_xpath("//li[@id='lmenu_5729']/a")
    driver.execute_script("arguments[0].click();", el)
    time.sleep(1)

    elements = driver.find_elements_by_xpath("//li[@id='lmenu_5729']/ul/li/a")

    for element in elements:
        names.append(element.get_property("text"))

        link = element.get_attribute("href")
        formatted_name = re.search("challenger-men-singles/(.+)/$", link).group(1)
        formatted_names.append(formatted_name)

    categories += ["challenger"] * len(elements)

    driver.quit()

    not_found = []

    for tour in tournaments:
        if tour.formatted_name in formatted_names:
            index = formatted_names.index(tour.formatted_name)
            setattr(tour, "flashscore_id", tour.formatted_name)
            setattr(tour, "category", categories[index])
        elif tour.name in names:
            index = names.index(tour.name)
            setattr(tour, "flashscore_id", formatted_names[index])
            setattr(tour, "category", categories[index])
        else:
            setattr(tour, "flashscore_id", -1)
            setattr(tour, "category", "atp")
            not_found.append(tour)

    tour_collect = pd.read_csv("datasets/tournaments_flashscore_manual_collect.csv")

    for tour in tournaments:
        if tour.flashscore_id == -1:
            result = tour_collect[tour_collect["atptour_id"] == tour.atptour_id]
            if len(result.index) == 1:
                setattr(tour, "flashscore_id", result.iloc[0]["flashscore_id"])
                setattr(tour, "category", result.iloc[0]["category"])

    return tournaments


def add_flashscore_tournament_id(tour_atptour_id, tournaments):
    for tournament in tournaments:
        if tournament.atptour_id == tour_atptour_id:
            return tournament.flashscore_id
    print("tournament not found: " + tour_atptour_id)
    return None


def add_flashscore_tournament_ids(dataset, tournaments):
    dataset["tournament_flashscore_id"] = dataset.apply(lambda row: add_flashscore_tournament_id(row["tournament_id"], tournaments), axis=1)
    return dataset

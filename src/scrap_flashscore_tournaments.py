import time
from selenium import webdriver
import re
import configparser
import pymongo

config = configparser.ConfigParser()
config.read("src/config.ini")
MONGO_CLIENT = config['mongo']['client']


def scrap_flash_score_tournaments():
    driver = webdriver.Chrome('/home/davy/Drivers/chromedriver')
    match_url = 'https://www.flashscore.com/tennis/'
    driver.get(match_url)
    time.sleep(0.5)
    
    # ATP
    names = []
    formatted_names = []
    
    el = driver.find_element_by_xpath("//li[@id='lmenu_5724']/a")
    driver.execute_script("arguments[0].click();", el)
    time.sleep(1)
    
    elements = driver.find_elements_by_xpath("//li[@id='lmenu_5724']/ul/li/a")
      
    for element in elements:
        names.append(str.lower(element.get_property("text")))
        
        link = element.get_attribute("href")
        formatted_name = re.search("atp-singles/(.+)/$", link).group(1)
        formatted_names.append(formatted_name)
        
    # ITF
    el = driver.find_element_by_xpath("//li[@id='lmenu_5733']/a")
    driver.execute_script("arguments[0].click();", el);
    time.sleep(1)
    
    elements = driver.find_elements_by_xpath("//li[@id='lmenu_5733']/ul/li/a")
    
    for element in elements:
        names.append(element.get_property("text"))
        
        link = element.get_attribute("href")
        formatted_name = re.search("itf-men-singles/(.+)/$", link).group(1)
        formatted_names.append(formatted_name)
        
    driver.quit()

    myclient = pymongo.MongoClient(MONGO_CLIENT)
    mydb = myclient["tennis"]
    mycol = mydb["tournaments"]
    tournaments = mycol.find({})
    not_found = []
    matched = []
    for tour in tournaments:
        if tour["formatted_name"] in formatted_names:
            matched.append([tour["id"], tour["formatted_name"]])
        elif tour["name"] in names:
            index = names.index(tour["name"])
            matched.append([tour["id"], formatted_names[index]])
        else:
            not_found.append(tour["formatted_name"])

    matched.append([568, 'st-petersburg'])
    matched.append([440, 'hertogenbosch'])
    matched.append([520, 'french-open'])
    matched.append([96, 'olympic-games'])
    matched.append([6815, 'delray-beach'])
    matched.append([479, 'geneva'])
    matched.append([605, 'finals-londres'])
    matched.append([65, 'poertschach'])
    matched.append([7696, 'next-gen-finals-milan'])
    matched.append([306, 'st-poelten'])

    for matched_tour in matched:
        myquery = {"id": matched_tour[0]}
        newvalues = {"$set": {"flashscore_name": matched_tour[1]}}
        x = mycol.update_many(myquery, newvalues)

import time
from selenium import webdriver
import re
import configparser
import pymongo


config = configparser.ConfigParser()
config.read("config.ini")
MONGO_CLIENT = config['mongo']['client']

def scrapFlashScoreTournaments():
    driver = webdriver.Chrome('/home/davy/Drivers/chromedriver')
    match_url  = 'https://www.flashscore.com/tennis/'
    driver.get(match_url);
    time.sleep(0.5)
    
    # ATP
    names = []
    formatted_names = []
    
    el = driver.find_element_by_xpath("//li[@id='lmenu_5724']/a")
    driver.execute_script("arguments[0].click();", el);
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
    notFound = []
    for tour in tournaments:
        if tour["formatted_name"] not in formatted_names and str.lower(tour["name"]) not in names : 
            notFound.append(tour["formatted_name"])
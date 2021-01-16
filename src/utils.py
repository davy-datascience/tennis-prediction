import configparser

from pymongo import MongoClient
from selenium import webdriver


def element_has_class(web_element, class_name):
    return class_name in web_element.get_attribute("class").split()


def get_chrome_driver(driver=None):
    """Get a new chrome driver or replace it to pass through DDOS protection"""
    if driver is not None:
        driver.quit()
    driver = webdriver.Chrome('/home/davy/Drivers/chromedriver')
    return driver


def get_mongo_client():
    config = configparser.ConfigParser()
    config.read("src/config.ini")
    mongo_client = config['mongo']['client']
    return MongoClient(mongo_client)

import configparser
import pandas as pd
import numpy as np
import os

from pymongo import MongoClient
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from numba import jit
from bson.json_util import loads
from json import JSONEncoder
from datetime import datetime


def element_has_class(web_element, class_name):
    return class_name in web_element.get_attribute("class").split()


def get_chrome_driver(driver=None):
    """Get a new chrome driver or replace it to pass through DDOS protection"""

    # Set log level to 'warning'
    os.environ['WDM_LOG_LEVEL'] = '30'

    if driver is not None:
        # Quit existing driver
        driver.quit()

    driver = None

    # Instantiate new chrome driver
    try:
        chrome_options = webdriver.ChromeOptions()
        # chrome_options.add_argument('--remote-debugging-port=9222')

        # Set 'user-agent' to pass through DDOS protection while --headless
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.125 Safari/537.36")
        chrome_options.add_argument('--headless')

        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')

        driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)

    except Exception as ex:
        print("CHROME DRIVER CRASHED !!!")
        print(ex)

    return driver


def get_mongo_client():
    config = configparser.ConfigParser()
    config.read("config.ini")
    mongo_client = config['mongo']['client']
    return MongoClient(mongo_client)


class PandasEncoder(JSONEncoder):
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
            return str(obj)
        else:
            return obj.__dict__


def get_dataframe_json(dataframe):
    return loads(PandasEncoder().encode(dataframe.to_dict('records')))


@jit
def add_with_numba(a, b):
    return a + b


@jit
def substract_with_numba(a, b):
    return a - b


@jit
def divide_with_numba(a, b):
    """ Divide one column by an other column of a dataframe with increased performance thanks to vectorization """
    return a / b

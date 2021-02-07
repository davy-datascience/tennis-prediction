import configparser

from pymongo import MongoClient
from selenium import webdriver
from numba import jit


def element_has_class(web_element, class_name):
    return class_name in web_element.get_attribute("class").split()


def get_chrome_driver(driver=None):
    """Get a new chrome driver or replace it to pass through DDOS protection"""

    # Get path of chrome driver
    config = configparser.ConfigParser()
    config.read("src/config.ini")
    chrome_driver_path = config['webdriver']['path']

    if driver is not None:
        # Quit existing driver
        driver.quit()

    driver = None

    # Instantiate new chrome driver
    try:
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--remote-debugging-port=9222')
        # chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        driver = webdriver.Chrome(chrome_driver_path, options=chrome_options)
        # driver = webdriver.Chrome(chrome_driver_path)
    except Exception as ex:
        print("CHROME DRIVER CRASHED !!!")
        print(ex)

    return driver


def get_mongo_client():
    config = configparser.ConfigParser()
    config.read("src/config.ini")
    mongo_client = config['mongo']['client']
    return MongoClient(mongo_client)


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

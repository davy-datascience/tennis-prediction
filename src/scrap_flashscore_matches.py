from selenium import webdriver
import re
import time
from selenium.common.exceptions import NoSuchElementException


def scrap_match_flashscore(match_id):
    try:
        driver = webdriver.Chrome('/home/davy/Drivers/chromedriver')
        # match_url = "https://www.flashscore.com/match/W6RCsxJR/#match-summary"
        match_url = "https://www.flashscore.com/match/W6RCsxJR/#match-statistics"
        driver.get(match_url)
        time.sleep(1)

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
            return None

        p1_ace = int(driver.find_element_by_xpath(root + "div[2]/div[1]/div[1]").text)
        p1_df = int(driver.find_element_by_xpath(root + "div[3]/div[1]/div[1]").text)

        p1_svpt_elem = driver.find_element_by_xpath(root + "div[17]/div[1]/div[1]").text
        p1_svpt_regex = re.search(r"^([0-9]+)% \(([0-9]+)/([0-9]+)$")
        p1_svpt = p1_svpt_regex.group(3)
        p1_svpt_won = p1_svpt_regex.group(2)
        p1_svpt_ratio = p1_svpt_regex.group(1) / 100

        p1_1st_elem = driver.find_element_by_xpath(root + "div[4]/div[1]/div[1]").text
        p1_1st_regex = re.search(r"^([0-9]+)% \(([0-9]+)/([0-9]+)$")
        p1_1st_in = p1_1st_regex.group(3)
        p1_1st_won = p1_1st_regex.group(2)
        p1_1st_ratio = p1_1st_regex.group(1) / 100

        p1_2nd_elem = driver.find_element_by_xpath(root + "div[5]/div[1]/div[1]").text
        p1_2nd_regex = re.search(r"^([0-9]+)% \(([0-9]+)/([0-9]+)$")
        p1_2nd_pt = p1_2nd_regex.group(3)
        p1_2nd_won = p1_2nd_regex.group(2)
        p1_2nd_ratio = p1_2nd_regex.group(1) / 100

        # = int(driver.find_element_by_xpath(root + "div[2]/div[1]/div[1]").text)
        # p1_bp_saved = int(driver.find_element_by_xpath(root + "div[2]/div[1]/div[1]").text)
        # p1_bp_faced = int(driver.find_element_by_xpath(root + "div[2]/div[1]/div[1]").text)

        p2_ace = int(driver.find_element_by_xpath(root + "div[2]/div[1]/div[3]").text)
        p2_df = int(driver.find_element_by_xpath(root + "div[3]/div[1]/div[3]").text)

    except Exception as ex:
        print("Error while scraping match id '{}'".format(match_id))
        print(type(ex))
        return None

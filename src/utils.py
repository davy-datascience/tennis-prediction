from selenium import webdriver


def element_has_class(web_element, class_name):
    return class_name in web_element.get_attribute("class").split()


def get_chrome_driver(driver=None):
    """Get a new chrome driver or replace it to pass through DDOS protection"""
    if driver is not None:
        driver.quit()
    driver = get_chrome_driver()
    return driver

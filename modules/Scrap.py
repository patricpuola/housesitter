#!/usr/bin/python3
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
import os, time, atexit
import setup
from db import DBCon

class Scrap:
    VALID_BROWSERS = ["chrome","firefox"]
    browser = "chrome"

    BROWSER_LEFT = 0
    BROWSER_RIGHT = 1
    
    # In non-headless mode browsers are split to left and right on the desktop
    active_webdrivers = {BROWSER_LEFT:[], BROWSER_RIGHT:[]}

    available_width = 0
    available_height = 0

    exit_process_registered = False

    @classmethod
    def setBrowser(cls, browser):
        if browser.lower() not in cls.VALID_BROWSERS:
            return False
        cls.browser = browser.lower()

    @classmethod
    def getChromeOptions(cls):
        chrome_options = webdriver.ChromeOptions()
        if setup.getConfig()['headless']:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        return chrome_options

    @classmethod
    def getWebDriver(cls, side = BROWSER_LEFT):
        cls.checkExitFunction()
        if cls.browser == 'chrome':
            chrome_path = setup.getWebDriverPath(cls.browser)
            chrome_options = cls.getChromeOptions()
            new_driver = webdriver.Chrome(chrome_path, options=chrome_options)
            cls.active_webdrivers[side].append(new_driver)
            return new_driver
    
    @classmethod
    def initWebdriverWindows(cls):  
        #TODO: test if headless needs window postioning
        if setup.getConfig()['headless']:
            return

        testing_driver = None

        # Window positioning and initial resize to avoid maximized window problems
        for driver in cls.active_webdrivers[cls.BROWSER_LEFT]:
            driver.set_window_rect(height = 480, width = 640, x = 0, y = 0)
            if testing_driver is None:
                testing_driver = driver
        for driver in cls.active_webdrivers[cls.BROWSER_RIGHT]:
            driver.set_window_rect(height = 480, width = 640, x = 0, y = 0)
            if testing_driver is None:
                testing_driver = driver

        # TODO: necessary?
        time.sleep(2)

        testing_driver.maximize_window()
        cls.available_width = testing_driver.get_window_size()['width']
        cls.available_height = testing_driver.get_window_size()['height']

        for driver in cls.active_webdrivers[cls.BROWSER_LEFT]:
            driver.set_window_rect(height = cls.available_height, width = cls.available_width/2, x = 0, y = 0)
        for driver in cls.active_webdrivers[cls.BROWSER_RIGHT]:
            driver.set_window_rect(height = cls.available_height, width = cls.available_width/2, x = cls.available_width, y = 0)
        return
    
    @classmethod
    def checkExitFunction(cls):
        if not cls.exit_process_registered:
            atexit.register(cls.shutdownDrivers)
            cls.exit_process_registered = True
        return


    @classmethod
    def shutdownDrivers(cls):
        for driver in cls.active_webdrivers[cls.BROWSER_LEFT]:
            driver.quit()
        for driver in cls.active_webdrivers[cls.BROWSER_RIGHT]:
            driver.quit()
        return


    @classmethod
    def buildXpathSelector(cls, tags, text):
        self_tags = list(map(lambda tag: "self::"+tag, tags))
        return """//*[{}][contains(text(), '{}')]""".format(" or ".join(self_tags), text)

    # Method to try to find and remove blocking popups and ads (elementClickInterfenrenceException)
    @classmethod
    def checkAndRemoveBlocker(cls, driver, title_text, accept_text, title_tag = None, accept_tag = None):
        valid_title_tags = ['h1', 'h2', 'div', 'span']
        valid_accept_tags = ['button', 'div', 'a']
        if title_tag is not None:
            valid_title_tags = [title_tag]
        if accept_tag is not None:
            valid_accept_tags = [accept_tag]
        
        try:
            title_element = driver.find_element_by_xpath(cls.buildXpathSelector(valid_title_tags, title_text))
            accept_element = driver.find_element_by_xpath(cls.buildXpathSelector(valid_accept_tags, accept_text))
        except NoSuchElementException:
            return
        accept_element.click()
    
    # Pass elements as list of tuples that consist of By -identifier type and the identifier value [(By.ById, "main_container"),(By.ByName, "accept-button")]
    # By.CLASS_NAME
    # By.CSS_SELECTOR
    # By.ID
    # By.LINK_TEXT
    # By.NAME 
    # By.PARTIAL_LINK_TEXT
    # By.TAG_NAME
    # By.XPATH
    @classmethod
    def waitFor(cls, driver, element_tuples, timeout_seconds):
        if type(element_tuples) == tuple:
            element_tuples = [element_tuples]

        wait_for_elements = []
        for type_identifier in element_tuples:
            wait_for_elements.append(expected_conditions.presence_of_element_located(type_identifier))
        
        try:
            WebDriverWait(driver, timeout_seconds).until(*wait_for_elements)
        except TimeoutException:
            return False
        return True

    @classmethod
    def getTableCellByHeader(cls, driver, header_text, header_tag = None):
        valid_header_tags = ['th', 'td']
        if header_tag is not None:
            valid_header_tags = [header_tag]
        xpath = cls.buildXpathSelector(valid_header_tags, header_text)
        xpath += "/following::td"
        try:
            text = driver.find_element(By.XPATH, xpath).text.strip()
        except NoSuchElementException:
            return None

        if len(text) > 0:
            return text
        else:
            return None
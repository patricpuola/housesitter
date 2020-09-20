#!/usr/bin/python3
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
import os, time
import setup
from db import DBCon


class Scrap:
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
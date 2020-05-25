#!/usr/bin/python3
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.by import By
import os, time
import setup
from db import DBCon
import housing

class SiteScraper:
    listing_table_name = 'listings'
    ads = []

    def saveAd(self, listing: housing.Listing):
        with db.get().cursor() as cursor:
            pass

    @classmethod
    def getNewListingId(cls):
        with DBCon.get().cursor() as cursor:
            cursor.execute("SHOW TABLE STATUS LIKE '"+cls.listing_table_name+"'")
            result = cursor.fetchone()
            if result is None:
                return False
            else:
                return result["Auto_increment"]

    # Method to try to find and remove blocking popups and ads (ElementClickInterfenrenceException)
    @classmethod
    def removeBlocker(cls, driver, target):
        pass

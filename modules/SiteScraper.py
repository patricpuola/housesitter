#!/usr/bin/python3
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.by import By
import os, time
import setup
from abc import ABC, abstractmethod, abstractproperty


class SiteScraper(ABC):
    @abstractproperty
    ads = []

    @abstractmethod
    def saveAd():
        pass

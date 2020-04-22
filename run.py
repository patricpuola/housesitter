#!/usr/bin/python3
import sys
sys.path.insert(1, '/srv/scraper/modules')

from selenium import webdriver
from selenium.webdriver.common.keys import Keys

import vuokraovi_com

# Chrome init
chrome_path = r"/srv/res/chromedriver.81"
chrome_options = webdriver.ChromeOptions()
#chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
driver = webdriver.Chrome(chrome_path, options=chrome_options)

vuokraovi_com.getListings(driver)

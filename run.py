#!/usr/bin/python3
from selenium import webdriver
import modules.vuokraovi_com

chrome_path = r"/srv/res/chromedriver.81"
chrome_options = webdriver.ChromeOptions()
#chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
driver = webdriver.Chrome(chrome_path, options=chrome_options)

vuokraovi_com.getListings(driver)

#!/usr/bin/python3
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.by import By
import time

#debug
from pprint import pprint
from inspect import getmembers

def getListings(driver):
	driver.get("https://vuokraovi.com")
	timeout = 5

	try:
		search_box_present = expected_conditions.presence_of_element_located((By.XPATH, getXpath("search_box")))
		search_button_present = expected_conditions.presence_of_element_located((By.XPATH, getXpath("search_button")))
		WebDriverWait(driver, timeout).until(search_box_present, search_button_present)
	except TimeoutException:
		print("Vuokraovi.com timed out")
	finally:
		print("Vuokraovi.com frontpage loaded")

	driver.find_element_by_xpath(getXpath("location_deny")).send_keys(Keys.SPACE)
	driver.find_element_by_xpath(getXpath("cookie")).send_keys(Keys.SPACE)

	search_box = driver.find_element_by_xpath(getXpath("search_box"))
	search_button = driver.find_element_by_xpath(getXpath("search_button"))

	search_box.send_keys("Helsinki")

	try:
		autofill_filled = expected_conditions.presence_of_element_located((By.CSS_SELECTOR, "ul.ui-autocomplete > li"))
		WebDriverWait(driver, timeout).until(autofill_filled)
	except TimeoutException:
		print("List item timeout")
	finally:
		search_box.send_keys(Keys.ENTER)

	search_button.click()

	try:
		results_displayed = expected_conditions.presence_of_element_located((By.CLASS_NAME, "list-item-container"))
		WebDriverWait(driver, timeout).until(results_displayed)
	except:
		print("Result display timeout")
	finally:
		ads = driver.find_elements_by_class_name("list-item-container")

	i = 0
	for ad in ads:
		location = ad.location_once_scrolled_into_view
		size = ad.size

		ad_png = open('/srv/scraper/screenshots/ad_'+str(i)+'.png', 'bw+')
		ad_png.write(ad.screenshot_as_png)
		ad_png.close()

		print("Ilmoitus "+str(i)+":")
		print(ad.text)
		i += 1


def getXpath(item):
	items = {
		"cookie": """/html/body/div[1]/div/div/div[2]/div[1]/button""",
		"location_deny": """//*[@id="alma-data-policy-banner__accept-cookies-only"]""",
		"search_box": """//*[@id="inputLocationOrRentalUniqueNo"]""",
		"search_button": """//*[@id="frontPageSearchPanelRentalsForm"]/div[4]/div[1]/button""",
		"search_autofill": """//*[@id="ui-id-1"]"""
	}

	return items[item]

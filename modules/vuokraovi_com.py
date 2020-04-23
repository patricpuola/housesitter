#!/usr/bin/python3
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.by import By
import os, time
#import listing from housing

def getListings(driver):
	driver.get("https://vuokraovi.com")
	timeout = 5

	listings = []

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

	if not os.path.exists(r"ad_shots"):
		os.makedirs(r"ad_shots")

	page_nr = 0
	while (scrapeResultPage(driver, page_nr, listings)):
		driver.find_element_by_xpath(getXpath("next_result_page")).click()
		page_nr += 1
		if (page_nr > 2):
			break

def scrapeResultPage(driver, page_nr, listings):
	original_listings = len(listings)

	timeout = 5
	try:
		results_displayed = expected_conditions.presence_of_element_located((By.CLASS_NAME, "list-item-container"))
		WebDriverWait(driver, timeout).until(results_displayed)
	except:
		print("Result display timeout")
	finally:
		ads = driver.find_elements_by_class_name("list-item-container")

	for ad in ads:
		location = ad.location_once_scrolled_into_view

		img_index = len(listings)

		ad_png = open(r'ad_shots/vuokraovi_com_ad__'+img_index+'.png', 'bw+')
		ad_png.write(ad.screenshot_as_png)
		ad_png.close()

		print("\nAd "+str(i)+" of page "+str(page_nr+1)+":")
		lines = ad.text.split("\n")
		house_type, area_m2 = lines[0].split(',',1)
		layout = lines[1]
		rent = lines[2]
		location = lines[3]
		available = lines[4]

	return (original_listings < len(listings))


def getXpath(item):
	items = {
		"cookie": """/html/body/div[1]/div/div/div[2]/div[1]/button""",
		"location_deny": """//*[@id="alma-data-policy-banner__accept-cookies-only"]""",
		"search_box": """//*[@id="inputLocationOrRentalUniqueNo"]""",
		"search_button": """//*[@id="frontPageSearchPanelRentalsForm"]/div[4]/div[1]/button""",
		"search_autofill": """//*[@id="ui-id-1"]""",
		"next_result_page": """//*[@id="listContent"]/div[3]/div[3]/ul/li[9]/a"""
	}

	return items[item]

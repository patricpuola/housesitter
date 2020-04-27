#!/usr/bin/python3
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
import sys, os, time
import setup
from pprint import pprint
from housing import Cost, Listing

def getListings(driver, deep_driver):
	driver.get("https://vuokraovi.com")
	deep_driver.get("https://vuokraovi.com")
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

	deep_driver.find_element_by_xpath(getXpath("location_deny")).send_keys(Keys.SPACE)
	deep_driver.find_element_by_xpath(getXpath("cookie")).send_keys(Keys.SPACE)

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
	while (scrapeResultPage(driver, deep_driver, page_nr, listings)):
		driver.find_element_by_xpath(getXpath("next_result_page")).click()
		page_nr += 1

def scrapeResultPage(driver, deep_driver, page_nr, listings):
	original_listings = len(listings)

	timeout = 5
	try:
		results_displayed = expected_conditions.presence_of_element_located((By.CLASS_NAME, "list-item-container"))
		WebDriverWait(driver, timeout).until(results_displayed)
	except:
		print("Result display timeout")
	finally:
		ads = driver.find_elements_by_class_name("list-item-container")

	deepScrape = {}

	for ad in ads:
		ad_index = len(listings)

		url = ad.find_elements_by_class_name("list-item-link")[0].get_attribute("href")

		listing = Listing(url)

		if (setup.getConfig()['ad_screenshot_enabled'] and len(setup.getConfig()['ad_screenshot_directory']) > 0):
			ad.location_once_scrolled_into_view # Triggers scroll for screenshotting
			ad_png = open(r''+setup.getConfig()['ad_screenshot_directory']+'/vuokraovi_com_ad_'+str(ad_index)+'.png', 'bw+')
			ad_png.write(ad.screenshot_as_png)
			ad_png.close()

		lines = ad.text.split("\n")
		house_type_area_m2 = lines[0].split(',', 1)
		layout = lines[1]
		rent = lines[2]
		location = lines[3]
		available = lines[4]

		if len(house_type_area_m2) == 2:
			housing_type = house_type_area_m2[0].strip()
			living_space = house_type_area_m2[1].strip()
		else:
			housing_type = house_type_area_m2[0].strip()
			living_space = None

		listing.fill(ownership_type = Listing.TYPE_OWN_RENTAL, housing_type = housing_type, price = rent, living_space_m2 = living_space, layout = layout, availability = available)

		listings.append(listing)
		deepScrape[ad_index] = url

	for ad_index in deepScrape:
		url = deepScrape[ad_index]
		deep_driver.get(url)
		try:
			accordion_displayed = expected_conditions.presence_of_element_located((By.XPATH, getXpath("deep_accordion")))
			WebDriverWait(deep_driver, timeout).until(accordion_displayed)
		except:
			print("Deep result accordion display timeout")
		finally:
			pass

		try:
			description = deep_driver.find_element_by_xpath(getXpath("deep_description")).text
		except NoSuchElementException:
			description = None

		try:
			street_address = deep_driver.find_element_by_xpath(getXpath("deep_street_address")).text
		except NoSuchElementException:
			street_address = None

		try:
			zip, city = deep_driver.find_element_by_xpath(getXpath("deep_zip_and_city")).text.split(" ", 1)
		except NoSuchElementException:
			zip = None
			city = None

		try:
			condition = deep_driver.find_element_by_xpath(getXpath("deep_condition")).text
		except NoSuchElementException:
			condition = None

		try:
			build_year = deep_driver.find_element_by_xpath(getXpath("deep_build_year")).text
		except NoSuchElementException:
			build_year = None

		try:
			total_area = deep_driver.find_element_by_xpath(getXpath("deep_total_area")).text
		except NoSuchElementException:
			total_area = None

		try:
			floor_and_max_floor = deep_driver.find_element_by_xpath(getXpath("deep_floor_and_max_floor")).text.split("/", 1)

			if len(floor_and_max_floor) == 2:
				floor = floor_and_max_floor[0].strip()
				floor_max = floor_and_max_floor[1].strip()
			elif len(floor_and_max_floor) == 1:
				floor = floor_and_max_floor[0].strip()
		except NoSuchElementException:
			floor = None
			floor_max = None

		listings[ad_index].fill(street_address = street_address, zip = zip, city = city, floor = floor, floor_max = floor_max, condition = condition, total_space_m2 = total_area, build_year = build_year, description = description)

	for listing in listings:
		pprint(listing.__dict__)
	sys.exit('done for now')
	return (original_listings < len(listings))


def getXpath(item):
	items = {
		"cookie": """/html/body/div[1]/div/div/div[2]/div[1]/button""",
		"location_deny": """//*[@id="alma-data-policy-banner__accept-cookies-only"]""",
		"search_box": """//*[@id="inputLocationOrRentalUniqueNo"]""",
		"search_button": """//*[@id="frontPageSearchPanelRentalsForm"]/div[4]/div[1]/button""",
		"search_autofill": """//*[@id="ui-id-1"]""",
		"next_result_page": """//*[@id="listContent"]/div[3]/div[3]/ul/li[9]/a""",
		"deep_accordion": """//*[@id="accordion"]""",
		"deep_street_address": """//*[@id="collapseOne"]/div/table/tbody/tr[1]/td/span[1]""",
		"deep_zip_and_city": """//*[@id="collapseOne"]/div/table/tbody/tr[1]/td/span[2]""",
		"deep_floor_and_max_floor": """//th[contains(text(), 'Kerros:')]/following::td""",
		"deep_condition": """//th[contains(text(), 'Yleiskunto:')]/following::td""",
		"deep_build_year": """//th[contains(text(), 'Rakennusvuosi:')]/following::td""",
		"deep_total_area": """//th[contains(text(), 'Kokonaispinta-ala:')]/following::td""",
		"deep_description": """//*[@id="itempageDescription"]"""
	}

	return items[item]

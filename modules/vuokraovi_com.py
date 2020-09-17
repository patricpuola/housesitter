#!/usr/bin/python3
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
import sys, os, time, re
import setup
from pprint import pprint
from housing import Cost, Listing

def getListings(driver, deep_driver):
	driver.get("https://vuokraovi.com")
	deep_driver.get("https://vuokraovi.com")
	time.sleep(5)
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
		url = re.sub('\?.*$', '', url)

		listing = Listing('vuokraovi.com', url)

		if (setup.getConfig()['screenshot_enabled'] and len(setup.getConfig()['screenshot_directory']) > 0):
			ad.location_once_scrolled_into_view # Triggers scroll for screenshotting
			ad_png = open(r''+setup.getConfig()['screenshot_directory']+'/vuokraovi_com_ad_'+str(listing.id)+'.png', 'bw+')
			ad_png.write(ad.screenshot_as_png)
			ad_png.close()

		listing.fill(ownership_type = Listing.TYPE_OWN_RENTAL)

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
			total_space_m2 = deep_driver.find_element_by_xpath(getXpath("deep_total_space_m2")).text
		except NoSuchElementException:
			total_space_m2 = None

		try:
			agency = deep_driver.find_element_by_xpath(getXpath("deep_agency")).text
		except NoSuchElementException:
			agency = None

		try:
			housing_type = deep_driver.find_element_by_xpath(getXpath("deep_housing_type")).text
		except NoSuchElementException:
			housing_type = None

		try:
			price = deep_driver.find_element_by_xpath(getXpath("deep_price")).text
		except NoSuchElementException:
			price = None

		try:
			layout = deep_driver.find_element_by_xpath(getXpath("deep_layout")).text
		except NoSuchElementException:
			layout = None

		try:
			availability = deep_driver.find_element_by_xpath(getXpath("deep_availability")).text
		except NoSuchElementException:
			availability = None

		try:
			living_space_m2 = deep_driver.find_element_by_xpath(getXpath("deep_living_space_m2")).text
		except NoSuchElementException:
			living_space_m2 = None

		try:
			floor_and_max_floor_str = deep_driver.find_element_by_xpath(getXpath("deep_floor_and_max_floor")).text
			floor_and_max_floor = floor_and_max_floor_str.split("/", 1)

			if len(floor_and_max_floor) == 2:
				floor = floor_and_max_floor[0].strip()
				floor_max = floor_and_max_floor[1].strip()
			elif len(floor_and_max_floor) == 1:
				floor = floor_and_max_floor[0].strip()
				floor_max = None
		except NoSuchElementException:
			floor = None
			floor_max = None

		listings[ad_index].fill(housing_type = housing_type, street_address = street_address, zip = zip, city = city, price = price, layout = layout, availability = availability, floor = floor, floor_max = floor_max, condition = condition, living_space_m2 = living_space_m2, total_space_m2 = total_space_m2, build_year = build_year, description = description, agency = agency)
		listing_costs = getCosts(deep_driver)
		for new_cost in listing_costs:
			listings[ad_index].addCost(new_cost)
		listings[ad_index].save()

		# Fetch images
		try:
			image_gallery_link = deep_driver.find_element_by_xpath(getXpath("deep_image_gallery_link")).get_attribute('href')
			deep_driver.get(image_gallery_link)
			image_elements = deep_driver.find_elements_by_css_selector(".show-images__images > a")
			for image in image_elements:
				listings[ad_index].addImage(image.get_attribute('href'))
		except NoSuchElementException:
			pass

	for listing in listings:
		pass
	sys.exit('done for now')
	return (original_listings < len(listings))

def getCosts(deep_driver):
	costs = []
	try:
		water_cost_text = deep_driver.find_element_by_xpath(getXpath("deep_cost_water")).text
		water_cost = Cost(type = Cost.TYPE_WATER, description = 'Vesimaksu', amount_EUR = 0.0, period = Cost.PERIOD_UNDEFINED)
		# TODO: fix this shit
		water_cost.amount, water_cost.period, water_cost.flags = parseCostOccurrence(water_cost_text)
		costs.append(water_cost)
	except NoSuchElementException:
		pass
	return costs

def parseCostOccurrence(text):
	period = None
	flags = Cost.NO_FLAGS
	amount = 0.0
	text_parts = re.split(r'\s+', text);
	for part in text_parts:
		sub_text = re.split(r'\\', part)
		for subpart in sub_text:
			if re.match(r'^kk$', subpart, flags=re.IGNORECASE):
				period = Cost.PERIOD_MONTHLY
			if re.match(r'^hlö$', subpart, flags=re.IGNORECASE):
				flags = flags | Cost.FLAG_MULTIPLY_PER_RESIDENT
			if re.match(r'\d+[\.,]\d+', subpart):
				amount = re.sub(r'[\D\.,]', '', subpart)
				amount = re.sub(r',', '.', amount)
	return (amount, period, flags)

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
		"deep_total_space_m2": """//th[contains(text(), 'Kokonaispinta-ala:')]/following::td""",
		"deep_description": """//*[@id="itempageDescription"]""",
		"deep_agency": """//*[@id="rentalContactInfo"]/p/b/a""",
		"deep_housing_type" : """//th[contains(text(), 'Tyyppi:')]/following::td""",
		"deep_price" : """//th[contains(text(), 'Vuokra:')]/following::td""",
		"deep_layout" : """//th[contains(text(), 'Kuvaus:')]/following::td""",
		"deep_availability" : """//th[contains(text(), 'Vapautuminen:')]/following::td""",
		"deep_living_space_m2" : """//th[contains(text(), 'Asuinpinta-ala:')]/following::td""",
		"deep_image_gallery_link" : """//strong[contains(text(), 'Katso kaikki kuvat')]/parent::a""",
		"deep_cost_water": """//th[contains(text(), 'Vesimaksu:')]/following::td""",
		"deep_cost_deposit": """//th[contains(text(), 'Vakuus:')]/following::td"""
	}

	return items[item]

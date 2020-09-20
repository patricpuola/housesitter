#!/usr/bin/python3
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from Scrap import Scrap
import sys, os, time, re
import setup
from pprint import pprint
from housing import Cost, Listing
from pprint import pprint

def getListings(driver, deep_driver):
	driver.get("https://vuokraovi.com")
	deep_driver.get("https://vuokraovi.com")
	time.sleep(5)
	timeout = 5

	listings = []

	if not Scrap.waitFor(driver, [(By.XPATH, getXpath("search_box")), (By.XPATH, getXpath("search_button"))], timeout):
		print("Vuokraovi.com timed out")
	print("Vuokraovi.com frontpage loaded")

	driver.find_element(By.XPATH, getXpath("location_deny")).send_keys(Keys.SPACE)

	deep_driver.find_element(By.XPATH, getXpath("location_deny")).send_keys(Keys.SPACE)

	Scrap.checkAndRemoveBlocker(driver, 'Käytämme evästeitä', 'Hyväksy')
	Scrap.checkAndRemoveBlocker(deep_driver, 'Käytämme evästeitä', 'Hyväksy')

	search_box = driver.find_element(By.XPATH, getXpath("search_box"))
	search_button = driver.find_element(By.XPATH, getXpath("search_button"))

	search_box.send_keys("Helsinki")

	if not Scrap.waitFor(driver, (By.CSS_SELECTOR, "ul.ui-autocomplete > li"), timeout):
		print("List item timeout")
	search_box.send_keys(Keys.ENTER)

	search_button.click()

	page_nr = 0
	while (scrapeResultPage(driver, deep_driver, page_nr, listings)):
		driver.find_element(By.XPATH, getXpath("next_result_page")).click()
		page_nr += 1

def scrapeResultPage(driver, deep_driver, page_nr, listings):
	timeout = 5
	original_listings = len(listings)

	if not Scrap.waitFor(driver, (By.CLASS_NAME, "list-item-container"), timeout):
		print("Result display timeout")

	ads = driver.find_elements_by_class_name("list-item-container")

	deepScrape = {}

	for ad in ads:
		ad_index = len(listings)

		url = ad.find_elements_by_class_name("list-item-link")[0].get_attribute("href")
		url = re.sub(r'\?.*$', '', url)

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
		if not Scrap.waitFor(deep_driver, (By.XPATH, getXpath("deep_accordion")), timeout):
			print("Deep result accordion display timeout")

		try:
			description = deep_driver.find_element(By.XPATH, getXpath("deep_description")).text
		except NoSuchElementException:
			description = None

		try:
			street_address = deep_driver.find_element(By.XPATH, getXpath("deep_street_address")).text
		except NoSuchElementException:
			street_address = None

		try:
			zip, city = deep_driver.find_element(By.XPATH, getXpath("deep_zip_and_city")).text.split(" ", 1)
		except NoSuchElementException:
			zip = None
			city = None

		condition = Scrap.getTableCellByHeader(deep_driver, 'Yleiskunto:')
		build_year = Scrap.getTableCellByHeader(deep_driver, 'Rakennusvuosi:')
		total_space_m2 = Scrap.getTableCellByHeader(deep_driver, 'Kokonaispinta-ala:')

		try:
			agency = deep_driver.find_element(By.XPATH, getXpath("deep_agency")).text
		except NoSuchElementException:
			agency = None

		housing_type = Scrap.getTableCellByHeader(deep_driver, 'Tyyppi:')
		price = Scrap.getTableCellByHeader(deep_driver, 'Vuokra:')
		layout = Scrap.getTableCellByHeader(deep_driver, 'Kuvaus:')
		availability = Scrap.getTableCellByHeader(deep_driver, 'Vapautuminen:')
		living_space_m2 = Scrap.getTableCellByHeader(deep_driver, 'Asuinpinta-ala:')
		floor_and_max_floor_str = Scrap.getTableCellByHeader(deep_driver, 'Kerros:')
		
		if floor_and_max_floor_str is not None:
			floor_and_max_floor = floor_and_max_floor_str.split("/", 1)

			if len(floor_and_max_floor) == 2:
				floor = floor_and_max_floor[0].strip()
				floor_max = floor_and_max_floor[1].strip()
			elif len(floor_and_max_floor) == 1:
				floor = floor_and_max_floor[0].strip()
				floor_max = None

		listings[ad_index].fill(housing_type = housing_type, street_address = street_address, zip = zip, city = city, price = price, layout = layout, availability = availability, floor = floor, floor_max = floor_max, condition = condition, living_space_m2 = living_space_m2, total_space_m2 = total_space_m2, build_year = build_year, description = description, agency = agency)
		listing_costs = getCosts(deep_driver)
		for new_cost in listing_costs:
			listings[ad_index].addCost(new_cost)
		listings[ad_index].save()

		# Fetch images
		try:
			image_gallery_link = deep_driver.find_element(By.XPATH, getXpath("deep_image_gallery_link")).get_attribute('href')
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
	# TODO: Empty strings getting through?
	water_cost_text = Scrap.getTableCellByHeader(deep_driver, 'Vesimaksu:')
	if water_cost_text is not None:
		water_cost = Cost(type = Cost.TYPE_WATER, description = 'Vesimaksu', amount_EUR = 0.0, period = Cost.PERIOD_UNDEFINED)
		parseCostOccurrence(water_cost, water_cost_text)
		costs.append(water_cost)
	
	# TODO: Empty strings getting through?
	deposit_text = Scrap.getTableCellByHeader(deep_driver, 'Vakuus:')
	if deposit_text is not None:
		deposit = Cost(type = Cost.TYPE_DEPOSIT, description = 'Vuokravakuus', amount_EUR = 0.0, period = Cost.PERIOD_NON_REOCCURRING)
		parseCostOccurrence(deposit, deposit_text) # period ignored
		costs.append(deposit)
	
	# TODO: parse a full list and add parsing for other running cost types, but also fix this shit
	return costs

def parseCostOccurrence(cost: Cost, text):
	period, flags, amount = None, Cost.NO_FLAGS, None
	text_parts = re.split(r'\s+', text)
	for part in text_parts:
		sub_text = re.split(r'/', part)
		for subpart in sub_text:
			subpart = subpart.strip()
			if re.match(r'kk', subpart, flags=re.IGNORECASE):
				period = Cost.PERIOD_MONTHLY
			if re.match(r'hlö', subpart, flags=re.IGNORECASE):
				flags = flags | Cost.FLAG_MULTIPLY_PER_RESIDENT
			if re.match(r'\d+[\.,]?\d*', subpart):
				amount = re.sub(r'[^\d\.,]', '', subpart)
				amount = float(re.sub(r',', '.', amount))

	if amount is not None:
		cost.setAmount(amount)
		if period is not None:
			cost.setPeriod(period)
		if flags != Cost.NO_FLAGS:
			cost.addFlags(flags)
		return True
	return False

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
		"deep_description": """//*[@id="itempageDescription"]""",
		"deep_agency": """//*[@id="rentalContactInfo"]/p/b/a""",
		"deep_image_gallery_link" : """//strong[contains(text(), 'Katso kaikki kuvat')]/parent::a""",
	}

	return items[item]

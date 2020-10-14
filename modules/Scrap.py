#!/usr/bin/python3
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, WebDriverException
from housing import Cost, Listing
import os, sys, time, atexit, re
from multiprocessing import Process
import setup
from db import DBCon


class Scrap:
	VALID_BROWSERS = ["chrome", "firefox"]
	browser = "chrome"

	BROWSER_LEFT = 0
	BROWSER_RIGHT = 1

	# In non-headless mode browsers are split to left and right on the desktop
	active_webdrivers = {BROWSER_LEFT: [], BROWSER_RIGHT: []}

	available_width = 0
	available_height = 0

	exit_process_registered = False

	EXPIRY_LOOKUP_STRING = {
		'vuokraovi.com': 'Kohdetta ei löytynyt'
	}

	@classmethod
	def setBrowser(cls, browser):
		if browser.lower() not in cls.VALID_BROWSERS:
			return False
		cls.browser = browser.lower()

	@classmethod
	def getChromeOptions(cls, headless = False):
		chrome_options = webdriver.ChromeOptions()
		if setup.getConfig()['headless'] or headless:
			chrome_options.add_argument("--headless")
		chrome_options.add_argument("--no-sandbox")
		chrome_options.add_argument("--disable-dev-shm-usage")
		return chrome_options

	@classmethod
	def getWebDriver(cls, headless = False, side=BROWSER_LEFT):
		#cls.checkExitFunction()
		if cls.browser == 'chrome':
			chrome_path = setup.getWebDriverPath(cls.browser)
			chrome_options = cls.getChromeOptions(headless = headless)
			new_driver = webdriver.Chrome(chrome_path, options=chrome_options)
			cls.active_webdrivers[side].append(new_driver)
			return new_driver

	@classmethod
	def initWebdriverWindows(cls, single_driver = None, single_side = BROWSER_LEFT):
		# TODO: test if headless needs window postioning
		if setup.getConfig()['headless']:
			return

		if cls.available_height == 0 and cls.available_width == 0:
			testing_driver = None

			if single_driver is None:
				# Window positioning and initial resize to avoid maximized window problems
				for driver in cls.active_webdrivers[cls.BROWSER_LEFT]:
					driver.set_window_rect(height=480, width=640, x=0, y=0)
					if testing_driver is None:
						testing_driver = driver
				for driver in cls.active_webdrivers[cls.BROWSER_RIGHT]:
					driver.set_window_rect(height=480, width=640, x=0, y=0)
					if testing_driver is None:
						testing_driver = driver
			else:
				single_driver.set_window_rect(height=480, width=640, x=0, y=0)
				testing_driver = single_driver

			# TODO: necessary?
			time.sleep(2)

			testing_driver.maximize_window()
			cls.available_width = testing_driver.get_window_size()['width']
			cls.available_height = testing_driver.get_window_size()['height']

		# While loop to fix: unknown error: failed to change window state to 'normal', current state is 'maximized'
		windows_set = False
		while(windows_set == False):
			try:
				if single_driver is None:
					for driver in cls.active_webdrivers[cls.BROWSER_LEFT]:
						driver.set_window_rect(height=cls.available_height, width=cls.available_width/2, x=0, y=0)
					for driver in cls.active_webdrivers[cls.BROWSER_RIGHT]:
						driver.set_window_rect(height=cls.available_height, width=cls.available_width/2, x=cls.available_width, y=0)
					windows_set = True
				else:
					if single_side == cls.BROWSER_LEFT:
						single_driver.set_window_rect(height=cls.available_height, width=cls.available_width/2, x=0, y=0)
					else:
						single_driver.set_window_rect(height=cls.available_height, width=cls.available_width/2, x=cls.available_width, y=0)
					windows_set = True
			except WebDriverException:
				time.sleep(0.1)
		return

	@classmethod
	def checkExitFunction(cls):
		if not cls.exit_process_registered:
			atexit.register(cls.shutdownDrivers)
			cls.exit_process_registered = True
		return

	@classmethod
	def shutdownDrivers(cls):
		for driver in cls.active_webdrivers[cls.BROWSER_LEFT]:
			driver.quit()
		for driver in cls.active_webdrivers[cls.BROWSER_RIGHT]:
			driver.quit()
		return

	@classmethod
	def buildXpathSelector(cls, text = None, tags = None):
		if text is not None:
			if tags is None:
				return """//[contains(text(), '{}')]""".format(text.lower())
			else:
				self_tags = list(map(lambda tag: "self::"+tag, tags))
				return """//*[{}][contains(text(), '{}')]""".format(" or ".join(self_tags), text.lower())
		elif tags is not None:
			self_tags = list(map(lambda tag: "self::"+tag, tags))
			return """//*[{}]""".format(" or ".join(self_tags))
		else:
			return False


	# Method to try to find and remove blocking popups and ads (elementClickInterfenrenceException)
	@classmethod
	def checkAndRemoveBlocker(cls, driver, title_text, accept_text, title_tag=None, accept_tag=None):
		valid_title_tags = ['h1', 'h2', 'div', 'span']
		valid_accept_tags = ['button', 'div', 'a']
		if title_tag is not None:
			valid_title_tags = [title_tag]
		if accept_tag is not None:
			valid_accept_tags = [accept_tag]

		try:
			title_element = driver.find_element_by_xpath(
				cls.buildXpathSelector(title_text, valid_title_tags))
			accept_element = driver.find_element_by_xpath(
				cls.buildXpathSelector(accept_text, valid_accept_tags))
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
			wait_for_elements.append(
				expected_conditions.presence_of_element_located(type_identifier))

		try:
			WebDriverWait(driver, timeout_seconds).until(*wait_for_elements)
		except TimeoutException:
			return False
		return True

	@classmethod
	def getTableCellByHeader(cls, driver, header_text, header_tag=None):
		valid_header_tags = ['th', 'td']
		if header_tag is not None:
			valid_header_tags = [header_tag]
		xpath = cls.buildXpathSelector(header_text, valid_header_tags)
		xpath += "/following::td"
		try:
			text = driver.find_element(By.XPATH, xpath).text.strip()
		except NoSuchElementException:
			return None

		if len(text) > 0:
			return text
		else:
			return None

	@classmethod
	def checkExpired(cls, listing_id=None):
		expired_int = int(Listing.EXPIRED, 2)
		listings_to_check = []
		with DBCon.get().cursor() as cursor:
			#TODO: add option for checking a specific listing by id
			cursor.execute(
				"SELECT id, url, site FROM listings WHERE flags & %s = 0 LIMIT 20" % (expired_int,))
			listings_to_check = cursor.fetchall()

		lookup_nodes = {}
		for i in range(0, setup.getConfig()['multiprocess_threads_max']):
			lookup_nodes['node_'+str(i)] = {'process': None, 'listings': []}
		
		# Divide listings evenly to each node
		listing_idx = 0
		for listing in listings_to_check:
			if listing['site'] not in cls.EXPIRY_LOOKUP_STRING:
				print('No expiry check string found for site: %s' % listing['site'])
				del listings_to_check[listing]
				continue
			node = "node_"+str(listing_idx % setup.getConfig()['multiprocess_threads_max'])
			lookup_nodes[node]['listings'].append(listing)
			listing_idx += 1

		# run headless
		for node in lookup_nodes:
			lookup_nodes[node]['process'] = Process(target=cls.lookupExpired, args=(lookup_nodes[node]['listings'],))
			lookup_nodes[node]['process'].start()

		for node in lookup_nodes:
			lookup_nodes[node]['process'].join()
		
		return
	
	# document.readyState (possibly implement jQuery.active later?)
	# uninitialized - Has not started loading yet
	# loading - Is loading
	# loaded - Has been loaded
	# interactive - Has loaded enough and the user can interact with it
	# complete - Fully loaded
	@classmethod
	def waitUntilLoaded(cls, driver, timeout = 5, frequery_ms = 200):
		step = frequery_ms/1000
		timer = 0.0
		while timer < timeout:
			ready_state = driver.execute_script('return document.readyState')
			if ready_state == 'complete':
				return True
			timer += step
			time.sleep(step)
		return False
	
	@classmethod
	def lookupExpired(cls, listings):
		#pid = str(os.getpid())

		cls.setBrowser("chrome")
		driver = cls.getWebDriver(headless = True)
		cls.initWebdriverWindows(driver)

		expired_int = int(Listing.EXPIRED, 2)
		for listing in listings:
			driver.get(listing['url'])
			cls.waitUntilLoaded(driver)
			lookup_xpath = cls.buildXpathSelector(cls.EXPIRY_LOOKUP_STRING[listing['site']])
			try:
				driver.find_element_by_xpath(lookup_xpath)
				with DBCon.get().cursor() as cursor:
					cursor.execute("UPDATE listings SET flags = flags | %s WHERE id = %s LIMIT 1", (expired_int, listing['id']))
			except NoSuchElementException:
				continue
		driver.quit()

	@classmethod
	def dump(cls, obj):
		for attr in dir(obj):
			print("obj.%s" % (attr,))

	@classmethod
	def clickSearchButton(cls, driver):
		search_xpath = cls.buildXpathSelector(tags = ['button'])
		try:
			buttons = driver.find_elements_by_xpath(search_xpath)
		except NoSuchElementException:
			print("Cannot find search button")
			return False

		for button in buttons:
			if re.search(r'hae', button.text.lower()):
				button.click()
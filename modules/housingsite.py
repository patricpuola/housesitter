from multiprocessing import Process
from Scrap import Scrap
import re
import setup
from lang import Lang
from selenium.common.exceptions import NoSuchElementException, WebDriverException, ElementClickInterceptedException
from selenium.webdriver.common.by import By

class HousingSite:
	'''
	Housing ad site
		1. Load main page
			a) Click away ads, cookie consent things and geolocation
		2. Do a search (all preferrably or narrowed to an area)
		3. Gather search results
		4. Spawn deep_driver(s) and do the actual scraping
			a) Grab images
	'''

	def __init__(self, site, lang = "en"):
		self.site = self.includeProtocol(site, False)
		self.site_url = self.includeProtocol(site, True)
		self.search_terms = {}
		self.search_terms['free_search'] = ""
		self.search_terms['field_search'] = None
		if isinstance(lang, str):
			lang = lang.lower()
			Lang.check(lang)
			self.lang = lang


	def includeProtocol(self, site, include):
		included = False
		protocol = ""
		if re.match(r'http://', site):
			included = True
			protocol = 'http://'
		elif re.match(r'https://', site):
			included = True
			protocol = 'https://'

		if include and not included:
			return 'https://' + site
		elif not include and included:
			return site.replace(protocol, '')
		else:
			return site

	def setSearchTerms(self, search, **kwargs):
		if search is not None:
			self.search_terms['free_search'] = search
		if kwargs is not None:
			self.search_terms['field_search'] = kwargs
		pass

	def start(self):
		Scrap.setBrowser("chrome")
		self.main_driver = Scrap.getWebDriver(Scrap.BROWSER_LEFT)
		Scrap.initWebdriverWindows(self.main_driver)
		self.deep_nodes = {}
		for i in range(0, setup.getConfig()['threads']):
			self.deep_nodes['node_' +
							str(i)] = {'process': None, 'listing_urls': []}
		self.main_driver.get(self.site_url)
		Scrap.waitUntilLoaded(self.main_driver)
		if self.search_terms['free_search'] is not None:
			self.inputSearchTerms()
		self.search()

	def search(self):
		search_xpath = Scrap.buildXpathSelector(tags = ['button'])
		try:
			buttons = self.main_driver.find_elements_by_xpath(search_xpath)
		except NoSuchElementException:
			print("Cannot find search button")
			return False

		for button in buttons:
			if re.search(r'hae', button.text.lower()):
				self.safeClick(self.main_driver, button)
				# this this one out as well

	def inputSearchTerms(self):
		search_box = None
		try:
			text_inputs = self.main_driver.find_elements_by_css_selector("input[type=\"text\"]")
		except NoSuchElementException:
			print("Cannot find search box")
			return False
		
		search_box = self.chooseSearchBox(text_inputs, 'location')
		
		search_box.send_keys(self.search_terms['free_search'])
		pass

	def chooseSearchBox(self, elements, keywords):
		if len(elements) == 1:
			return elements[0]
		# Scoring 0-100
		id_match_value = 30
		class_match_value = 20
		initial_score: 10
		candidates = [initial_score] * len(elements)
		for idx, element in elements:
			id = element.get_attribute('id').lower()
			classes = element.get_attribute('class').lower()
			for keyword in keywords:
				keyword = keyword.lower()

				if re.match(r''+keyword, id):
					candidates[idx] += id_match_value

				if re.match(r''+keyword, classes):
					candidates[idx] += class_match_value
		winner = candidates.index(max(candidates))
		return elements[winner]

	def scrape(self, listing_urls):
		driver = Scrap.getWebDriver(Scrap.BROWSER_RIGHT)
		Scrap.initWebdriverWindows(driver)

	def extractAttribute(self, element_str, attribute):
		match = re.search(r''+attribute+'=[\'"]([^\'"]+)[\'"]', element_str, re.IGNORECASE)
		if match is not None:
			return match.group(1)
		else:
			return None

	def safeClick(self, driver, button):
		try:
			button.click()
		except ElementClickInterceptedException as e:
			error = str(e)
			match = re.search(r'Other element would receive the click: ([^\n]+)', error)
			element = match.group(1)
			el_id = self.extractAttribute(element, 'id')
			el_classes = self.extractAttribute(element, 'class')
			if el_id is not None:
				element = driver.find_element_by_id(el_id)
			elif el_classes is not None:
				class_selector = '.'+re.sub(r'\s+', '.', el_classes.strip())
				blocker = driver.find_element(By.CSS_SELECTOR, class_selector)
				blocking_parent = blocker.find_element(By.XPATH, '..')
				buttons = None
				while (True):
					buttons = blocking_parent.find_elements(By.CSS_SELECTOR, 'button')
					if len(buttons) == 0:
						blocking_parent = blocking_parent.find_element(By.XPATH, '..')
					else:
						break
				for button in buttons:
					pass
					# Implement language

	def findAndRemoveBlocker(self, blocking_element):
		pass

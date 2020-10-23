import Scrap
import re
import setup
import lang
import Levenshtein
import time
import sys
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
	# Filtering size values
	thumbnail_height_min = 80
	thumbnail_height_max = 400
	thumbnail_width_min = 100
	thumbnail_width_max = 500

	def __init__(self, site, language = "en"):
		self.site = self.includeProtocol(site, False)
		self.site_url = self.includeProtocol(site, True)
		self.search_terms = {}
		self.search_terms['free_search'] = ""
		self.search_terms['field_search'] = None
		language = language.lower()
		lang.Lang.check(language)
		self.language = language

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

	def setThumbnailLimits(self, height_min = None, height_max = None, width_min = None, width_max = None):
		if height_min is not None:
			self.thumbnail_height_min = height_min
		if height_min is not None:
			self.thumbnail_height_min = height_max
		if height_min is not None:
			self.thumbnail_width_min = width_min
		if height_min is not None:
			self.thumbnail_width_max = width_max
		
	def start(self):
		Scrap.Scrap.setBrowser("chrome")
		self.main_driver = Scrap.Scrap.getWebDriver(Scrap.Scrap.BROWSER_LEFT)
		Scrap.Scrap.initWebdriverWindows(self.main_driver)
		self.deep_nodes = {}
		for i in range(0, setup.getConfig()['threads']):
			self.deep_nodes['node_' +
							str(i)] = {'process': None, 'listing_urls': []}
		self.main_driver.get(self.site_url)
		Scrap.Scrap.waitUntilLoaded(self.main_driver)
		if self.search_terms['free_search'] is not None:
			self.inputSearchTerms()
		self.search()

		item_conts = self.findResultPageItemContainers(self.main_driver)
		print("done for now")
		sys.exit()


	def search(self):
		search_xpath = Scrap.Scrap.buildXpathSelector(tags = ['button'])
		try:
			buttons = self.main_driver.find_elements_by_xpath(search_xpath)
		except NoSuchElementException:
			print("Cannot find search button")
			return False

		search_text = lang.Lang.get('search', self.language)
		for button in buttons:
			if re.search(r''+search_text, button.text.lower(), re.IGNORECASE):
				return self.safeClick(self.main_driver, button)

		print("Cannot find search button with text: "+search_text)
		sys.exit()

	def inputSearchTerms(self):
		search_box = None
		try:
			text_inputs = self.main_driver.find_elements_by_css_selector("input[type=\"text\"]")
		except NoSuchElementException:
			print("Cannot find search box")
			return False
		
		search_box = self.chooseSearchBox(text_inputs, 'location')
		
		search_box.send_keys(self.search_terms['free_search'])

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
		driver = Scrap.Scrap.getWebDriver(Scrap.Scrap.BROWSER_RIGHT)
		Scrap.Scrap.initWebdriverWindows(driver)

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
			button_text_keys = ['accept', 'accept-all']
			button_texts = []
			for text_key in button_text_keys:
				translated_text = lang.Lang.get(text_key, self.language)
				button_texts.append(translated_text)
			error = str(e)
			match = re.search(r'Other element would receive the click: ([^\n]+)', error)
			blocking_element = match.group(1)

			el_id = self.extractAttribute(blocking_element, 'id')
			el_classes = self.extractAttribute(blocking_element, 'class')

			if el_id is not None:
				blocker = driver.find_element_by_id(el_id)
			elif el_classes is not None:
				class_selector = '.'+re.sub(r'\s+', '.', el_classes.strip())
				blocker = driver.find_element(By.CSS_SELECTOR, class_selector)

			if blocker is not None:
				blocking_parent = blocker.find_element(By.XPATH, '..')
				while (True):
					found_buttons = blocking_parent.find_elements(By.CSS_SELECTOR, 'button')
					if len(found_buttons) == 0:
						blocking_parent = blocking_parent.find_element(By.XPATH, '..')	# move to parent
					else:
						break
				closest_match = None
				for idx, found_button in enumerate(found_buttons):
					for trn_text in button_texts:
						distance = Levenshtein.distance(found_button.text, trn_text)
						if closest_match is None or closest_match[1] > distance:
							closest_match = (idx, distance)
				element = found_buttons[closest_match[0]]
			else:
				return False
			
			if element is not None:
				element.click()
				Scrap.Scrap.waitUntilLoaded(driver)
				button.click()
				Scrap.Scrap.waitUntilLoaded(driver)
				return True
			else:
				return False
	
	def scroll(self, driver, dir = "down"):
		before_y_offset = driver.execute_script('return window.scrollY')
		if dir == "down":
			driver.execute_script('window.scrollBy(0, window.innerHeight);')
		elif dir == "up":
			driver.execute_script('window.scrollBy(0, -window.innerHeight);')
		elif dir == "reset":
			driver.execute_script('window.scroll(0, 0);')
		after_y_offset = driver.execute_script('return window.scrollY')
		return before_y_offset != after_y_offset
	
	def findResultPageItemContainers(self, driver):
		common_images = {}
		images = []
		
		self.scroll(driver, "reset")
		while True:
			all_images = driver.find_elements(By.TAG_NAME, 'img')
			for image in all_images:
				if image in images:
					continue
				size = image.size
				if self.thumbnail_height_min > size['height'] or size['height'] > self.thumbnail_height_max or self.thumbnail_width_min > size['width'] or size['width'] > self.thumbnail_width_max:					continue
				images.append(image)
				size_comb = str(size['width'])+'x'+str(size['height'])
				location_x = str(image.location['x'])
				image_di = size_comb+"_"+location_x
				if image_di not in common_images:
					common_images[image_di] = 0
				common_images[image_di] += 1
			if not self.scroll(driver, "down"):
				break
		
		self.scroll(driver, "reset")
		# Work in progress / find common ancestor between most common image size/x-coord
		print(common_images)
		print("Most common dimensions and location:")
		common_di = max(common_images, key=common_images.get)
		print(common_di)

			
	def findAndRemoveBlocker(self, blocking_element):
		pass

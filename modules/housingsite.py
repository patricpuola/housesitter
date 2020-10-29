import Scrap
import re
import setup
import lang
import Levenshtein
import time
import sys
import functools
import multiprocessing
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

	blockers = []

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
		self.main_driver.get(self.site_url)
		Scrap.Scrap.waitUntilLoaded(self.main_driver)
		if self.search_terms['free_search'] is not None:
			self.inputSearchTerms()
		self.search()

		self.findNavigationElements(self.main_driver)
		self.findResultPageItemContainers(self.main_driver)

		url_queue = multiprocessing.JoinableQueue()
		self.deep_scrapers = [ DeepScraper(url_queue, self.language, self.blockers) for i in range(setup.getConfig()['threads']) ]	# Spawn workers

		for ds in self.deep_scrapers:	# Start workers
			ds.start()

		while True:
			deep_links = self.getDeepLinks(self.main_driver)
			for url in deep_links:
				url_queue.put(url)
			if not self.nextPage(self.main_driver):
				break
			break	# debug
		
		for ds in self.deep_scrapers:	# Kill workers
			print("poison")
			url_queue.put(None)
		
		print("wait for join")
		url_queue.join()
		print("done for now")
		sys.exit()

	@classmethod
	def buildXpathSelector(cls, text = None, tags = None):
		if text is not None:
			if tags is None:
				return """//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZÅÄÖ', 'abcdefghijklmnopqrstuvwxyzåäö'), '{}')]""".format(text.lower())
			else:
				self_tags = list(map(lambda tag: "self::"+tag, tags))
				return """//*[{}][contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZÅÄÖ', 'abcdefghijklmnopqrstuvwxyzåäö'), '{}')]""".format(" or ".join(self_tags), text.lower())
		elif tags is not None:
			self_tags = list(map(lambda tag: "self::"+tag, tags))
			return """//*[{}]""".format(" or ".join(self_tags))
		else:
			return False

	def search(self):
		search_xpath = self.buildXpathSelector(tags = ['button'])
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
		driver.execute_script('arguments[0].scrollIntoView(true);', button)
		try:
			button.click()
			Scrap.Scrap.waitUntilLoaded(driver)
			return True
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
				blocker_tag = element.tag_name
				blocker_classes = element.get_attribute('class').split(" ")
				self.blockers.append({'tag': blocker_tag, 'classes': blocker_classes})
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

		common_di = max(common_images, key=common_images.get)
		(thumbnail_width, thumbnail_height, x_offset) = re.split('[x_]', common_di)
		thumbnail_width = int(thumbnail_width)
		thumbnail_height = int(thumbnail_height)
		x_offset = int(x_offset)

		thumbnails = []
		for image in images:
			if image.size['height'] == thumbnail_height and image.size['width'] == thumbnail_width and image.location['x'] == x_offset:	# x_offset optional?
				thumbnails.append(image)
		
		if (len(thumbnails) >= 2):
			image_a = thumbnails[0]
			image_b = thumbnails[1]
			parent_a = image_a.find_element(By.XPATH, '..')
			parent_b = image_b.find_element(By.XPATH, '..')
			while parent_a != parent_b:	# Find common parent container
				result_item_container = parent_a
				parent_a = parent_a.find_element(By.XPATH, '..')
				parent_b = parent_b.find_element(By.XPATH, '..')
			result_container = parent_a
		else:
			print("Unable to determine result items' containers")
			return False

		self.result_container = {'tag': result_container.tag_name, 'classes': result_container.get_attribute('class').split(" ")}
		self.result_item_container = {'tag': result_item_container.tag_name, 'classes': result_item_container.get_attribute('class').split(" ")}
		return True

	def getDeepLinks(self, driver):
		if not hasattr(self, 'result_item_container'):
			self.findResultPageItemContainers(driver)
		result_container = driver.find_element(By.CSS_SELECTOR, self.result_container["tag"]+"."+".".join(self.result_container["classes"]))
		items = result_container.find_elements(By.CSS_SELECTOR, self.result_item_container["tag"]+"."+".".join(self.result_item_container["classes"]))
		links = []
		for item in items:
			a = item.find_element(By.TAG_NAME, 'a')
			if a is not None:
				links.append(a.get_attribute('href'))
		return links
	
	def findNavigationElements(self, driver):
		path_delimiter = '+'
		def compare_elements(el1, el2):
			if el1.tag_name != el2.tag_name:
				return 0
			similar_classes = list(set(el1.class_list) & set(el2.class_list))
			return len(similar_classes)

		def returnPathScores(base_path, base_element):
			current_tier = len(base_path.split(path_delimiter))
			paths = {}
			for tier, key in enumerate(nav_button_groups):
				if tier < current_tier:
					continue
				for idx, el in enumerate(nav_button_groups[key]):
					score = compare_elements(base_element, el)
					if score > 0:
						new_path = base_path+"+"+str(idx)
						paths[new_path] = score
						if (tier+1 < len(nav_button_groups.keys())):	# check if next tier exists
							paths = {**paths, **returnPathScores(new_path, base_element)}
				break
			return paths

		nav_button_possible_tags = ['div','a','button','input']
		search_for_navs = ['1','2','3']

		nav_button_groups = {}
		for nav_page in search_for_navs:
			xpath = self.buildXpathSelector(nav_page, nav_button_possible_tags)
			elements = driver.find_elements(By.XPATH, xpath)
			if len(elements) > 0:
				for el in elements:
					digits = re.sub(r'\D', '', el.text)
					if digits == nav_page:
						el.class_list = el.get_attribute('class').split(" ")
						if nav_page not in nav_button_groups:
							nav_button_groups[nav_page] = []
						nav_button_groups[nav_page].append(el)

		if len(nav_button_groups) == 0:
			print("Cannot find any likely navigation buttons")
			return False

		first_page = search_for_navs[0]
		paths = {}
		for idx, el in enumerate(nav_button_groups[first_page]):
			path = str(idx)
			paths = {**paths, **returnPathScores(path, el)}

		candidate_list = []
		for path, score in paths.items():
			candidate_list.append({'path':path, 'score':score})
		
		sorted(candidate_list, key = lambda candidate: len(candidate['path']) + candidate['score'], reverse=True)	# path length + similiar classes = score
		likely_group = candidate_list[0]

		element_indices = likely_group['path'].split(path_delimiter)
		element_indices = list(map(int, element_indices))
		self.nav = {'tag': nav_button_groups[first_page][element_indices[0]].tag_name}
		candidate_elements = []
		for candidate_tier, el_idx in enumerate(element_indices):
			for tier, key in enumerate(nav_button_groups):
				if tier == candidate_tier:
					candidate_elements.append(nav_button_groups[key][el_idx])
					break
		self.nav['classes'] = functools.reduce(set.intersection, list(map(lambda el: set(el.class_list), candidate_elements)))

		return True

	def getLastResultPage(self, driver):
		if not hasattr(self, 'nav'):
			self.findNavigationElements(driver)
		class_selector = "."+".".join(self.nav['classes']) if len(self.nav['classes']) > 0 else ""
		page_nav_buttons = driver.find_elements(By.CSS_SELECTOR, self.nav['tag']+class_selector)
		if (len(page_nav_buttons) == 0):
			print("Cannot find navigation buttons")
			return False
		last_el = page_nav_buttons[-1]
		last_page = re.sub(r'\D', '', last_el.text)
		return int(last_page)

	def nextPage(self, driver):
		if not hasattr(self, 'current_result_page'):
			self.current_result_page = 1
		if not hasattr(self, 'last_result_page'):
			self.last_result_page = self.getLastResultPage(driver)

		if self.current_result_page < self.last_result_page:
			next_page = self.current_result_page + 1
			class_selector = "."+".".join(self.nav['classes']) if len(self.nav['classes']) > 0 else ""
			page_nav_buttons = driver.find_elements(By.CSS_SELECTOR, self.nav['tag']+class_selector)
			for button in page_nav_buttons:
				content = int(re.sub(r'\D', '', button.text))
				if (content == next_page):
					return self.safeClick(driver, button)
		else:
			return False

class DeepScraper(multiprocessing.Process):
	def __init__(self, url_queue, language, blockers):
		multiprocessing.Process.__init__(self)
		self.url_queue = url_queue
		Scrap.Scrap.setBrowser("chrome")
		self.driver = Scrap.Scrap.getWebDriver(headless = False)
		Scrap.Scrap.initWebdriverWindows(self.driver, Scrap.Scrap.BROWSER_LEFT)
		self.blockers = blockers
		self.blockers_cleared = False
		self.language = language
	
	def run(self):
		proc_name = self.name
		print("Start: "+proc_name)
		keys = ['price','year','size']
		translations = {}
		for key in keys:
			translations[key] = lang.Lang.get(key, self.language)
		while True:
			url = self.url_queue.get()	# Blocking
			if url is None:
				print("Exit: "+proc_name)
				self.url_queue.task_done()
				break
			self.driver.get(url)
			Scrap.Scrap.waitUntilLoaded(self.driver)
			self.clearBlockers()
			# Page loaded, start scraping
			scraped_values = {}
			for key, trans_val in translations.items():
				print("key: %s Translated: %s" % (key, trans_val))
				xpath = HousingSite.buildXpathSelector(trans_val)
				elements = self.driver.find_elements(By.XPATH, xpath)
				for el in elements:
					print(el.tag_name)
					print(el.text)
				likely_element = min(elements, key=lambda el: Levenshtein.distance(el.text, trans_val))
				print("likely candidate")
				print(likely_element.tag_name)
				print(likely_element.text)
				following_element = self.getFollowingElement(likely_element)
				scraped_values[key] = following_element.text
			print(scraped_values)
			# Data scraping done, check for images
			self.getImages()
			self.url_queue.task_done()
		return

	def getImages(self):
		image_link = None
		pictures_trans = lang.Lang.get('pictures', self.language)
		image_links = self.driver.find_elements(By.PARTIAL_LINK_TEXT, pictures_trans) 	#TODO: fix this
		if len(image_links) == 0:
			return None
		elif len(image_links) == 1:
			image_link = image_links[0].get_attribute('href')
		else:
			# TODO: proper scoring of links
			image_link = image_links[0].get_attribute('href')
		
		if image_link is not None:
			return False
		self.driver.get(image_link)
		Scrap.Scrap.waitUntilLoaded(self.driver)
		anchors = self.driver.find_elements(By.TAG_NAME, 'a')
		hrefs = []
		for anchor in anchors:
			try:
				anchor.find_element(By.TAG_NAME, 'img')
				hrefs.append(anchor.get_attribute('href'))
			except NoSuchElementException:
				pass
		print(hrefs)
		return

	def getFollowingElement(self, element):
		following_xpath = "following-sibling::*"
		parent_xpath = ".."
		try:
			following_element = element.find_element(By.XPATH, following_xpath)
		except NoSuchElementException:
			parent = element.find_element(By.XPATH, parent_xpath)
			following_element = self.getFollowingElement(parent)
		return following_element
	
	def clearBlockers(self):
		if self.blockers_cleared:
			return True
		for blocker in self.blockers:
			class_selector = "."+".".join(blocker['classes']) if len(blocker['classes']) > 0 else ""
			blocker = self.driver.find_elements(By.CSS_SELECTOR, blocker['tag']+class_selector)
			if len(blocker) > 1:
				print("More than one potential button found for blocker "+blocker['tag']+class_selector)
			elif len(blocker) == 1:
				blocker[0].click()
				Scrap.Scrap.waitUntilLoaded(self.driver)

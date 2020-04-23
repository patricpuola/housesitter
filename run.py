#!/usr/bin/python3
import sys, os, json
sys.path.insert(1, r'modules')

from selenium import webdriver
from selenium.webdriver.common.keys import Keys

import vuokraovi_com
import credentials_secure as cred

# Configuration
with open(r"config.json", 'r') as conf_file:
	conf_json = conf_file.read()
	conf = json.loads(conf_json)

if (conf['opencage_enabled']):
	try:
		from opencage.geocoder import OpenCageGeocode
		geocoder = OpenCageGeocode(cred.opencage.api_key)
	except ImportError:
		print("Opencage geocoding not available, install it via pip3 to geocode addresses")
		conf['opencage_enabled'] = False

# debug
#query = u"Mannerheimintie 1, Helsinki, Finland"
#results = geocoder.geocode(query)
#print(u'%f;%f;%s;%s' % (results[0]['geometry']['lat'], results[0]['geometry']['lng'], results[0]['components']['country_code'], results[0]['annotations']['timezone']['name']))
#sys.exit()

# Chrome init
chrome_path = r"webdrivers/chromedriver.81"
chrome_options = webdriver.ChromeOptions()
#chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
driver = webdriver.Chrome(chrome_path, options=chrome_options)

vuokraovi_com.getListings(driver)

driver.quit()

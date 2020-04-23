#!/usr/bin/python3
import sys, os
sys.path.insert(1, r'modules')
flags = sys.argv

from selenium import webdriver
from selenium.webdriver.common.keys import Keys

import vuokraovi_com
import setup
from setup import getConfig as conf
from setup import getCredentials as cred

if "setup" in flags:
	setup.init()

if not conf()['initial_setup_performed']:
	print("Run the initial setup first:\n"+" ".join(sys.argv)+" setup")
	sys.exit()


if conf()['opencage_enabled']:
	if setup.isModuleInstalled('opencage'):
		from opencage.geocoder import OpenCageGeocode
		geocoder = OpenCageGeocode(cred()['opencage']['api_key'])
	else:
		print("'opencage' geocoding not available, install it via pip3 to geocode addresses")
		conf()['opencage_enabled'] = False

def getGeo(query):
	global geocoder
	if not conf()['opencage_enabled']:
		return false

	results = geocoder.geocode(query)
	result = results[0]

	geo = {}
	geo['lng'] = result['geometry']['lng']
	geo['lat'] = result['geometry']['lat']
	geo['confidence'] = result['confidence']
	if 'suburb' in result['components']:
		geo['suburb'] = result['components']['suburb']
	if 'city' in result['components']:
		geo['city'] = result['components']['city']
	if 'town' in result['components']:
		geo['city'] = result['components']['town']

	return geo
sys.exit()
# Chrome init
chrome_path = r"webdrivers/chromedriver.81"
chrome_options = webdriver.ChromeOptions()
#chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
driver = webdriver.Chrome(chrome_path, options=chrome_options)

vuokraovi_com.getListings(driver)

driver.quit()

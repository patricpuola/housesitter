#!/usr/bin/python3
import sys, os, time, math
sys.path.insert(1, r'modules')
flags = sys.argv

os.popen('pkill chromedriver')
os.popen('pkill chrome')

from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

from SiteScraper import SiteScraper
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

# Chrome init
chrome_path = r"webdrivers/chromedriver.83"
chrome_options = webdriver.ChromeOptions()
if conf()['headless']:
	chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
main_driver = webdriver.Chrome(chrome_path, options=chrome_options)
deep_driver = webdriver.Chrome(chrome_path, options=chrome_options)

main_driver.set_window_position(0,0)
deep_driver.set_window_position(0,0)

# Window positioning and resizing
main_driver.maximize_window()
window_width = main_driver.get_window_size()['width']
window_height = main_driver.get_window_size()['height']

# Sidebar check
main_driver.fullscreen_window()
sidebar_compensation = main_driver.get_window_size()['width']-window_height
main_driver.fullscreen_window()

main_driver.set_window_rect(height = window_height, width = window_width/2, x = 0, y = 0)
deep_driver.set_window_rect(height = window_height, width = window_width/2, x = window_width + sidebar_compensation, y = 0)
vuokraovi_com.getListings(main_driver, deep_driver)

main_driver.quit()
deep_driver.quit()

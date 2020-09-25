#!/usr/bin/python3
import sys, os, time, math
from pathlib import Path
sys.path.insert(1, r'modules')
flags = sys.argv

os.popen('pkill chromedriver')
os.popen('pkill chrome')
'''
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import WebDriverException
'''
from Scrap import Scrap
import vuokraovi_com
import setup
from setup import getConfig as conf
from setup import getCredentials as cred
from pprint import pprint

if "setup" in flags:
	setup.init()

if not conf()['initial_setup_performed']:
	print("Run the initial setup first:\n"+" ".join(sys.argv)+" setup")
	sys.exit()

if conf()['opencage_enabled']:
	if setup.isModuleInstalled('opencage'):
		from geocode import Geocode
	else:
		print("'opencage' geocoding not available, install it via pip3 to geocode addresses")
		conf()['opencage_enabled'] = False

if "geocode" in flags:
	if conf()['opencage_enabled']:
		Geocode.checkListings()
	else:
		print("Geocoding is currently disabled")
	sys.exit()

if "empty" in flags:
	setup.emptyTables()
	sys.exit()

Scrap.setBrowser("chrome")
main_driver = Scrap.getWebDriver(Scrap.BROWSER_LEFT)
deep_driver = Scrap.getWebDriver(Scrap.BROWSER_RIGHT)

Scrap.initWebdriverWindows()

vuokraovi_com.getListings(main_driver, deep_driver)


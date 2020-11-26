#!/usr/bin/python3
import sys, os, time, math
sys.path.insert(1, r'modules')
flags = sys.argv

os.popen('pkill chromedriver')
os.popen('pkill chrome')

import Scrap
import vuokraovi_com
import setup
import housingsite

if "setup" in flags:
	setup.init()

if not setup.getConfig()['initial_setup_performed']:
	print("Run the initial setup first:\n"+" ".join(sys.argv)+" setup")
	sys.exit()

if setup.getConfig()['opencage_enabled']:
	if setup.isModuleInstalled('opencage'):
		from geocode import Geocode
	else:
		print("'opencage' geocoding not available, install it via pip3 to geocode addresses")
		setup.getConfig()['opencage_enabled'] = False

if "geocode" in flags:
	if setup.getConfig()['opencage_enabled']:
		Geocode.checkListings()
	else:
		print("Geocoding is currently disabled")
	sys.exit()

if "empty" in flags:
	setup.emptyTables()
	setup.deleteImages()
	sys.exit()

if "expired" in flags:
	Scrap.Scrap.checkExpired()
	sys.exit()

etuovi = housingsite.HousingSite('etuovi.com', 'fi')
etuovi.setSearchTerms(city='Helsinki')
etuovi.start()


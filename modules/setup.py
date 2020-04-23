#!/usr/bin/python3
import sys, os, re, importlib, json, pprint

required_packages = ['mariadb-server']
optional_packages = []

required_modules = ['selenium', 'pymysql']
optional_modules = ['opencage']

config = None
credentials = None

def getConfig(force = False):
	global config
	if config != None and not force:
		return config

	with open(r"config.json", 'r') as config_file:
		config_json = config_file.read()
		config = json.loads(config_json)

	return config

def saveConfig():
	global config
	with open(r"config.json", 'w') as config_file:
		json.dump(config, config_file, indent=3)

def getCredentials(force = False):
	global credentials
	if credentials != None and not force:
		return credentials

	if not os.path.exists(r"credentials.json.secure"):
		print("""ERROR: Cannot find "credentials.json.secure" """)
		print("""Use credentials.json.secure.template to fill-in and rename""")
		sys.exit()

	with open(r"credentials.json.secure", 'r') as conf_file:
		conf_json = conf_file.read()
		credentials = json.loads(conf_json)

	return credentials

import db

def isPackageInstalled(package):
	response = os.popen('apt -qq list %s 2>null' % package).read()
	lines = response.split("\n")
	for line in lines:
		if line.find(package) == 0 and line.find('installed') != -1:
			return True
	return False

def isModuleInstalled(module):
	try:
		importlib.import_module(module)
	except ImportError:
		return False
	return True

def init():
	print("\n[ HOUSESITTER INITIAL SETUP ]")

	if config['initial_setup_performed']:
		if input("This system has already been initialized, redo? [Y/N]:").lower() != 'y':
			print("[ DONE ]\n")
			sys.exit()
		else:
			print("Redoing initial setup")

	print("Database and database user setup...")
	if db.checkUserDB():
		print("Database ok")
	else:
		sys.exit()

	getConfig()['initial_setup_performed'] = True
	saveConfig()
	print("\n[ DONE, CONFIG UPDATED ]\n")
	sys.exit()

def check():
	print("\n[ HOUSESITTER SETUP CHECK ]")

	missing_required_packages = []
	missing_required_modules = []
	missing_optional_packages = []
	missing_optional_modules = []

	status_ready = True

	for package in required_packages:
		if not isPackageInstalled(package):
			missing_required_packages.append(package)
			status_ready = False

	for module in required_modules:
		if not isModuleInstalled(module):
			missing_required_modules.append(module)
			status_ready = False

	for package in optional_packages:
		if not isPackageInstalled(package):
			missing_optional_packages.append(package)

	for module in optional_modules:
		if not isModuleInstalled(module):
			missing_optional_modules.append(module)

	if len(missing_required_packages) > 0:
		print("Missing required packages:")
		print("\t"+', '.join(missing_required_packages))

	if len(missing_required_modules) > 0:
		print("Missing required modules:")
		print("\t"+', '.join(missing_required_modules))

	if len(missing_optional_packages) > 0:
		print("Missing optional packages:")
		print("\t"+', '.join(missing_optional_packages))

	if len(missing_optional_modules) > 0:
		print("Missing optional modules:")
		print("\t"+', '.join(missing_optional_modules))

	if not status_ready:
		print("[ SETUP NOK ]")
		print("[ EXIT ]\n")
		sys.exit()
	else:
		print("[ SETUP OK ]\n")


#!/usr/bin/python3
import sys, os, re, importlib, json, pprint, pymysql

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

	depedencyCheck()
	screenshot_directory = r""+getConfig()['screenshot_directory']
	if os.path.exists(screenshot_directory) == False:
		os.makedirs(screenshot_directory)
		os.chmod(screenshot_directory, 0o777)
		print("Screenshot folder created")


	print("Database and database user setup...")
	if checkUserDB():
		print("Database ok")
	else:
		print("User or Database creation error")
		sys.exit()

	print("Creating tables...")
	if createTables():
		print("Tables ok")
	else:
		print("Table creation error")
		sys.exit()

	getConfig()['initial_setup_performed'] = True
	saveConfig()
	print("\n[ DONE, CONFIG UPDATED ]\n")
	sys.exit()

def depedencyCheck():
	import db
	print("Dependency check...")

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
		print("Dependencies not OK")
		print("[ EXIT ]\n")
		sys.exit()
	else:
		print("Dependencies OK\n")

def checkUserDB():
	from db import DBCon
	user_creation = "CREATE USER '%s'@'%s' IDENTIFIED BY '%s'" % (getCredentials()['mysql']['username'], getConfig()['db_host'], getCredentials()['mysql']['password'])
	database_creation = "CREATE DATABASE IF NOT EXISTS %s CHARACTER SET %s COLLATE %s" % (getConfig()['db_name'], getConfig()['db_character_set'], getConfig()['db_collation'])
	user_grant = "GRANT ALL PRIVILEGES ON %s.* TO '%s'@'%s'" % (getConfig()['db_name'], getCredentials()['mysql']['username'], getConfig()['db_host'])
	flush = "FLUSH PRIVILEGES"
	'''
	print("\nUser '%s' or database '%s' does not exist or have sufficient access" % (getCredentials()['mysql']['username'], getConfig()['db_name']))
	print("Input root password to check and add user and/or database to %s or Ctrl-C to exit and do it manually" % (getConfig()['db_service']))
	try:
		root_pwd = input("root password: ")
	except KeyboardInterrupt:
		print("Connect to mysql shell and run these commands manually:")
		print(user_creation)
		print(database_creation)
		print(user_grant)
		print(flush)
		sys.exit()
	'''
	root_pwd = getCredentials()['mysql_root_pwd']
	root_connection = DBCon.get(user='root', password=root_pwd, db=None, persistent=False)

	if root_connection is False:
		print("Unable to connect as root, aborting setup")
		sys.exit()

	try:
		with root_connection.cursor() as cursor:
			cursor.execute("SELECT EXISTS(SELECT 1 FROM mysql.user WHERE user = '%s') as user_found" % (getCredentials()['mysql']['username']))
			result = cursor.fetchone()
			if result["user_found"] == 1:
				user_exists = True
			else:
				user_exists = False

			if not user_exists:
				cursor.execute(user_creation)

			cursor.execute(database_creation)
			cursor.execute(user_grant)
			cursor.execute(flush)

		root_connection.close()
	except pymysql.Error as e:
		error_nr, error_text = [e.args[0], e.args[1]]
		print("PyMySQL Error (%d): %s" % (error_nr, error_text))
		return False

	return True

def createTables():
	from db import DBCon
	table_template_path = r"table_templates"
	table_templates = [f for f in os.listdir(table_template_path) if os.path.isfile(os.path.join(table_template_path, f))]


	for table_template in table_templates:
		with open(os.path.join(table_template_path, table_template), "r") as template_file:
			with DBCon.get().cursor() as cursor:
				cursor.execute(template_file.read())

	return True

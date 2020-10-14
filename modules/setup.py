#!/usr/bin/python3
import sys, os, re, json, pprint, pymysql, requests, wget, pwd, grp, stat
import subprocess
from bs4 import BeautifulSoup
from zipfile import ZipFile
from pathlib import Path

required_packages = ['mariadb-server', 'wget']
optional_packages = []

installed_modules = []
required_modules = ['selenium', 'pymysql', 'beautifulsoup4', 'iso639']
optional_modules = ['opencage']

ROOT = Path(__file__).resolve().parent.parent
CONFIG_FILE = ROOT / 'config.json'
CREDENTIALS_FILE = ROOT / 'credentials.json.secure'

config = None
credentials = None

TMP_DIR = "/tmp/"
WEBDRIVER_DIR = ROOT / 'webdrivers'
webdrivers = {
	'chrome': {
		'url': 'https://chromedriver.chromium.org/',
		'download_url': 'https://chromedriver.storage.googleapis.com/',
		'package': 'google-chrome-stable'
	},
	'firefox': {
		'url': 'tba', # TODO
		'package': 'firefox'
	}
}

def fixFileOwnerAndMode(filepath):
	uid = pwd.getpwnam(getConfig()['user']).pw_uid
	gid = grp.getgrnam(getConfig()['group']).gr_gid
	os.chown(filepath, uid, gid)
	os.chmod(filepath, stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)
	return True

def getWebDriverPath(browser):
	if not isinstance(browser, str):
		print("""getWebDriverPath(browser) parameter is not a string""")
		sys.exit()
	browser = browser.lower()
	valid_browsers = ['chrome', 'firefox']
	if browser.lower() not in valid_browsers:
		print("""{} is not a valid browser""".format(browser))
		sys.exit()
	download_url = None
	if browser == 'chrome':
			package_version = getPackageVersion(webdrivers[browser]['package'])
			main_version = parseWebDriverMainVersion(package_version)
			webdriver_file = "chromedriver." + main_version
			if not os.path.exists(WEBDRIVER_DIR / webdriver_file):
				main_page_html = requests.get(webdrivers[browser]['url'] + 'downloads').text
				soup = BeautifulSoup(main_page_html, 'html.parser')
				for link in soup.find_all('a', href=True, text=re.compile(r'ChromeDriver ' + main_version)):
					full_version = str(re.search(r"[\d\.]+", link.text)[0])
					download_url = webdrivers[browser]['download_url'] + full_version + '/chromedriver_linux64.zip'
					break
			else:
				return WEBDRIVER_DIR / webdriver_file
	elif browser == 'firefox':
		# TODO
		pass

	if (download_url == None):
		print("{} WebDriver missing, cannot find download link. Please download WebDriver manually".format(browser))
		sys.exit()
	
	tmp_zip = TMP_DIR + browser + "driver.zip"
	print("Webdriver missing for current version of {}, downloading matching one".format(browser))
	print("Downloading {} to {}".format(download_url, tmp_zip))
	wget.download(download_url, tmp_zip)
	with ZipFile(tmp_zip, 'r') as zipObject:
		for filename in zipObject.namelist():
			if (filename.endswith('driver')):
				with open(WEBDRIVER_DIR / webdriver_file, "wb") as webdriver_handle:
					webdriver_handle.write(zipObject.read(filename))
				fixFileOwnerAndMode(WEBDRIVER_DIR / webdriver_file)

	new_webdriver_fullpath = WEBDRIVER_DIR / webdriver_file
	
	if not new_webdriver_fullpath:
		print("Something is wrong with downloaded zip file, driver file not found in {}".format(tmp_zip))
	else:
		return new_webdriver_fullpath

def parseWebDriverMainVersion(version_str):
	return str(re.search(r"^[\d]+", version_str.strip())[0])

def getConfig(force = False):
	global config
	if config != None and not force:
		return config

	with open(CONFIG_FILE, 'r') as config_file:
		config_json = config_file.read()
		config = json.loads(config_json)

	return config

def saveConfig():
	global config
	with open(CONFIG_FILE, 'w') as config_file:
		json.dump(config, config_file, indent=3)

def getCredentials(force = False):
	global credentials
	if credentials != None and not force:
		return credentials

	if not CREDENTIALS_FILE.exists():
		print("""ERROR: Cannot find "credentials.json.secure" """)
		print("""Use credentials.json.secure.template to fill-in and rename""")
		sys.exit()

	with open(CREDENTIALS_FILE, 'r') as conf_file:
		conf_json = conf_file.read()
		credentials = json.loads(conf_json)

	return credentials

import db

def getPackageVersion(package):
	response = os.popen('apt -qq list %s 2>/dev/null' % package).read()
	lines = response.split("\n")
	for line in lines:
		if line.find(package) == 0 and line.find('installed') != -1:
			match = re.search(r"^[\S]+\s([\S]+)", line)
			return str(match[1])
	return False

def isPackageInstalled(package):
	response = os.popen('apt -qq list %s 2>/dev/null' % package).read()
	lines = response.split("\n")
	for line in lines:
		if line.find(package) == 0 and line.find('installed') != -1:
			return True
	return False

def isModuleInstalled(module):
	#if len(installed_modules) == 0: #check why global variable not found
	out = subprocess.Popen(['pip3', 'list'],
	stdout=subprocess.PIPE,
	stderr=subprocess.STDOUT)
	stdout, stderr = out.communicate()
	text_output = stdout.decode("utf-8")
	module_list = text_output.split("\n")[2:]
	module_list = list(map(lambda line: re.split(r'\s+', line)[0], module_list))
	module_list = list(filter(lambda module: len(module) > 0, module_list))
	installed_modules = module_list
	return module in installed_modules

def init():
	print("\n[ HOUSESITTER INITIAL SETUP ]")

	if config['initial_setup_performed']:
		if input("This system has already been initialized, redo? [Y/N]: ").lower() != 'y':
			print("[ DONE ]\n")
			sys.exit()
		else:
			print("Redoing initial setup")

	depedencyCheck()
	screenshot_directory = ROOT / getConfig()['screenshot_directory']
	if not screenshot_directory.exists():
		# TODO check 2 lines below
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
	# TODO: remove credential hardcoding
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
	table_template_path = ROOT / "table_templates"
	# TODO: check line below
	table_templates = [f for f in os.listdir(table_template_path) if os.path.isfile(os.path.join(table_template_path, f))]


	for table_template in table_templates:
		with open(os.path.join(table_template_path, table_template), "r") as template_file:
			with DBCon.get().cursor() as cursor:
				cursor.execute(template_file.read())

	return True

def emptyTables():
	if input("Are you sure you want to TRUNCATE() all tables? [Y/N]: ").lower() != 'y':
		print("[ DONE ]\n")
		return
	from db import DBCon
	print("Emptying all tables...")
	with DBCon.get(cursor_type=DBCon.CURSOR_TYPE_NORMAL).cursor() as cursor:
		cursor.execute('SHOW TABLES')
		tables = cursor.fetchall()
		for table in tables:
			table_name = table[0]
			cursor.execute('TRUNCATE TABLE `{}`'.format(table_name))
			print("`{}` OK".format(table_name))
	print("[ DONE ]\n")
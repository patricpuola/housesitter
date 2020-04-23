#!/usr/bin/python3
import sys
import pymysql
import setup

db_cred = setup.getCredentials()['mysql']
config = setup.getConfig()

connection = None
attempts_max = 3

user_and_db_checked = False

USER_ACCESS_DENIED = 1698
DB_ACCESS_DENIED = 1044

def get(attempt = 0):
	global connection, retries_max, user_and_db_checked

	attempt += 1
	if connection != None:
		return connection

	try:
		connection = pymysql.connect(host=config['db_host'], user=db_cred['username'], passwd=db_cred['password'], unix_socket=config['db_unix_socket'])
		connection.select_db(config['db_name'])
	except pymysql.Error as e:
		error_nr, error_text = [e.args[0], e.args[1]]
		print("PyMySQL Error (%d): %s" % (error_nr, error_text))

		if (attempt < attempts_max):
			return get(attempt)

def checkUserDB():
	global user_and_db_checked

	print("\nUser '%s' or database '%s' does not exist or have sufficient access" % (db_cred['username'], config['db_name']))
	print("Input root password to check and add user and/or database to %s or Ctrl-C to exit and do it manually" % (config['db_service']))
	try:
		root_pwd = input("root password: ")
	except KeyboardInterrupt:
		print('exit')
		sys.exit()

	try:
		root_connection = pymysql.connect(host=config['db_host'], user='root', passwd=root_pwd, unix_socket=config['db_unix_socket'])
	except pymysql.Error as e:
		error_nr, error_text = [e.args[0], e.args[1]]
		print("PyMySQL Error (%d): %s" % (error_nr, error_text))
		return False

	try:
		with root_connection.cursor() as cursor:
			cursor.execute("SELECT EXISTS(SELECT 1 FROM mysql.user WHERE user = '%s')" % (db_cred['username']))
			user_exists = True if cursor.fetchone()[0] == 1 else False

			if not user_exists:
				cursor.execute("CREATE USER '%s'@'%s' IDENTIFIED BY '%s'" % (db_cred['username'], config['db_host'], db_cred['password']))

			cursor.execute("CREATE DATABASE IF NOT EXISTS %s CHARACTER SET %s COLLATE %s" % (config['db_name'], config['db_character_set'], config['db_collation']))
			cursor.execute("GRANT ALL PRIVILEGES ON %s.* TO '%s'@'%s'" % (config['db_name'], db_cred['username'], config['db_host']))
			cursor.execute("FLUSH PRIVILEGES")

		root_connection.commit()
		root_connection.close()
	except pymysql.Error as e:
		error_nr, error_text = [e.args[0], e.args[1]]
		print("PyMySQL Error (%d): %s" % (error_nr, error_text))
		return False


	user_and_db_checked = True
	return True

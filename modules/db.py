#!/usr/bin/python3
import sys
import pymysql
from setup import getCredentials, getConfig

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
		connection = pymysql.connect(host=getConfig()['db_host'], user=getCredentials()['mysql']['username'], passwd=getCredentials()['mysql']['password'], unix_socket=getConfig()['db_unix_socket'])
		connection.select_db(getConfig()['db_name'])
	except pymysql.Error as e:
		error_nr, error_text = [e.args[0], e.args[1]]
		print("PyMySQL Error (%d): %s" % (error_nr, error_text))

		if (attempt < attempts_max):
			return get(attempt)

def checkUserDB():
	global user_and_db_checked

	print("\nUser '%s' or database '%s' does not exist or have sufficient access" % (getCredentials()['mysql']['username'], getConfig()['db_name']))
	print("Input root password to check and add user and/or database to %s or Ctrl-C to exit and do it manually" % (getConfig()['db_service']))
	try:
		root_pwd = input("root password: ")
	except KeyboardInterrupt:
		print('exit')
		sys.exit()

	try:
		root_connection = pymysql.connect(host=getConfig()['db_host'], user='root', passwd=root_pwd, unix_socket=getConfig()['db_unix_socket'])
	except pymysql.Error as e:
		error_nr, error_text = [e.args[0], e.args[1]]
		print("PyMySQL Error (%d): %s" % (error_nr, error_text))
		return False

	try:
		with root_connection.cursor() as cursor:
			cursor.execute("SELECT EXISTS(SELECT 1 FROM mysql.user WHERE user = '%s')" % (getCredentials()['mysql']['username']))
			user_exists = True if cursor.fetchone()[0] == 1 else False

			if not user_exists:
				cursor.execute("CREATE USER '%s'@'%s' IDENTIFIED BY '%s'" % (getCredentials()['mysql']['username'], getConfig()['db_host'], getCredentials()['mysql']['password']))

			cursor.execute("CREATE DATABASE IF NOT EXISTS %s CHARACTER SET %s COLLATE %s" % (getConfig()['db_name'], getConfig()['db_character_set'], getConfig()['db_collation']))
			cursor.execute("GRANT ALL PRIVILEGES ON %s.* TO '%s'@'%s'" % (getConfig()['db_name'], getCredentials()['mysql']['username'], getConfig()['db_host']))
			cursor.execute("FLUSH PRIVILEGES")

		root_connection.commit()
		root_connection.close()
	except pymysql.Error as e:
		error_nr, error_text = [e.args[0], e.args[1]]
		print("PyMySQL Error (%d): %s" % (error_nr, error_text))
		return False


	user_and_db_checked = True
	return True

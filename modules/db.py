#!/usr/bin/python3
import sys
import pymysql
import setup

class DBCon:
	USER_ACCESS_DENIED = 1698
	DB_ACCESS_DENIED = 1044

	connection = None
	attempts_max = 3
	attempt = 0

	@classmethod
	def get(cls, attempt = 0, user = setup.getCredentials()['mysql']['username'], password = setup.getCredentials()['mysql']['password'], db = setup.getConfig()['db_name'], persistent = True):
		cls.attempt = attempt
		cls.attempt += 1
		if cls.connection is not None and persistent is True:
			return cls.connection

		try:
			if persistent is True:
				cls.connection = pymysql.connect(host=setup.getConfig()['db_host'], user=user, passwd=password, unix_socket=setup.getConfig()['db_unix_socket'], charset='utf8', cursorclass=pymysql.cursors.DictCursor, autocommit=True)
				if db is not None:
					cls.connection.select_db(db)
				return cls.connection
			else:
				nonpersistent_connection = pymysql.connect(host=setup.getConfig()['db_host'], user=user, passwd=password, unix_socket=setup.getConfig()['db_unix_socket'], charset='utf8', cursorclass=pymysql.cursors.DictCursor, autocommit=True)
				if db is not None:
					nonpersistent_connection.select_db(db)
				return nonpersistent_connection
		except pymysql.Error as e:
			error_nr, error_text = [e.args[0], e.args[1]]
			print("PyMySQL Error (%d): %s" % (error_nr, error_text))

			if (cls.attempt < cls.attempts_max):
				return get(cls.attempt)
			else:
				return False

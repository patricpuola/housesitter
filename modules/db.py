#!/usr/bin/python3
import sys
import pymysql
import pymongo
import setup
import os

class DBCon:	# MariaDB
	USER_ACCESS_DENIED = 1698
	DB_ACCESS_DENIED = 1044

	CURSOR_TYPE_UNDEFINED = 0
	CURSOR_TYPE_NORMAL = 1
	CURSOR_TYPE_DICT = 2

	connection = None
	attempts_max = 3
	attempt = 0

	cursor_type_in_use = CURSOR_TYPE_UNDEFINED

	@classmethod
	def get(cls, attempt = 0, user = setup.getCredentials()['mysql']['username'], password = setup.getCredentials()['mysql']['password'], db = setup.getConfig()['db_name'], persistent = True, cursor_type = CURSOR_TYPE_DICT):
		cls.attempt = attempt
		cls.attempt += 1
		if cls.connection is not None and cls.connection.open and persistent is True and cursor_type == cls.cursor_type_in_use:
			return cls.connection

		cls.cursor_type_in_use = cursor_type

		if cursor_type == cls.CURSOR_TYPE_NORMAL:
			cursorclass = pymysql.cursors.Cursor
		else:
			cursorclass = pymysql.cursors.DictCursor

		conversions = pymysql.converters.conversions
		conversions[pymysql.FIELD_TYPE.BIT] = lambda x: int.from_bytes(x, byteorder='big')
		try:
			if persistent is True:
				cls.connection = pymysql.connect(host=setup.getConfig()['db_host'], user=user, passwd=password, unix_socket=setup.getConfig()['db_unix_socket'], charset='utf8', cursorclass=cursorclass, autocommit=True, conv=conversions)
				if db is not None:
					cls.connection.select_db(db)
				cls.attempt = 0
				return cls.connection
			else:
				nonpersistent_connection = pymysql.connect(host=setup.getConfig()['db_host'], user=user, passwd=password, unix_socket=setup.getConfig()['db_unix_socket'], charset='utf8', cursorclass=cursorclass, autocommit=True, conv=conversions)
				if db is not None:
					nonpersistent_connection.select_db(db)
				cls.attempt = 0
				return nonpersistent_connection
		except pymysql.Error as e:
			error_nr, error_text = [e.args[0], e.args[1]]
			print("PyMySQL Error (%d): %s" % (error_nr, error_text))

			if (cls.attempt < cls.attempts_max):
				return cls.get(cls.attempt, user=user, password=password, db=db, persistent=persistent, cursor_type=cls.cursor_type_in_use)
			else:
				return False

class MongoCon:
	clients = {}	# Process-id dependent connection management

	@classmethod
	def get(cls):
		pid = os.getpid()
		if pid not in cls.clients:
			cls.clients[pid] = cls.connect()
		else:
			try:
				cls.clients[pid].server_info()
			except pymongo.errors.ServerSelectionTimeoutError:
				cls.clients[pid] = cls.connect()
		return cls.clients[pid]['housesitter']

	@classmethod
	def connect(cls):
		try:
			return pymongo.MongoClient(host="localhost", port=27017)
		except pymongo.errors.ServerSelectionTimeoutError as err:
			print("ERROR WHEN CONNECTION")
			print(err)
		return
import db
import iso639

class Lang:
	@classmethod
	def get(cls, key, lang):
		cls.check(lang)
		with db.DBCon.get().cursor() as cursor:
			cursor.execute("SELECT value FROM languages WHERE language = '%s' AND `key` = '%s' LIMIT 1" % (lang,key))
			row = cursor.fetchone()
		if row is not None:
			return row['value']
		else:
			return None

	@classmethod
	def set(cls, key, value, lang):
		cls.check(lang)
		with db.DBCon.get().cursor() as cursor:
			cursor.execute("SELECT id, value FROM languages WHERE `key` = '%s' AND language = '%s' LIMIT 1" % (key, lang))
			old = cursor.fetchone()
			if old is not None:
				if old['value'] != value:
					cursor.execute("UPDATE languages SET value = '%s' WHERE id = %d" % (value, old['id']))
			else:
				cursor.execute("INSERT INTO languages (`key`, language, value) VALUES ('%s', '%s', '%s')" % (key, lang, value))
		return True

	@classmethod
	def addKey(cls, key):
		with db.DBCon.get().cursor() as cursor:
			cursor.execute("SELECT 1 FROM languages WHERE `key` = '%s' AND language IS NULL" % (key,))
			found = cursor.fetchone()
			if (found is not None):
				return False
			else:
				cursor.execute("INSERT INTO languages (`key`, language, value) VALUES ('%s', NULL, NULL)" % (key,))
				return True

	@classmethod
	def deleteKey(cls, key):
		with db.DBCon.get().cursor() as cursor:
			cursor.execute("DELETE FROM languages WHERE `key` = '%s'" % (key,))
			return True

	@classmethod
	def addLanguage(cls, language):
		with db.DBCon.get().cursor() as cursor:
			print("checking language")
			cursor.execute("SELECT 1 FROM languages WHERE language = '%s' LIMIT 1" % (language,))
			print("execute 1")
			if cursor.fetchone() is not None:
				return False
			print("check passed")
			cursor.execute("INSERT INTO languages (`key`, language, value) VALUES (NULL, '%s', NULL)" % (language,))
			print("language added")
			return True
	
	@classmethod
	def getLanguages(cls):
		languages = []
		with db.DBCon.get().cursor() as cursor:
			cursor.execute("SELECT language FROM languages WHERE `key` IS NULL AND value IS NULL")
			row = cursor.fetchone()
			while row is not None:
				languages.append(row['language'])
				row = cursor.fetchone()
		return languages
			

	@classmethod
	def getAll(cls):
		translations = {}
		with db.DBCon.get().cursor() as cursor:
			cursor.execute("SELECT `key` FROM languages WHERE language IS NULL")
			keys = cursor.fetchall()
			for row in keys:
				key = row['key']
				translations[key] = {}
				cursor.execute("SELECT language, value FROM languages WHERE `key` = '%s'" % (key,))
				for row in cursor:
					translations[key][row['language']] = row['value']
		return translations

	@classmethod
	def getLangAbbr(cls):
		languages = iso639.languages.part1.keys()
		return languages

	@classmethod
	def check(cls, lang):
		try:
			iso639.languages.get(alpha2=lang)
		except KeyError:
			raise Exception("Language is not in the correct 2 letter format (ISO 639-1)")
		return True
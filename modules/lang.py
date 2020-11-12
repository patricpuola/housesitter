import db
import iso639

class Lang:
	@classmethod
	def get(cls, key, language):
		cls.check(language)
		translation = db.MongoCon.get()['languages'].find_one({'key':key, 'language':language})
		if translation is not None:
			return translation['values']
		else:
			return None

	@classmethod
	def set(cls, key, values, language):
		cls.check(language)
		translation = db.MongoCon.get()['languages'].find_one({'key': key, 'language': language})
		if translation is None:
			db.MongoCon.get()['languages'].insert_one({'key':key, 'language':language, 'values':[]})
		query = {"key":key, "language":language}
		update = {"$set": {"values": values}}
		db.MongoCon.get()['languages'].update_one(query, update)
		return True

	@classmethod
	def addKey(cls, key):
		get_key = db.MongoCon.get()['languages'].find_one({'key': key, 'language': None})
		if get_key is not None:
			return False
		db.MongoCon.get()['languages'].insert_one({'key': key, 'language': None, 'values': None})
		return True

	@classmethod
	def deleteKey(cls, key):
		query = {'key': key}
		delete = db.MongoCon.get()['languages'].delete_many(query)
		return delete.deleted_count

	@classmethod
	def addLanguage(cls, language):
		cls.check(language)
		get_language = db.MongoCon.get()['languages'].find_one({'key': None, 'language': language})
		if get_language is not None:
			return False
		db.MongoCon.get()['languages'].insert_one({'key': None, 'language': language, 'values': None})
		return True
	
	@classmethod
	def deleteLanguage(cls, language):
		cls.check(language)
		query = {'language': language}
		delete = db.MongoCon.get()['languages'].delete_many(query)
		return delete.deleted_count
	
	@classmethod
	def getLanguages(cls):
		return db.MongoCon.get()['languages'].distinct("language", {"language": {"$ne": None}})

	@classmethod
	def getAll(cls):
		translations = {}
		for item in db.MongoCon.get()['languages'].find({'key':{'$ne':None}}):
			if item['key'] not in translations:
				translations[item['key']] = {}
			if item['language'] is not None and item['language'] not in translations[item['key']]:
				translations[item['key']][item['language']] = item['values']
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
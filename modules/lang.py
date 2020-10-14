from db import DBCon
from iso639 import languages

class Lang:
	@classmethod
	def get(cls, key, lang):
		cls.check(lang)
		with DBCon.get(cursor_type=DBCon.CURSOR_TYPE_NORMAL).cursor() as cursor:
			cursor.execute("SELECT value FROM languages WHERE lang = %s LIMIT 1" % (lang,))
			value = cursor.fetchone()
		return value

	@classmethod
	def set(cls, key, value, lang):
		cls.check(lang)
		with DBCon.get().cursor() as cursor:
			cursor.execute("SELECT id, value FROM languages WHERE key = %s AND lang = %s LIMIT 1" % (key, lang))
			old = cursor.fetchone()
			if old is not None:
				if old['value'] != value:
					cursor.execute("UPDATE lang SET value = %s WHERE id = %d" % (value, old['id']))
			else:
				cursor.execute("INSERT INTO languages (key, language, value) VALUES (%s, %s, %s)" % (key, lang, value))
		return True

	@classmethod
	def getAll(cls):
		with DBCon.get().cursor() as cursor:
			cursor.execute("SELECT * FROM languages")
			language = cursor.fetchall()
		return language

	@classmethod
	def check(cls, lang):
		try:
			languages.get(alpha2=lang)
		except KeyError:
			raise Exception("Language is not in the correct 2 letter format (ISO 639-1)")
		return True
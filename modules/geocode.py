#!/usr/bin/python3
import setup
from db import DBCon
from opencage.geocoder import OpenCageGeocode

'''
[OpenCage Free license]
Limit 2500 Requests/day
1 Request/s
'''

class Geocode:
	geocoder = None

	@classmethod
	def query(cls, query):
		if not setup.getConfig()['opencage_enabled']:
			return False

		if not cls.initCheck():
			return False

		geo = cls.getCache(query)

		if (geo is not False):
			return geo
		else:
			return cls.queryAPI(query)

	# TODO: error handling / return False
	@classmethod
	def initCheck(cls):
		if cls.geocoder is None:
			cls.geocoder = OpenCageGeocode(setup.getCredentials()['opencage']['api_key'])
		return True

	@classmethod
	def getCache(cls, query):
		with DBCon.get().cursor() as cursor:
			cursor.execute("SELECT query, lat, lng, confidence, city, suburb, date_updated FROM geocodes WHERE query = %s LIMIT 1", (query))
			result = cursor.fetchone()
			if result is not None:
				print("cache hit")
				return result
			else:
				print("cache miss")
				return False

	@classmethod
	def queryAPI(cls, query):
		print("api hit")
		results = cls.geocoder.geocode(query)
		result = results[0]

		geo = {}
		geo["query"] = query
		geo["lng"] = result["geometry"]["lng"]
		geo["lat"] = result["geometry"]["lat"]
		geo["confidence"] = result["confidence"]
		if "suburb" in result["components"]:
			geo["suburb"] = result["components"]["suburb"]
		else:
			geo["suburb"] = None

		if "city" in result["components"]:
			geo["city"] = result["components"]["city"]
		else:
			geo["city"] = None

		if "town" in result["components"]:
			geo["city"] = result["components"]["town"]

		with DBCon.get().cursor() as cursor:
			insert_columns = []
			insert_placeholders = []
			insert_values = []
			for column, value in geo.items():
				if value is None:
					continue
				insert_columns.append(column)
				insert_placeholders.append("%s")
				insert_values.append(str(value))

			values = tuple(insert_values)
			cursor.execute("INSERT INTO geocodes ("+", ".join(insert_columns)+") VALUES ("+", ".join(insert_placeholders)+")", values)

		return geo

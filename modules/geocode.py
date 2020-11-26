#!/usr/bin/python3
import setup
import db
import sys, pprint
from opencage.geocoder import OpenCageGeocode
from housing import Listing

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

		return cls.queryAPI(query)

	# TODO: error handling / return False
	@classmethod
	def initCheck(cls):
		if cls.geocoder is None:
			cls.geocoder = OpenCageGeocode(setup.getCredentials()['opencage']['api_key'])
		return True

	@classmethod
	def queryAPI(cls, query):
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

		return geo

	@classmethod
	def checkListings(cls):
		listing_rows = []
		with db.DBCon.get().cursor() as cursor:
			cursor.execute("SELECT id, street_address, zip, city FROM listings WHERE lat IS NULL or lng IS NULL")
			listing_rows = cursor.fetchall()

		with db.DBCon.get().cursor() as cursor:
			for row in listing_rows:
				if row == None:
					break
				if row['street_address'] == None or row['zip'] == None or row['city'] == None:
					continue
				full_address = row["street_address"]+", "+str(row["zip"])+" "+row["city"]
				geo = cls.query(full_address)
				if geo is not False:
					update_values = []
					sql_update = "UPDATE listings SET lat = %s, lng = %s"
					update_values.append(geo['lat'])
					update_values.append(geo['lng'])
					if geo["suburb"] is not None:
						sql_update += ", suburb = %s"
						update_values.append(geo["suburb"])
					sql_update += " WHERE id = %s LIMIT 1"
					update_values.append(row["id"])
					update_values = tuple(update_values)
					cursor.execute(sql_update, update_values)

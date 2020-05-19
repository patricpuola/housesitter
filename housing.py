#!/usr/bin/python3
import re
from db import DBCon

class Cost:
	TYPE_UNDEFINED = 0
	TYPE_LAND_RENT = 1
	TYPE_MAINTENANCE = 2
	TYPE_FINANCING = 3
	TYPE_WATER = 4
	TYPE_ELECTRICITY = 5

	PERIOD_UNDEFINED = 0
	PERIOD_MONTH = 1
	PERIOD_YEAR = 2
	PERIOD_NON_REOCCURRING = 3
	PERIOD_OTHER = 4

	def __init__(self, type = TYPE_UNDEFINED, description = "", amount_monthly_EUR = 0.0, period = PERIOD_MONTH, period_multiplier = None, multiply_per_resident = False):
		self.type = type
		self.description = description
		self.amount_monthly_EUR = amount_monthly_EUR
		self.period = period
		self.period_multiplier = period_multiplier
		self.multiply_per_resident = multiply_per_resident

		self.sanitize()

	def sanitize(self):
		if not self.type in [TYPE_UNDEFINED, TYPE_LAND_RENT, TYPE_MAINTENANCE, TYPE_FINANCING]:
			self.type = TYPE_UNDEFINED

		if type(self.description) != str:
			self.description = "";

		self.amount_monthly_EUR = abs(self.amount_monthly_EUR)

		if not self.period in [PERIOD_UNDEFINED, PERIOD_MONTH, PERIOD_YEAR, PERIOD_OTHER]:
			self.period = PERIOD_UNDEFINED

		if self.period != PERIOD_OTHER and self.period_multiplier != None:
			self.period_multiplier = None

class Listing:
	TYPE_OWN_UNDEFINED = 0
	TYPE_OWN_RENTAL = 1
	TYPE_OWN_OWNERSHIP = 2
	TYPE_OWN_PART_OWNDERSHIP = 3

	DEFAULT_COUNTRY = "FI"

	def __init__(self, site, url):
		self.id = None
		self.url = url
		self.site = site
		self.ownership_type = None
		self.housing_type = None
		self.street_address = None
		self.zip = None
		self.city = None
		self.price = None
		self.country = self.DEFAULT_COUNTRY
		self.agency = None
		self.description = None
		self.living_space_m2 = None
		self.layout = None
		self.total_space_m2 = None
		self.availability = None
		self.build_year = None
		self.floor = None
		self.floor_count = None
		self.floor_max = None
		self.additional_info = None
		self.condition = None
		self.date_added = None
		self.date_updated = None
		self.costs = []

		save()

	def fill(self, ownership_type = None, housing_type = None, street_address = None, zip = None, city = None, country = None, price = None, agency = None, description = None, living_space_m2 = None, layout = None, total_space_m2 = None, availability = None, build_year = None, floor = None, floor_count = None, floor_max = None, additional_info = None, condition = None, date_added = None):
		fill_data = locals()
		for key in fill_data:
			if fill_data[key] is not None and key != 'self':
				setattr(self, key, fill_data[key])

	def sanitize(self):
		#sanitize all attributes
		if not self.ownership_type in [TYPE_OWN_UNDEFINED, TYPE_OWN_RENTAL, TYPE_OWN_OWNERSHIP, TYPE_OWN_PART_OWNERSHIP]:
			self.ownership_type = TYPE_OWN_UNDEFINED

		self.zip = re.sub(r'\D', '', self.zip)
		self.city = self.city.capitalize()
		self.city = 'FI' if len(self.city) == 0 else self.city
		self.living_space_m2 = re.sub(r'\D', '', self.living_space_m2)
		self.layout = re.sub(r',', '+', re.sub(r'\s', '', self.layout)).upper()
		self.total_space_m2 = re.sub('\D', '', self.total_space_m2)
		self.build_year = re.sub(r'\D', '', self.build_year)
		self.floor = re.sub(r'\D', '', self.floor)
		self.floor_count = re.sub(r'\D', '', self.floor)
		self.floor_max = re.sub(r'\D', '', self.floor)

	def addCost(self, new_cost: Cost, check_duplicates = True):
		if check_duplicates:
			for cost in self.costs:
				if cost == new_cost:
					return false

		self.costs.append(new_cost)

	def save(self):
		if self.id is not None:
			with DBCon.get().cursor() as cursor:
				cursor.execute("SHOW COLUMNS FROM listings")
				table_columns = []
				for column in cursor:
					if (column["Field"] != "id"):
						table_columns.append(column["Field"])

				update_sql = "UPDATE listings SET "
				update_columns = []
				update_values = []

				for idx in table_columns:
					column = update_columns[idx]
					update_columns.append(column+" = %s")
					update_values.append(getattr(self, column))

				update_sql += ", ".join(update_columns)
				update_sql += "WHERE id = %s LIMIT 1"
				update_values.append(self.id)
				update_value_tuple = tuple(update_values)
				cursor.execute(update_sql, update_value_tuple)

		else:
			with DBCon.get().cursor() as cursor:
				cursor.execute("SELECT id FROM listings WHERE url = %s", self.url)
				id = cursor.fetchone()
				if (id is not None):
					self.id = id
				else:
					cursor.execute("INSERT INTO listings (site, url, date_updated) VALUES (%s, %s, NOW())", (self.site, self.url))
					self.id = cursor.lastrowid
		return True

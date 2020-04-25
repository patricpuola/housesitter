#!/usr/bin/python3
import re

class Listing:
	TYPE_OWN_UNDEFINED = 0
	TYPE_OWN_RENTAL = 1
	TYPE_OWN_OWNERSHIP = 2
	TYPE_OWN_PART_OWNDERSHIP = 3

	def __init__(ownership_type, housing_type, street_address, zip, city, country, price, indoor_size_m2, layout, outdoor_size_m2):
		self.ownership_type = ownership_type
		self.housing_type = housing_type
		self.street_address = street_address
		self.zip = zip
		self.city = city
		self.price = price
		self.country = country
		self.indoor_size_m2 = indoor_size_m2
		self.layout = layout
		self.outdoor_size_m2 = outdoor_size_m2
		self.costs = []

		self.sanitize()

	def sanitize():
		#sanitize all attributes
		if not self.ownership_type in [TYPE_OWN_UNDEFINED, TYPE_OWN_RENTAL, TYPE_OWN_OWNERSHIP, TYPE_OWN_PART_OWNERSHIP]:
			self.ownership_type = TYPE_OWN_UNDEFINED

		self.zip = re.sub(r'\D', '', self.zip)
		self.city = self.city.capitalize()
		self.city = 'FI' if len(self.city) == 0 else self.city
		self.indoor_size_m2 = re.sub(r'\D', '', self.indoor_size_m2)
		self.layout = self.layout #TODO: quantize rooms
		self.outdoor_size_m2 = re.sub('\D', '', self.outdoor_size_m2)

	def addCost(new_cost, check_duplicates = True):
		if check_duplicates:
			for cost in self.costs:
				if cost == new_cost:
					return false
		self.costs.append(new_cost)

class Cost:
	TYPE_UNDEFINED = 0
	TYPE_LAND_RENT = 1
	TYPE_MAINTENANCE = 2
	TYPE_FINANCING = 3

	PERIOD_UNDEFINED = 0
	PERIOD_MONTH = 1
	PERIOD_YEAR = 2
	PERIOD_OTHER = 3

	def __init__(type, description, amount_monthly_EUR, period = self.PERIOD_MONTH, period_multiplier = 1):
		self.type = type
		self.description = description
		self.amount_monthly_EUR = amount_monthly_EUR
		self.period = period
		self.period_multiplier = period_multiplier

		self.sanitize()

	def sanitize():
		if not self.type in [TYPE_UNDEFINED, TYPE_LAND_RENT, TYPE_MAINTENANCE, TYPE_FINANCING]:
			self.type = TYPE_UNDEFINED

		self.amount_monthly_EUR = abs(self.amount_monthly_EUR)

		if not self.period in [PERIOD_UNDEFINED, PERIOD_MONTH, PERIOD_YEAR, PERIOD_OTHER]:
			self.period = PERIOD_UNDEFINED

		if self.period != PERIOD_OTHER and self.period_multiplier != 1:
			self.period_multiplier = 1

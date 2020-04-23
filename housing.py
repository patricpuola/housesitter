#!/usr/bin/python3

class Listing:
	TYPE_UNDEFINED = 0
	TYPE_RENTAL = 1
	TYPE_OWNERSHIP = 2
	TYPE_PART_OWNDERSHIP = 3

	def __init__(ownership_type, housing_type, street_address, city, price, indoor_size_m2, layout, outdoor_size_m2):
		self.ownership_type = ownership_type
		self.housing_type = housing_type
		self.street_address = street_address
		self.city = city
		self.price = price
		self.indoor_size_m2 = indoor_size_m2
		self.layout = layout
		self.outdoor_size_m2 = outdoor_size_m2

		self.sanitize()

	def sanitize():
		#sanitize all attributes
		if not self.ownership_type in [TYPE_UNDEFINED, TYPE_RENTAL, TYPE_OWNERSHIP, TYPE_PART_OWNERSHIP]:
			self.ownership_type = TYPE_UNDEFINED
		#etc... todo

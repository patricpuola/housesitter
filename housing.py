#!/usr/bin/python3
import re, pymysql, hashlib, uuid, mimetypes, pathlib, requests
from db import DBCon
import setup
from pprint import pprint

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
	TYPE_OWN_PART_OWNERSHIP = 3

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

		self.save()

	def fill(self, ownership_type = None, housing_type = None, street_address = None, zip = None, city = None, country = None, price = None, agency = None, description = None, living_space_m2 = None, layout = None, total_space_m2 = None, availability = None, build_year = None, floor = None, floor_count = None, floor_max = None, additional_info = None, condition = None, date_added = None):
		fill_data = locals()
		for key in fill_data:
			if fill_data[key] is not None and key != 'self':
				setattr(self, key, fill_data[key])

	def sanitize(self):
		#sanitize all attributes
		if not self.ownership_type in [self.TYPE_OWN_UNDEFINED, self.TYPE_OWN_RENTAL, self.TYPE_OWN_OWNERSHIP, self.TYPE_OWN_PART_OWNERSHIP]:
			self.ownership_type = self.TYPE_OWN_UNDEFINED

		if self.zip is not None:
			self.zip = re.sub(r'\D', '', str(self.zip))
		if self.city is not None:
			self.city = self.city.capitalize()
		if self.country is not None:
			self.country = 'FI'
		if self.price is not None:
			self.price = re.sub(r'[^\d,\.]', '', str(self.price))
			self.price = re.sub(r',', '.', self.price)
		if self.living_space_m2 is not None:
			self.living_space_m2 = re.sub(r'[^\d,\.]', '', str(self.living_space_m2))
			self.living_space_m2 = re.sub(r',', '.', self.living_space_m2)
		if self.layout is not None:
			self.layout = re.sub(r',', '+', re.sub(r'\s', '', str(self.layout))).upper()
		if self.total_space_m2 is not None:
			self.total_space_m2 = re.sub(r'[^\d,\.]', '', str(self.total_space_m2))
			self.total_space_m2 = re.sub(r',', '.', str(self.total_space_m2))
		if self.build_year is not None:
			self.build_year = re.sub(r'\D', '', str(self.build_year))
		if self.floor is not None:
			self.floor = re.sub(r'\D', '', str(self.floor))
		if self.floor_count is not None:
			self.floor_count = re.sub(r'\D', '', str(self.floor_count))
		if self.floor_max is not None:
			self.floor_max = re.sub(r'\D', '', str(self.floor_max))

		for attr, value in self.__dict__.items():
			if type(value) == str and len(value) == 0:
				setattr(self, attr, None)

	def addCost(self, new_cost: Cost, check_duplicates = True):
		if check_duplicates:
			for cost in self.costs:
				if cost == new_cost:
					return false

		self.costs.append(new_cost)

	def save(self):
		if self.id is not None:
			self.sanitize()
			with DBCon.get().cursor() as cursor:
				cursor.execute("SHOW COLUMNS FROM listings")
				table_columns = []
				for column in cursor:
					if (column["Field"] != "id"):
						table_columns.append(column["Field"])

				update_sql = "UPDATE listings SET "
				update_columns = []
				update_values = []

				for column in table_columns:
					value = getattr(self, column)
					if value is not None:
						update_columns.append("`"+column+"` = %s")
						update_values.append(value)

				update_sql += ", ".join(update_columns)
				update_sql += " WHERE id = %s LIMIT 1"
				update_values.append(self.id)
				update_value_tuple = tuple(update_values)
				cursor.execute(update_sql, update_value_tuple)
		else:
			# todo: fix this shit
			with DBCon.get().cursor() as cursor:
				cursor.execute("SELECT id FROM listings WHERE url = %s", self.url)
				url_listing = cursor.fetchone()
				if (url_listing is not None):
					self.id = url_listing["id"]
				else:
					cursor.execute("INSERT INTO listings (site, url, date_updated) VALUES (%s, %s, NOW())", (self.site, self.url))
					self.id = cursor.lastrowid
		return True

	def addImage(self, image_url):
		extension = pathlib.Path(image_url).suffix
		mime_types = mimetypes.guess_type(image_url)
		mime_type = str(mime_types[0])
		original_filename = pathlib.Path(image_url).name
		image_obj = requests.get(image_url)
		image_data = image_obj.content
		hash_MD5 = hashlib.md5(image_data).hexdigest()
		image_id = None
		image_obj.close()

		# Check if image hash found in database
		with DBCon.get().cursor() as cursor:
			cursor.execute("SELECT id FROM images WHERE hash_MD5 = %s LIMIT 1", (hash_MD5))
			found = cursor.fetchone()
			if found is not None:
				return False

		with DBCon.get().cursor() as cursor:
			# Check if image uuid found in database
			uuid_found = True
			while uuid_found is not None:
				image_id = str(uuid.uuid4())
				cursor.execute("SELECT 1 FROM images WHERE uuid = %s LIMIT 1", (image_id))
				uuid_found = cursor.fetchone()

		image_file = open(r''+setup.getConfig()['screenshot_directory']+image_id+extension, 'bw+')
		image_file.write(image_data)
		image_file.close()

		with DBCon.get().cursor() as cursor:
			cursor.execute("INSERT INTO images (listing_id, uuid, hash_MD5, extension, mime_type, original_filename, date_added) VALUES (%s, %s, %s, %s, %s, %s, NOW())", (self.id, image_id, hash_MD5, extension, mime_type, original_filename))

		return True

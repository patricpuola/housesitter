#!/usr/bin/python3
import re, pymysql, hashlib, uuid, mimetypes, pathlib, requests
import db
import setup

class Cost:
	TYPE_UNDEFINED = 0
	TYPE_LAND_RENT = 1
	TYPE_MAINTENANCE = 2
	TYPE_FINANCING = 3
	TYPE_WATER = 4
	TYPE_ELECTRICITY = 5
	TYPE_DEPOSIT = 6
	valid_types = [TYPE_UNDEFINED, TYPE_LAND_RENT, TYPE_MAINTENANCE, TYPE_FINANCING, TYPE_WATER, TYPE_ELECTRICITY, TYPE_DEPOSIT]

	PERIOD_UNDEFINED = 0
	PERIOD_DAILY = 1
	PERIOD_WEEKLY = 2
	PERIOD_MONTHLY = 3
	PERIOD_YEARLY = 4
	PERIOD_NON_REOCCURRING = 5
	valid_periods = [PERIOD_UNDEFINED, PERIOD_DAILY, PERIOD_WEEKLY, PERIOD_MONTHLY, PERIOD_YEARLY, PERIOD_NON_REOCCURRING]

	NO_FLAGS = int('00000000', 2)
	FLAG_MULTIPLY_PER_RESIDENT = int('00000001', 2)
	ALL_FLAGS = int('11111111', 2)

	def __init__(self, type = TYPE_UNDEFINED, description = "", amount_EUR = 0.0, period = PERIOD_MONTHLY, period_multiplier = 1.0, flags = NO_FLAGS):
		self.id = None
		self.type = type
		self.description = description
		self.amount_EUR = amount_EUR
		self.period = period
		self.period_multiplier = period_multiplier
		self.flags = flags

		self.sanitize()

	def sanitize(self):
		if not self.type in self.valid_types:
			self.type = self.TYPE_UNDEFINED

		if type(self.description) != str:
			self.description = ""

		self.amount_EUR = abs(self.amount_EUR)
		if type(self.amount_EUR) is not float:
			self.amount_EUR = float(self.amount_EUR)

		if not self.period in self.valid_periods:
			self.period = self.PERIOD_UNDEFINED

		if type(self.period_multiplier) is not float:
			self.period_multiplier = float(self.period_multiplier)

	def setAmount(self, amount_EUR):
		if type(amount_EUR) is float:
			self.amount_EUR = amount_EUR

	def setPeriod(self, period):
		if period in self.valid_periods:
			self.period = period

	def addFlags(self, flags):
		if flags <= self.ALL_FLAGS and flags > 0:
			self.flags = self.flags | flags

#TODO: create load() -function and refactor implementation
class Listing:
	TYPE_OWN_UNDEFINED = 0
	TYPE_OWN_RENTAL = 1
	TYPE_OWN_OWNERSHIP = 2
	TYPE_OWN_PART_OWNERSHIP = 3

	DEFAULT_COUNTRY = "FI"

	INIT_FLAGS = b'00000000'
	GEOCODING_PREFORMED = b'00000001'
	EXPIRED = b'00000010'

	def __init__(self, site, url):
		self.id = None
		self.url = url
		self.site = site
		self.ownership_type = None
		self.housing_type = None
		self.street_address = None
		self.zip = None
		self.suburb = None
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
		self.flags = self.INIT_FLAGS
		self.date_added = None
		self.date_updated = None
		self.costs = []

		self.save()

	def fill(self, **kwargs):
		#ownership_type = None, housing_type = None, street_address = None, zip = None, suburb = None, city = None, country = None, price = None, agency = None, description = None, living_space_m2 = None, layout = None, total_space_m2 = None, availability = None, build_year = None, floor = None, floor_count = None, floor_max = None, additional_info = None, condition = None, flags = None, date_added = None
		for key, value in kwargs.items():
			if value is not None and key != 'self' and hasattr(self, key):
				setattr(self, key, value)

	def sanitize(self):
		#sanitize all attributes
		if not self.ownership_type in [self.TYPE_OWN_UNDEFINED, self.TYPE_OWN_RENTAL, self.TYPE_OWN_OWNERSHIP, self.TYPE_OWN_PART_OWNERSHIP]:
			self.ownership_type = self.TYPE_OWN_UNDEFINED

		if self.zip is not None:
			self.zip = re.sub(r'\D', '', str(self.zip))
		if self.city is not None:
			self.city = self.city.capitalize()
		if self.suburb is not None:
			self.suburb = self.suburb.capitalize()
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

		for idx, cost in enumerate(self.costs):
			self.costs[idx].sanitize()

	def addCost(self, new_cost, check_duplicates = True):
		if check_duplicates:
			for cost in self.costs:
				if cost == new_cost:
					return false

		self.costs.append(new_cost)

	def save(self):
		if self.id is not None:
			self.sanitize()
			if not self.validate():
				with db.DBCon.get().cursor() as cursor:
					cursor.execute("DELETE FROM listings WHERE id = {} LIMIT 1".format(self.id))
				return False
			with db.DBCon.get().cursor() as cursor:
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
						if type(value) is bytes:
							value = int(value,2)
						update_columns.append("`"+column+"` = %s")
						update_values.append(value)

				update_sql += ", ".join(update_columns)
				update_sql += " WHERE id = %s LIMIT 1"
				update_values.append(self.id)
				update_value_tuple = tuple(update_values)
				cursor.execute(update_sql, update_value_tuple)

				cursor.execute("SHOW COLUMNS FROM costs")
				table_columns = []
				# TODO: prevent duplicate costs when save() if called multiple times
				for column in cursor:
					if (column["Field"] != "id" and column["Field"] != "date_updated"):
						table_columns.append(column["Field"])
				for cost in self.costs:
					cost.listing_id = self.id
					insert_sql = "INSERT INTO costs "
					insert_columns = []
					insert_placeholders = []
					insert_values = []

					for column in table_columns:
						value = getattr(cost, column)
						if value is not None:
							if type(value) is bytes:
								value = int(value,2)
							insert_columns.append("`"+column+"`")
							insert_placeholders.append("%s")
							insert_values.append(value)
					insert_sql += "("+", ".join(insert_columns)+") VALUES "
					insert_sql += "("+", ".join(insert_placeholders)+")"
					insert_values = tuple(insert_values)
					cursor.execute(insert_sql, insert_values)
		else:
			with db.DBCon.get().cursor() as cursor:
				cursor.execute("SELECT id FROM listings WHERE url = %s", self.url)
				url_listing = cursor.fetchone()
				if (url_listing is not None):
					self.id = url_listing["id"]
				else:
					cursor.execute("INSERT INTO listings (site, url, date_updated) VALUES (%s, %s, NOW())", (self.site, self.url))
					self.id = cursor.lastrowid
		return True
	
	def validate(self):
		required_fields = []
		#required_fields = ['street_address', 'zip', 'city', 'price']
		missing_fields = []
		for field in required_fields:
			if getattr(self,field) is None:
				missing_fields.append(field)
		if len(missing_fields) > 0:
			print("Housing has missing fields:\nid: {}".format(self.id)+"\nURL: {}".format(self.url)+"\nFields: "+", ".join(missing_fields))
			return False
		return True

	def addImage(self, image_url):
		head_check = requests.head(image_url)
		if not head_check.ok or 'Content-Type' not in head_check.headers or not re.match('image', head_check.headers['Content-Type']):
			return False
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
		with db.DBCon.get().cursor() as cursor:
			cursor.execute("SELECT id FROM images WHERE hash_MD5 = %s LIMIT 1", (hash_MD5))
			found = cursor.fetchone()
			if found is not None:
				return False

		with db.DBCon.get().cursor() as cursor:
			# Check if image uuid found in database
			uuid_found = True
			while uuid_found is not None:
				image_id = str(uuid.uuid4())
				cursor.execute("SELECT 1 FROM images WHERE uuid = %s LIMIT 1", (image_id))
				uuid_found = cursor.fetchone()

		image_file = open(r''+setup.getConfig()['screenshot_directory']+image_id+extension, 'bw+')
		image_file.write(image_data)
		image_file.close()

		with db.DBCon.get().cursor() as cursor:
			cursor.execute("INSERT INTO images (listing_id, uuid, hash_MD5, extension, mime_type, original_filename, date_added) VALUES (%s, %s, %s, %s, %s, %s, NOW())", (self.id, image_id, hash_MD5, extension, mime_type, original_filename))

		return True
	
	@classmethod
	def getHousingTypes(cls):
		return {
			'rental': cls.TYPE_OWN_RENTAL,
			'ownership': cls.TYPE_OWN_OWNERSHIP,
			'part_ownership': cls.TYPE_OWN_PART_OWNERSHIP
		}
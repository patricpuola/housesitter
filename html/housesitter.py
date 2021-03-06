#!/usr/bin/python3
import flask
import cairosvg
import sys, math
import io
sys.path.insert(1, r'../modules')
import db
import lang
import setup
import housing
import time
import json
import shutil
import regex
app = flask.Flask(__name__)

def getNavLinks():
	sites = ['map', 'listings', 'language']
	links = []
	links.append({'href':'/', 'text':'Stats'})
	for site in sites:
		links.append({'href':'/'+site, 'text':site.capitalize()})
	return links

def getListings(housing_type = None, count = 20, offset = 0, getCoordinates = False):
	listings = []
	with db.DBCon.get().cursor() as cursor:
		if housing_type is not None:
			cursor.execute("SELECT id, url, site, ownership_type, housing_type, description, street_address, zip, city, suburb, price, country, agency, layout, living_space_m2, total_space_m2, build_year, lat, lng, flags FROM listings WHERE ownership_type = %d ORDER BY date_updated DESC LIMIT %d OFFSET %d" % (housing_type, count, offset))
		else:
			cursor.execute("SELECT id, url, site, ownership_type, housing_type, description, street_address, zip, city, suburb, price, country, agency, layout, living_space_m2, total_space_m2, build_year, lat, lng, flags FROM listings ORDER BY date_updated DESC LIMIT %d OFFSET %d" % (count, offset))		
		
		while True:
			listing = cursor.fetchone()
			if listing == None:
				break
			for prop in listing:
				if listing[prop] == None:
					listing[prop] = ""
			listing['expired'] = listing['flags'] & int(housing.Listing.EXPIRED, 2) > 0
			listings.append(listing)
	return listings

def getImageIds(listing_id: int, limit = None):
	image_ids = []
	with db.DBCon.get().cursor() as cursor:
		if limit is not None:
			cursor.execute("SELECT id FROM images WHERE listing_id = %d LIMIT %d" % (listing_id, limit))
		else:
			cursor.execute("SELECT id FROM images WHERE listing_id = %d" % listing_id)
		images_result = cursor.fetchall()
		for image_res in images_result:
			image_ids.append(image_res['id'])
	return image_ids

def getImageData(image_id: int):
	image_dir = setup.getConfig()['screenshot_directory']
	img_db = db.DBCon.get(persistent=False)
	with img_db.cursor() as cursor:
		cursor.execute("SELECT uuid, extension, mime_type FROM images WHERE id = %d LIMIT 1" % image_id)
		image = cursor.fetchone()
		filename = image['uuid'] + image['extension']
	img_db.close()
	return (setup.ROOT / image_dir / filename, image['mime_type'])

def getStats():
	stats = []
	with db.DBCon.get().cursor() as cursor:
		cursor.execute("SELECT 'Listings' as `stat`, count(id) as `value` FROM listings")
		stats.append(cursor.fetchone())
		cursor.execute("SELECT 'Images' as `stat`, count(id) as `value` FROM images")
		stats.append(cursor.fetchone())
		cursor.execute("SELECT 'Geocodes' as `stat`, count(id) as `value` FROM listings WHERE lat IS NOT NULL AND lng IS NOT NULL")
		stats.append(cursor.fetchone())
	
	total, used, free = shutil.disk_usage("/")
	stats.append({'stat':'Total', 'value':"%d GiB" % (total // (2**30))})
	stats.append({'stat':'Used', 'value':"%d GiB" % (used // (2**30))})
	stats.append({'stat':'Free', 'value':"%d GiB" % (free // (2**30))})

	return stats

def getZoom(lng_range, lat_range):
	def getBaseLog(x, y):
		return math.log(y) / math.log(x)
	LNG_MAX = 80
	LNG_MIN = -180
	LAT_MAX = 90
	LAT_MIN = -90
	range_percentage_lng = lng_range / (abs(LNG_MIN)+LNG_MAX)
	range_percentage_lat = lat_range / (abs(LAT_MIN)+LAT_MAX)
	zoom = abs(getBaseLog(2, range_percentage_lat))
	return zoom

def getListingMarkers():
	markers = None
	with db.DBCon.get().cursor() as cursor:
		cursor.execute("SELECT lng, lat FROM geocodes")
		markers = cursor.fetchall()
	return markers

def getMapStartingPoint():
	starting_point = {'lng':0, 'lat':0, 'zoom': 0}
	with db.DBCon.get().cursor() as cursor:
		cursor.execute("SELECT MIN(lng) as lng_min, MAX(lng) as lng_max, MIN(lat) as lat_min, MAX(lat) as lat_max FROM geocodes")
		map_values = cursor.fetchone()
	if map_values["lng_min"] is not None and map_values["lng_max"] is not None and map_values["lat_min"] is not None and map_values["lat_max"] is not None:
		starting_point['lng'] = (map_values['lng_min'] + map_values['lng_max']) / 2
		starting_point['lat'] = (map_values['lat_min'] + map_values['lat_max']) / 2
		lng_range = map_values['lng_max'] - map_values['lng_min']
		lat_range = map_values['lat_max'] - map_values['lat_min']
		starting_point['zoom'] = getZoom(lng_range, lat_range)
	return starting_point

def appendAnalysis(listings, dataset_analysis = {}):
	if (len(listings) < 1):
		dataset_analysis['price_per_m2_min'] = 0
		dataset_analysis['price_per_m2_max'] = 0
		dataset_analysis['price_min'] = 0
		dataset_analysis['price_max'] = 0
		return
	price_per_m2_min = 0
	price_per_m2_max = 0
	price_max = 0
	price_min = 0
	for listing in listings:
		listing['analysis'] = {}
		if not isinstance(listing['price'], float) or not isinstance(listing['living_space_m2'], int):
			continue
		listing['analysis']['price_per_m2'] = listing['price'] / listing['living_space_m2']
		if price_per_m2_min is None or listing['analysis']['price_per_m2'] < price_per_m2_min:
			price_per_m2_min = listing['analysis']['price_per_m2']
		if price_per_m2_max is None or listing['analysis']['price_per_m2'] > price_per_m2_max:
			price_per_m2_max = listing['analysis']['price_per_m2']

		if price_min is None or listing['price'] < price_min:
			price_min = listing['price']
		if price_max is None or listing['price'] > price_max:
			price_max = listing['price']

	dataset_analysis['price_per_m2_min'] = price_per_m2_min
	dataset_analysis['price_per_m2_max'] = price_per_m2_max
	dataset_analysis['price_min'] = price_min
	dataset_analysis['price_max'] = price_max

	price_per_m2_max_normalized = price_per_m2_max - price_per_m2_min
	price_max_normalized = price_max - price_min
	
	for listing in listings:
		if 'price_per_m2' not in listing['analysis']:
			continue
		price_per_m2_normalized = listing['analysis']['price_per_m2'] - price_per_m2_min
		listing['analysis']['price_per_m2_dataset_relational'] = price_per_m2_normalized / price_per_m2_max_normalized

		price_normalized = listing['price'] - price_min
		listing['analysis']['price_dataset_relational'] = price_normalized / price_max_normalized


def getRGB(value):
	if value is None or value > 100:
		red = 255
		green = 255
		blue = 255
	elif 0 <= value <= 25:
		red = int(value / 25 * 255)
		green = 255
		blue = 0
	elif 25 < value <= 50:
		red = 255
		green = 255 - int((value-25) / 25 * 255)
		blue = 0
	elif 50 < value <= 75:
		red = 255
		green = 0
		blue = int((value-50) / 25 * 255)
	else:
		red = 255 - int((value-75) / 25 * 255)
		green = 0
		blue = 255
	
	return red,green,blue

@app.route('/')
def index():
	return flask.render_template('index.html', nav=getNavLinks(), stats=getStats())

@app.route('/listings')
@app.route('/listings/<int:detail>')
def listings(detail=None):
	listings = None
	if detail is None:
		listings = getListings(None, 20, 0, False)
		for listing in listings:
			listing['images'] = []
			image_ids = getImageIds(listing['id'])
			for image_id in image_ids:
				listing['images'].append({'url':'/image/'+str(image_id), 'id':image_id})
			listing['price'] = 0.0 if len(str(listing['price'])) == 0 else listing['price']
			listing['living_space_m2'] = 0 if len(str(listing['living_space_m2'])) == 0 else listing['living_space_m2']
		   
	return flask.render_template('listings.html', nav=getNavLinks(), listings=listings, detail=detail)

@app.route('/language')
def language():
	translations = lang.Lang.getAll()
	lang_abbr = lang.Lang.getLangAbbr()
	translated_languages = lang.Lang.getLanguages()
	return flask.render_template('language.html', nav=getNavLinks(), translations=translations, lang_abbr=lang_abbr, translated_languages=translated_languages)

@app.route('/language/mgmt/<action>', methods=["POST", "GET"])
@app.route('/language/mgmt/<action>/<value>', methods=["POST", "GET"])
def language_mgmt(action=None, value=None):
	if action is None:
		pass
	if action == 'add_lang' and value is not None:
		if (lang.Lang.addLanguage(value)):
			return flask.redirect(flask.url_for('language'), 303)
		else:
			return "This language column already exists"
	elif action == 'set_translation':   # ajax
		data = flask.request.get_json()
		if (lang.Lang.set(data['key'], data['values'], data['language'])):
			return json.dumps({"response":"OK"})
		else:
			return json.dumps({"response":"ERROR"})
	elif action == 'add_key' and value is not None:
		key = value
		lang.Lang.addKey(key)
		return flask.redirect(flask.url_for('language'), 303)
	elif action == 'delete_key' and value is not None:
		key = value
		lang.Lang.deleteKey(key)
		return flask.redirect(flask.url_for('language'), 303)
	elif action == 'delete_language' and value is not None:
		language = value
		lang.Lang.deleteLanguage(language)
		return flask.redirect(flask.url_for('language'), 303)

@app.route('/image/<int:id>')
def image(id = None):
	(img_path, mime_type) = getImageData(id)
	img_data = None
	with open(img_path, 'rb') as img_file:
		img_data = img_file.read()
	return flask.Response(response=img_data, headers={'Content-type':mime_type}, mimetype=mime_type)

@app.route('/map')
@app.route('/map/<housing_type>')
def map(housing_type = None):
	housing_types = housing.Listing.getHousingTypes()
	housing_type_links = []
	housing_type_links.append({'href': '/map', 'text': 'None'})
	for htype in housing_types:
		housing_type_links.append({'href': '/map/'+htype, 'text': htype.replace('_',' ').capitalize()})
	access_token = setup.getCredentials()['mapbox']['access_token']
	marker_variations = []
	housing_filter = None
	if housing_type in housing_types:
		housing_filter = housing_types[housing_type]
	listings = getListings(housing_filter, 20, 0, True)
	dataset_analysis = {}
	appendAnalysis(listings, dataset_analysis)
	for listing in listings:
		image_ids = getImageIds(listing['id'], 1)
		listing['thumbnail_url'] = None
		if len(image_ids) > 0:
			listing['thumbnail_url'] = '/image/'+str(image_ids[0])
		if 'price_per_m2_dataset_relational' in listing['analysis']:
			listing['analysis']['marker_dot_intensity'] = int(round(listing['analysis']['price_per_m2_dataset_relational']*100,2))
		else:
			listing['analysis']['marker_dot_intensity'] = None #TODO: fix
		
		if 'price_dataset_relational' in listing['analysis']:
			listing['analysis']['marker_intensity'] = int(round(listing['analysis']['price_dataset_relational']*100,2))
		else:
			listing['analysis']['marker_intensity'] = None #TODO: fix
		
		if listing['analysis']['marker_intensity'] is not None and listing['analysis']['marker_dot_intensity'] is not None:
			marker_variation = (listing['analysis']['marker_intensity'],listing['analysis']['marker_dot_intensity'])
			if marker_variation not in marker_variations:
				marker_variations.append(marker_variation)

	return flask.render_template('map.html', nav=getNavLinks(), access_token=access_token, starting_point=getMapStartingPoint(), listings=listings, marker_variations=marker_variations, dataset_analysis=dataset_analysis, housing_type=housing_type, housing_type_links=housing_type_links)

@app.route('/asset/map_marker/')
@app.route('/asset/map_marker/<int:intensity>')
@app.route('/asset/map_marker/<int:intensity>/<int:dot_intensity>')
def asset(intensity = None, dot_intensity = None):
	if not 0 <= intensity <= 100:
		intensity = None
	if not 0 <= dot_intensity <= 100:
		dot_intensity = None
	color = getRGB(intensity)
	dot_color = getRGB(dot_intensity)
	asset = setup.ROOT / "html/static/marker.svg"
	with open(asset, 'r') as asset_file:
		asset_data = asset_file.read()
	asset_data = asset_data.replace('{{ marker_color }}', 'rgb({},{},{})'.format(*color)).replace('{{ dot_color }}', 'rgb({},{},{})'.format(*dot_color))
	png = io.BytesIO()
	cairosvg.svg2png(bytestring=asset_data, write_to=png)
	return flask.Response(response=png.getvalue(), headers={'Content-type':'image/png'}, mimetype='image/png')

@app.route('/migrate')
def migrate():
	# remove this after all migrating done from mysql to mongodb
	with db.DBCon.get().cursor() as cursor:
		cursor.execute("SELECT distinct(`key`) as 'key' from languages WHERE `key` is not null")
		rows = cursor.fetchall()
		keys = []
		for row in rows:
			keys.append(row['key'])
		cursor.execute("SELECT distinct(language) as language from languages WHERE language is not null")
		rows = cursor.fetchall()
		languages = []
		for row in rows:
			languages.append(row['language'])
		list = []
		for key in keys:
			for language in languages:
				obj = {'key':key, 'language': language, 'values':[]}
				cursor.execute("SELECT value FROM languages WHERE `key` = '%s' AND language = '%s' LIMIT 1" % (key, language))
				row = cursor.fetchone()
				if row['value'] is not None:
					value = row['value']
					obj['values'].append(value)
					list.append(obj)
	return "yay"

@app.route('/test')
def test():
	for x in db.MongoCon.get()['languages'].find():
		print(x)
	return "hello world"

if __name__ == '__main__':
	app.debug = True
	app.run(host='10.10.42.3')
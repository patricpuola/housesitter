#!/usr/bin/python3
from flask import Flask, render_template, Response
from cairosvg import svg2png
import sys, math
from io import BytesIO
sys.path.insert(1, r'../modules')
from setup import getConfig, ROOT, getCredentials
from db import DBCon
app = Flask(__name__)

sites = ['map', 'listings']

def getNavLinks():
    links = []
    links.append({'href':'/', 'text':'Stats'})
    for site in sites:
        links.append({'href':'/'+site, 'text':site.capitalize()})
    return links

def getListings(count = 20, offset = 0, getCoordinates = False):
    listings = []
    with DBCon.get().cursor() as cursor:
        cursor.execute("SELECT id, url, site, housing_type, description,  street_address, zip, city, suburb, price, country, agency, layout, living_space_m2, total_space_m2, build_year FROM listings ORDER BY date_updated DESC LIMIT %d OFFSET %d" % (count, offset))
        with DBCon.get().cursor() as geo_cursor:
            while True:
                listing = cursor.fetchone()
                if listing == None:
                    break
                listing["lng"] = None
                listing["lat"] = None
                if getCoordinates is True:
                    full_address = listing["street_address"]+", "+str(listing["zip"])+" "+listing["city"]
                    geo_cursor.execute("SELECT lat, lng FROM geocodes WHERE query = '{}' LIMIT 1".format(full_address))
                    coords = geo_cursor.fetchone()
                    if coords:
                        listing["lng"] = coords['lng']
                        listing["lat"] = coords['lat']
                listings.append(listing)
    return listings

def getImageIds(listing_id: int, limit = None):
    image_ids = []
    with DBCon.get().cursor() as cursor:
        if limit is not None:
            cursor.execute("SELECT id FROM images WHERE listing_id = %d LIMIT %d" % (listing_id, limit))
        else:
            cursor.execute("SELECT id FROM images WHERE listing_id = %d" % listing_id)
        images_result = cursor.fetchall()
        for image_res in images_result:
            image_ids.append(image_res['id'])
    return image_ids

def getImageData(image_id: int):
    image_dir = getConfig()['screenshot_directory']
    img_db = DBCon.get(persistent=False)
    with img_db.cursor() as cursor:
        cursor.execute("SELECT uuid, extension, mime_type FROM images WHERE id = %d LIMIT 1" % image_id)
        image = cursor.fetchone()
        filename = image['uuid'] + image['extension']
    img_db.close()
    return (ROOT / image_dir / filename, image['mime_type'])

def getStats():
    stats = []
    with DBCon.get().cursor() as cursor:
        cursor.execute("SELECT 'Listings' as `stat`, count(id) as `value` FROM listings")
        stats.append(cursor.fetchone())
        cursor.execute("SELECT 'Images' as `stat`, count(id) as `value` FROM images")
        stats.append(cursor.fetchone())
        cursor.execute("SELECT 'Geocodes' as `stat`, count(id) as `value` FROM geocodes")
        stats.append(cursor.fetchone())
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
    with DBCon.get().cursor() as cursor:
        cursor.execute("SELECT lng, lat FROM geocodes")
        markers = cursor.fetchall()
    return markers

def getMapStartingPoint():
    starting_point = {'lng':None, 'lat':None, 'zoom': 9}
    with DBCon.get().cursor() as cursor:
        cursor.execute("SELECT MIN(lng) as lng_min, MAX(lng) as lng_max, MIN(lat) as lat_min, MAX(lat) as lat_max FROM geocodes")
        map_values = cursor.fetchone()
    if map_values:
        starting_point['lng'] = (map_values['lng_min'] + map_values['lng_max']) / 2
        starting_point['lat'] = (map_values['lat_min'] + map_values['lat_max']) / 2
        lng_range = map_values['lng_max'] - map_values['lng_min']
        lat_range = map_values['lat_max'] - map_values['lat_min']
        starting_point['zoom'] = getZoom(lng_range, lat_range)
        print(starting_point)
    return starting_point

@app.route('/')
def index():
    return render_template('index.html', nav=getNavLinks(), stats=getStats())

@app.route('/listings')
@app.route('/listings/<int:detail>')
def listings(detail=None):
    listings = None
    if detail is None:
        listings = getListings()
        for listing in listings:
            listing['images'] = []
            image_ids = getImageIds(listing['id'])
            for image_id in image_ids:
                listing['images'].append({'url':'/image/'+str(image_id), 'id':image_id})
           
    return render_template('listings.html', nav=getNavLinks(), listings=listings, detail=detail)

@app.route('/image/<int:id>')
def image(id = None):
    (img_path, mime_type) = getImageData(id)
    img_data = None
    with open(img_path, 'rb') as img_file:
        img_data = img_file.read()
    return Response(response=img_data, headers={'Content-type':mime_type}, mimetype=mime_type)

@app.route('/map')
def map():
    access_token = getCredentials()['mapbox']['access_token']
    listings = getListings(20, 0, True)
    for listing in listings:
        image_ids = getImageIds(listing['id'], 1)
        listing['thumbnail_url'] = None
        if len(image_ids) > 0:
            listing['thumbnail_url'] = '/image/'+str(image_ids[0])
    return render_template('map.html', nav=getNavLinks(), access_token=access_token, starting_point=getMapStartingPoint(), listings=listings)

@app.route('/asset/map_marker/<int:intensity>')
def asset(intensity = 0):
    red = 255 if intensity >= 50 else (intensity/50) * 255
    green = 255 if intensity <= 50 else 255 - ((intensity-50)/50) * 255
    asset = ROOT / "html/static/marker.svg"
    with open(asset, 'r') as asset_file:
        asset_data = asset_file.read()
    asset_data = asset_data.replace('{{ marker_color }}', 'rgb({},{},0)'.format(red,green)).replace('{{ dot_color }}', 'white')
    png = BytesIO()
    svg2png(bytestring=asset_data, write_to=png)
    return Response(response=png.getvalue(), headers={'Content-type':'image/png'}, mimetype='image/png')

if __name__ == '__main__':
    app.debug = True
    app.run(host='10.10.42.3')
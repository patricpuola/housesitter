#!/usr/bin/python3
from flask import Flask, render_template, Response
import sys
sys.path.insert(1, r'../modules')
from setup import getConfig
from setup import ROOT
from db import DBCon
app = Flask(__name__)

sites = ['map', 'listings']

def getNavLinks():
    links = []
    links.append({'href':'/', 'text':'Stats'})
    for site in sites:
        links.append({'href':'/'+site, 'text':site.capitalize()})
    return links

def getListings(count = 20, offset = 0):
    with DBCon.get().cursor() as cursor:
        cursor.execute("SELECT id, url, site, housing_type, street_address, zip, city, suburb, price, country, agency, layout, living_space_m2, total_space_m2, build_year FROM listings ORDER BY date_updated DESC LIMIT %d OFFSET %d" % (count, offset))
        listings = cursor.fetchall()
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
    with DBCon.get().cursor() as cursor:
        cursor.execute("SELECT uuid, extension, mime_type FROM images WHERE id = %d LIMIT 1" % image_id)
        image = cursor.fetchone()
        filename = image['uuid'] + image['extension']
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
    return render_template('map.html', nav=getNavLinks())

if __name__ == '__main__':
    app.debug = True
    app.run(host='10.10.42.3')
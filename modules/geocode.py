#!/usr/bin/python3
import setup, db
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

    	results = cls.geocoder.geocode(query)
    	result = results[0]

    	geo = {}
    	geo['lng'] = result['geometry']['lng']
    	geo['lat'] = result['geometry']['lat']
    	geo['confidence'] = result['confidence']
    	if 'suburb' in result['components']:
    		geo['suburb'] = result['components']['suburb']
    	if 'city' in result['components']:
    		geo['city'] = result['components']['city']
    	if 'town' in result['components']:
    		geo['city'] = result['components']['town']

    	return geo

    # TODO: error handling / return False
    @classmethod
    def initCheck(cls):
        if cls.geocoder is None:
            cls.geocoder = OpenCageGeocode(setup.getCredentials()['opencage']['api_key'])
        return True

    

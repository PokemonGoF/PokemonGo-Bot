

import googlemaps
import json
import threading
import time
from pgoapi import PGoApi
from pgoapi.utilities import f2i, h2f
from math import radians, sqrt, sin, cos, atan2

GOOGLEMAPS_KEY = "AIzaSyAZzeHhs-8JZ7i18MjFuM35dJHq70n3Hx4"

working_thread=None
gmaps = googlemaps.Client(key=GOOGLEMAPS_KEY)

def convert_toposition(lat,lng,art):
    return (lat, lng, art)

def search_seen_fort(fort,api,position):
	lat=fort['latitude']
	lng=fort['longitude']
	fortID=fort['id']
	distant=geocalc(position[0],position[1],lat,lng)*1000
	print('distant is {}m'.format(distant))
	if distant > 10:
		print('need setup the postion to farming fort')
		position=convert_toposition(lat, lng, 0.0)
		print(position,fortID)
		api.set_position(*position)
		api.player_update(latitude=lat,longitude=lng)
		response_dict = api.call()
		print('Response dictionary 1: \n\r{}'.format(json.dumps(response_dict, indent=2)))

		api.fort_details(fort_id=fort['id'], latitude=position[0], longitude=position[1])
		response_dict = api.call()
		print('Response dictionary 2: \n\r{}'.format(json.dumps(response_dict, indent=2)))
		time.sleep(2)
		api.fort_search(fort_id=fort['id'], fort_latitude=lat, fort_longitude=lng, player_latitude=f2i(position[0]), player_longitude=f2i(position[1]))
		response_dict = api.call()
		print('Response dictionary 3: \n\r{}'.format(json.dumps(response_dict, indent=2)))
		time.sleep(8)
def geocalc(lat1, lon1, lat2, lon2):
    lat1 = radians(lat1)
    lon1 = radians(lon1)
    lat2 = radians(lat2)
    lon2 = radians(lon2)

    dlon = lon1 - lon2

    EARTH_R = 6372.8

    y = sqrt(
        (cos(lat2) * sin(dlon)) ** 2
        + (cos(lat1) * sin(lat2) - sin(lat1) * cos(lat2) * cos(dlon)) ** 2
        )
    x = sin(lat1) * sin(lat2) + cos(lat1) * cos(lat2) * cos(dlon)
    c = atan2(y, x)
    return EARTH_R * c

def start_working():
    global working_thread

    print('register_background_thread: queueing')
    working_thread = threading.Timer(30, pokemon_working)  # delay, in seconds

    working_thread.daemon = True
    working_thread.name = 'working_thread'
    working_thread.start()
def pokemon_working():
    directions_result = gmaps.directions((49.004, 8.456),
                                         (49.004, 8.469),
                                         mode="walking")
    if directions_result and len(directions_result) > 0:
        """
        print directions_result[0]
        for ka, va in directions_result[0].iteritems():
            print ka+'\n'
            print va
        exit(0)
        """
        steps = directions_result[0]['legs'][0]['steps']
        print len(steps)
        for index, item in enumerate(steps):
            print index,item['start_location'],'-->',item['end_location'],'duration: ',item['duration']['value'],'sec'
#start_working();

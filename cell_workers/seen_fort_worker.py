import json
import time
from math import radians, sqrt, sin, cos, atan2
from pgoapi.utilities import f2i, h2f

class SeenFortWorker(object):

    def __init__(self, fort, bot):
        self.fort = fort
        self.api = bot.api
        self.position = bot.position
        self.config = bot.config
        self.rest_time = 50

    def work(self):
        lat = self.fort['latitude']
        lng = self.fort['longitude']
        fortID = self.fort['id']
        distant = self._geocalc(self.position[0], self.position[1], lat, lng) * 1000

        print('distant is {}m'.format(distant))
        if distant > 10:
            print('need walk to farming fort position')
            position = (lat, lng, 0.0)
            print(position,fortID)
            if self.config.walk > 0:
                self.api.walk(self.config.walk, *position)
            else:
                self.api.set_position(*position)
            self.api.player_update(latitude=lat,longitude=lng)
            response_dict = self.api.call()
            print('Response dictionary 1: \n\r{}'.format(json.dumps(response_dict, indent=2)))
            time.sleep(1.2)

        self.api.fort_details(fort_id=self.fort['id'], latitude=position[0], longitude=position[1])
        response_dict = self.api.call()
        print('Response dictionary 2: \n\r{}'.format(json.dumps(response_dict, indent=2)))
        time.sleep(2)
        self.api.fort_search(fort_id=self.fort['id'], fort_latitude=lat, fort_longitude=lng, player_latitude=f2i(position[0]), player_longitude=f2i(position[1]))
        response_dict = self.api.call()
        print('Response dictionary 3: \n\r{}'.format(json.dumps(response_dict, indent=2)))
        if 'responses' in response_dict and \
            'FORT_SEARCH' in response_dict['responses']:
            if 'chain_hack_sequence_number' in response_dict['responses']['FORT_SEARCH']:
                time.sleep(2)
                return response_dict['responses']['FORT_SEARCH']['chain_hack_sequence_number']
            else:
                print('may search too often, lets have a rest')
                return 11
        time.sleep(8)
        return 0

    def _geocalc(self, lat1, lon1, lat2, lon2):
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

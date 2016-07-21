import logging
import json
import time
from math import radians, sqrt, sin, cos, atan2
from pgoapi.utilities import f2i

class SeenFortWorker(object):

    def __init__(self, fort, bot):
        self.fort = fort
        self.api = bot.api
        self.position = bot.position
        self.config = bot.config
        self.rest_time = 50
        self.log = logging.getLogger(__name__)
        self.item_list = json.load(open('items.json'))

    def work(self):
        lat = self.fort['latitude']
        lng = self.fort['longitude']
        fortID = self.fort['id']
        distance = self._geocalc(self.position[0], self.position[1], lat, lng) * 1000

        self.log.info('Found fort {} at distance {}m'.format(fortID, distance))
        if distance > 10:
            self.log.debug('Need to move closer to Pokestop')
            position = (lat, lng, 0.0)
            if self.config.walk > 0:
                self.api.walk(self.config.walk, *position)
            else:
                self.api.set_position(*position)
            self.api.player_update(latitude=lat,longitude=lng)
            response_dict = self.api.call()
            self.log.debug('Arrived at Pokestop')
            time.sleep(1.2)

        self.api.fort_details(fort_id=self.fort['id'], latitude=position[0], longitude=position[1])
        response_dict = self.api.call()
        fort_details = response_dict['responses']['FORT_DETAILS']
        self.log.debug('Now at Pokestop "%s" - Spinning',  fort_details['name'])
        time.sleep(2)
        self.api.fort_search(fort_id=self.fort['id'], fort_latitude=lat, fort_longitude=lng, player_latitude=f2i(position[0]), player_longitude=f2i(position[1]))
        response_dict = self.api.call()
        if 'responses' in response_dict and \
            'FORT_SEARCH' in response_dict['responses']:

            spin_details = response_dict['responses']['FORT_SEARCH']
            if spin_details['result'] == 1:
                self.log.info("Loot:")
                self.log.info('Experience: %s xp', spin_details.get('experience_awarded', 0))
                items_awarded = spin_details.get('items_awarded', [])
                for item in items_awarded:
                    item_id = str(item['item_id'])
                    self.log.info('%sx %s', item['item_count'], self.item_list[item_id])
            elif spin_details['result'] == 2:
                self.log.info("Pokestop out of range")
            elif spin_details['result'] == 3:
                self.log.info("Pokestop on cooldown")
            elif spin_details['result'] == 4:
                self.log.info("Inventory is full!")

            if 'chain_hack_sequence_number' in response_dict['responses']['FORT_SEARCH']:
                time.sleep(2)
                return response_dict['responses']['FORT_SEARCH']['chain_hack_sequence_number']
            else:
                self.log.info('may search too often, lets have a rest')
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

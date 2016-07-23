# -*- coding: utf-8 -*-

import json
import time
import pprint

from math import ceil
from s2sphere import CellId, LatLng
from google.protobuf.internal import encoder

from human_behaviour import sleep, random_lat_long_delta
from cell_workers.utils import distance, i2f, format_time

from pgoapi.utilities import f2i, h2f
import logger


class Stepper(object):
    def __init__(self, bot):
        self.bot = bot
        self.api = bot.api
        self.config = bot.config

        self.pos = 1
        self.x = 0
        self.y = 0
        self.dx = 0
        self.dy = -1
        self.steplimit = self.config.max_steps
        self.steplimit2 = self.steplimit**2
        self.origin_lat = self.bot.position[0]
        self.origin_lon = self.bot.position[1]

    def take_step(self):
        position = (self.origin_lat, self.origin_lon, 0.0)

        self.api.set_position(*position)

        for step in range(self.steplimit2):
            # starting at 0 index
            logger.log('[#] Scanning area for objects ({} / {})'.format(
                (step + 1), self.steplimit**2))
            if self.config.debug:
                logger.log(
                    'steplimit: {} x: {} y: {} pos: {} dx: {} dy {}'.format(
                        self.steplimit2, self.x, self.y, self.pos, self.dx,
                        self.dy))
            # Scan location math
            if -self.steplimit2 / 2 < self.x <= self.steplimit2 / 2 and -self.steplimit2 / 2 < self.y <= self.steplimit2 / 2:
                position = (self.x * 0.0025 + self.origin_lat,
                            self.y * 0.0025 + self.origin_lon, 0)
                if self.config.walk > 0:
                    self._walk_to(self.config.walk, *position)
                else:
                    self.api.set_position(*position)
                print('[#] {}'.format(position))
            if self.x == self.y or self.x < 0 and self.x == -self.y or self.x > 0 and self.x == 1 - self.y:
                (self.dx, self.dy) = (-self.dy, self.dx)

            (self.x, self.y) = (self.x + self.dx, self.y + self.dy)

            self._work_at_position(position[0], position[1], position[2], True)
            sleep(10)

    def _walk_to(self, speed, lat, lng, alt):
        dist = distance(
            i2f(self.api._position_lat), i2f(self.api._position_lng), lat, lng)
        steps = (dist + 0.0) / (speed + 0.0)  # may be rational number
        intSteps = int(steps)
        residuum = steps - intSteps
        logger.log('[#] Walking from ' + str((i2f(self.api._position_lat), i2f(
            self.api._position_lng))) + " to " + str(str((lat, lng))) +
                   " for approx. " + str(format_time(ceil(steps))))
        if steps != 0:
            dLat = (lat - i2f(self.api._position_lat)) / steps
            dLng = (lng - i2f(self.api._position_lng)) / steps

            for i in range(intSteps):
                cLat = i2f(self.api._position_lat) + \
                    dLat + random_lat_long_delta()
                cLng = i2f(self.api._position_lng) + \
                    dLng + random_lat_long_delta()
                self.api.set_position(cLat, cLng, alt)
                self.bot.heartbeat()
                sleep(1)  # sleep one second plus a random delta
                self._work_at_position(
                    i2f(self.api._position_lat), i2f(self.api._position_lng),
                    alt, False)

            self.api.set_position(lat, lng, alt)
            self.bot.heartbeat()
            logger.log("[#] Finished walking")

    def _work_at_position(self, lat, lng, alt, pokemon_only=False):
        cellid = self._get_cellid(lat, lng)
        timestamp = [0, ] * len(cellid)
        self.api.get_map_objects(latitude=f2i(lat),
                                 longitude=f2i(lng),
                                 since_timestamp_ms=timestamp,
                                 cell_id=cellid)

        response_dict = self.api.call()
        # pprint.pprint(response_dict)
        # Passing Variables through a file
        if response_dict and 'responses' in response_dict:
            if 'GET_MAP_OBJECTS' in response_dict['responses']:
                if 'map_cells' in response_dict['responses'][
                        'GET_MAP_OBJECTS']:
                    with open('web/location-%s.json' %
                              (self.config.username), 'w') as outfile:
                        json.dump(
                            {'lat': lat,
                             'lng': lng,
                             'cells': response_dict[
                                 'responses']['GET_MAP_OBJECTS']['map_cells']},
                            outfile)
                    with open('data/last-location-%s.json' %
                              (self.config.username), 'w') as outfile:
                        outfile.truncate()
                        json.dump({'lat': lat, 'lng': lng}, outfile)
        if response_dict and 'responses' in response_dict:
            if 'GET_MAP_OBJECTS' in response_dict['responses']:
                if 'status' in response_dict['responses']['GET_MAP_OBJECTS']:
                    if response_dict['responses']['GET_MAP_OBJECTS'][
                            'status'] is 1:
                        map_cells = response_dict['responses'][
                            'GET_MAP_OBJECTS']['map_cells']
                        position = (lat, lng, alt)
                    # Sort all by distance from current pos- eventually this should build graph & A* it
                    # print(map_cells)
                    #print( s2sphere.from_token(x['s2_cell_id']) )
                    map_cells.sort(key=lambda x: distance(lat, lng, x['forts'][0]['latitude'], x[
                                   'forts'][0]['longitude']) if 'forts' in x and x['forts'] != [] else 1e6)
                    for cell in map_cells:
                        self.bot.work_on_cell(cell, position, pokemon_only)

    def _get_cellid(self, lat, long, radius=10):
        origin = CellId.from_lat_lng(LatLng.from_degrees(lat, long)).parent(15)
        walk = [origin.id()]

        # 10 before and 10 after
        next = origin.next()
        prev = origin.prev()
        for i in range(radius):
            walk.append(prev.id())
            walk.append(next.id())
            next = next.next()
            prev = prev.prev()
        return sorted(walk)

    def _encode(self, cellid):
        output = []
        encoder._VarintEncoder()(output.append, cellid)
        return ''.join(output)

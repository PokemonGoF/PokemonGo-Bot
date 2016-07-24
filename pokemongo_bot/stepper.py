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
        self.cells = None

        self.pos = 1
        self.x = 0
        self.y = 0
        self.dx = 0
        self.dy = -1
        self.steplimit = self.config.max_steps
        self.steplimit2 = self.steplimit**2
        self.current_lat = self.bot.position[0]
        self.current_lon = self.bot.position[1]
        self.position = (self.current_lat, self.current_lon)

    def take_step(self):
        self.position = (self.x * 0.0025 + self.current_lat, self.y * 0.0025 + self.current_lon, 0)
        self.current_lat = self.position[0]
        self.current_lon = self.position[1]

        if self.config.walk > 0:
            self._walk_to(*self.position)
        else:
            self.set_position(*self.position)
        if self.x == self.y or self.x < 0 and self.x == -self.y or self.x > 0 and self.x == 1 - self.y:
            (self.dx, self.dy) = (-self.dy, self.dx)

        (self.x, self.y) = (self.x + self.dx, self.y + self.dy)

    def set_position(self, lat, lon, alt=0, update_cells=True):
        self.api.set_position(lat, lon, alt)
        self.position = (lat, lon)
        self.bot.position = self.position
        if update_cells:
            self.get_cells()

    def _walk_to(self, lat, lng, alt): #walkto_andupdate cells
        dist = distance(
            i2f(self.api._position_lat), i2f(self.api._position_lng), lat, lng)
        steps = (dist + 0.0) / (self.config.walk + 0.0)  # may be rational number
        intSteps = int(steps)
        residuum = steps - intSteps
        if steps != 0:
            logger.log('[#] Walking from ' + str((i2f(self.api._position_lat), i2f(
                self.api._position_lng))) + " to " + str(str((lat, lng))) +
                       " for approx. " + str(format_time(ceil(steps))))

            dLat = (lat - i2f(self.api._position_lat)) / steps
            dLng = (lng - i2f(self.api._position_lng)) / steps

            for i in range(intSteps):
                cLat = i2f(self.api._position_lat) + \
                    dLat + random_lat_long_delta()
                cLng = i2f(self.api._position_lng) + \
                    dLng + random_lat_long_delta()
                self.set_position(cLat, cLng, alt, update_cells=False)
                self.bot.heartbeat()
                sleep(1)  # sleep one second plus a random delta

            self.set_position(lat, lng, alt)
            self.bot.heartbeat()
            logger.log("[#] Finished walking")
        else:
            self.get_cells()

    def get_cells(self):
        timestamp = "\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000"
        cellid = self._get_cellid(self.position[0], self.position[1])
        self.api.get_map_objects(latitude=f2i(self.position[0]), longitude=f2i(self.position[1]),
                                     since_timestamp_ms=timestamp, cell_id=cellid)
        response_dict = self.api.call()
        self.cells=response_dict['responses']['GET_MAP_OBJECTS']['map_cells']

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

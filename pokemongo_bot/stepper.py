import json
import time

from math import ceil
from s2sphere import CellId, LatLng
from google.protobuf.internal import encoder

from human_behaviour import sleep, random_lat_long_delta
from cell_workers.utils import distance, i2f

from pgoapi.utilities import f2i, h2f


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
        self.steplimit=self.config.maxsteps
        self.steplimit2 = self.steplimit**2
        self.origin_lat = self.bot.position[0]
        self.origin_lon = self.bot.position[1]

    def take_step(self):
        position=(self.origin_lat,self.origin_lon,0.0)

        self.api.set_position(*position)

        for step in range(self.steplimit2):
            #starting at 0 index
            print('[#] Scanning area for objects ({} / {})'.format((step+1), self.steplimit**2))
            if self.config.debug:
                print('steplimit: {} x: {} y: {} pos: {} dx: {} dy {}'.format(self.steplimit2, self.x, self.y, self.pos, self.dx, self.dy))
            # Scan location math
            if -self.steplimit2 / 2 < self.x <= self.steplimit2 / 2 and -self.steplimit2 / 2 < self.y <= self.steplimit2 / 2:
                position = (self.x * 0.0025 + self.origin_lat, self.y * 0.0025 + self.origin_lon, 0)
                if self.config.walk > 0:
                    self._walk_to(self.config.walk, *position)
                else:
                    self.api.set_position(*position)
                print(position)
            if self.x == self.y or self.x < 0 and self.x == -self.y or self.x > 0 and self.x == 1 - self.y:
                (self.dx, self.dy) = (-self.dy, self.dx)

            (self.x, self.y) = (self.x + self.dx, self.y + self.dy)

            # get map objects call
            # ----------------------

            cellid = self._get_cellid(position[0], position[1])
            timestamp = [0,] * len(cellid)
            self.api.get_map_objects(latitude=f2i(position[0]), longitude=f2i(position[1]), since_timestamp_ms=timestamp, cell_id=cellid)
            with open('location.json', 'w') as outfile:
                json.dump({'lat': position[0], 'lng': position[1]}, outfile)

            response_dict = self.api.call()
            if response_dict and 'responses' in response_dict and \
                'GET_MAP_OBJECTS' in response_dict['responses'] and \
                'status' in response_dict['responses']['GET_MAP_OBJECTS'] and \
                response_dict['responses']['GET_MAP_OBJECTS']['status'] is 1:
                map_cells=response_dict['responses']['GET_MAP_OBJECTS']['map_cells']
                for cell in map_cells:
                    self.bot.work_on_cell(cell,position)
            sleep(10)

    def _walk_to(self, speed, lat, lng, alt):
        dist = distance(i2f(self.api._position_lat), i2f(self.api._position_lng), lat, lng)
        steps = (dist+0.0)/(speed+0.0) # may be rational number
        intSteps = int(steps)
        residuum = steps - intSteps
        print '[#] Walking from ' + str((i2f(self.api._position_lat), i2f(self.api._position_lng))) + " to " + str(str((lat, lng))) + " for approx. " + str(ceil(steps)) + " seconds"
        if steps != 0:
            dLat = (lat - i2f(self.api._position_lat)) / steps
            dLng = (lng - i2f(self.api._position_lng)) / steps

            for i in range(intSteps):
                self.api.set_position(i2f(self.api._position_lat) + dLat + random_lat_long_delta(), i2f(self.api._position_lng) + dLng + random_lat_long_delta(), alt)
                self.bot.heartbeat()
                sleep(1) # sleep one second plus a random delta

            self.api.set_position(lat, lng, alt)
            self.bot.heartbeat()
        print "[#] Finished walking"

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

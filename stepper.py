import time

from s2sphere import CellId, LatLng
from google.protobuf.internal import encoder

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
    def walking_hook(own,i):
        print '\rwalking hook ',i,
    def take_step(self):
        position=(self.origin_lat,self.origin_lon,0.0)
        for step in range(self.steplimit2):
            #starting at 0 index
            print('[#] Scanning area for objects ({} / {})'.format((step+1), self.steplimit**2))

            # get map objects call
            # ----------------------
            timestamp = "\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000"
            cellid = self._get_cellid(position[0], position[1])
            self.api.get_map_objects(latitude=f2i(position[0]), longitude=f2i(position[1]), since_timestamp_ms=timestamp, cell_id=cellid)

            response_dict = self.api.call()
            #print('Response dictionary: \n\r{}'.format(json.dumps(response_dict, indent=2)))
            if response_dict and 'responses' in response_dict and \
                'GET_MAP_OBJECTS' in response_dict['responses'] and \
                'status' in response_dict['responses']['GET_MAP_OBJECTS'] and \
                response_dict['responses']['GET_MAP_OBJECTS']['status'] is 1:
                #print('got the maps')
                map_cells=response_dict['responses']['GET_MAP_OBJECTS']['map_cells']
                print('map_cells are {}'.format(len(map_cells)))
                for cell in map_cells:
                    self.bot.work_on_cell(cell,position)

            if self.config.debug:
                print('steplimit: {} x: {} y: {} pos: {} dx: {} dy {}'.format(self.steplimit2, self.x, self.y, self.pos, self.dx, self.dy))
            # Scan location math
            if -self.steplimit2 / 2 < self.x <= self.steplimit2 / 2 and -self.steplimit2 / 2 < self.y <= self.steplimit2 / 2:
                position = (self.x * 0.0025 + self.origin_lat, self.y * 0.0025 + self.origin_lon, 0)
                if self.config.walk > 0:
                    self.api.walk(self.config.walk, *position,walking_hook=self.walking_hook)
                else:
                    self.api.set_position(*position)
                print(position)
            if self.x == self.y or self.x < 0 and self.x == -self.y or self.x > 0 and self.x == 1 - self.y:
                (self.dx, self.dy) = (-self.dy, self.dx)

            (self.x, self.y) = (self.x + self.dx, self.y + self.dy)
            time.sleep(10)

    def _get_cellid(self, lat, long):
        origin = CellId.from_lat_lng(LatLng.from_degrees(lat, long)).parent(15)
        walk = [origin.id()]

        # 10 before and 10 after
        next = origin.next()
        prev = origin.prev()
        for i in range(10):
            walk.append(prev.id())
            walk.append(next.id())
            next = next.next()
            prev = prev.prev()
        return ''.join(map(self._encode, sorted(walk)))

    def _encode(self, cellid):
        output = []
        encoder._VarintEncoder()(output.append, cellid)
        return ''.join(output)

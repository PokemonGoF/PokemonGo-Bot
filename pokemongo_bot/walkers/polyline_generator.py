import time
from itertools import chain
from math import ceil

import haversine
import polyline
import requests

class PolylineObjectHandler:
    '''
    Does this need to be a class?
    More like a namespace...
    '''
    _cache = None
    _instability = 0
    _run = False

    @staticmethod
    def cached_polyline(origin, destination, speed):
        '''
        Google API has limits, so we can't generate new Polyline at every tick...
        '''

        # _cache might be None...
        is_old_cache = lambda : tuple(origin) != PolylineObjectHandler._cache.get_last_pos()
        new_dest_set = lambda : tuple(destination) != PolylineObjectHandler._cache.destination

        if PolylineObjectHandler._run and (not is_old_cache()):
            # bot used to have struggle with making a decision.
            PolylineObjectHandler._instability -= 1
            if PolylineObjectHandler._instability <= 0:
                PolylineObjectHandler._instability = 0
                PolylineObjectHandler._run = False
            pass # use current cache
        elif None == PolylineObjectHandler._cache or is_old_cache() or new_dest_set():
            # no cache, old cache or new destination set by bot, so make new polyline
            PolylineObjectHandler._instability += 2
            if 10 <= PolylineObjectHandler._instability:
                PolylineObjectHandler._run = True
                PolylineObjectHandler._instability = 20 # next N moves use same cache

            PolylineObjectHandler._cache = Polyline(origin, destination, speed)
        else:
            # valid cache found
            PolylineObjectHandler._instability -= 1
            PolylineObjectHandler._instability = max(PolylineObjectHandler._instability, 0)
            pass # use current cache
        return PolylineObjectHandler._cache


class Polyline(object):
    def __init__(self, origin, destination, speed):
        self.DIRECTIONS_API_URL='https://maps.googleapis.com/maps/api/directions/json?mode=walking'
        self.origin = origin
        self.destination = tuple(destination)
        self.DIRECTIONS_URL = '{}&origin={}&destination={}'.format(self.DIRECTIONS_API_URL,
                '{},{}'.format(*self.origin),
                '{},{}'.format(*self.destination))
        
        self.directions_response = requests.get(self.DIRECTIONS_URL).json()
        try:
        # Polyline walker starts teleporting after reaching api query limit.
        # throw error here atm, catch it at factory and return StepWalker
        #
        # In case of API limit reached we get back we get a status 200 code with an empty routes []
        #
        # {u'error_message': u'You have exceeded your rate-limit for this API.',
        #  u'routes': [],
        #  u'status': u'OVER_QUERY_LIMIT'
        # }

            self.polyline_points = [x['polyline']['points'] for x in
                                    self.directions_response['routes'][0]['legs'][0]['steps']]
        # This handles both cases:
        # a) the above API Quota reached self.directions_response['routes'] = []
        # b) ZERO_RESULTS {
        #    "geocoded_waypoints" : [ {}, {} ],
        #    "routes" : [],
        #    "status" : "ZERO_RESULTS"
        # }
        except IndexError:
            self.polyline_points = self.directions_response['routes']
            raise # catch at factory atm...
        self.points = [self.origin] + self.get_points(self.polyline_points) + [self.destination]
        self.speed = float(speed)
        self.lat, self.long = self.points[0][0], self.points[0][1]
        self.polyline = self.combine_polylines(self.points)
        self.elevation_samples = int(min(self.get_total_distance(self.points)/self.speed +1, 512))
        self.ELEVATION_API_URL='https://maps.googleapis.com/maps/api/elevation/json?path=enc:'
        self.ELEVATION_URL = '{}{}&samples={}'.format(self.ELEVATION_API_URL,
                                                      self.polyline, self.elevation_samples)
        self.elevation_response = requests.get(self.ELEVATION_URL).json()
        self.polyline_elevations = [x['elevation'] for x in self.elevation_response['results']]
        self._timestamp = time.time()
        self.is_paused = False
        self._last_paused_timestamp = None
        self._paused_total = 0.0
        self._last_pos = (None, None)

    def reset_timestamps(self):
        self._timestamp = time.time()
        self.is_paused = False
        self._last_paused_timestamp = None
        self._paused_total = 0.0

    def get_points(self, polyline_points):
        crd_points = []
        for points in polyline_points:
            crd_points += polyline.decode(points)
        crd_points = [x for n,x in enumerate(crd_points) if x not in crd_points[:n]]
        return crd_points

    def combine_polylines(self, points):
        return polyline.encode(points)

    def pause(self):
        if not self.is_paused:
            self.is_paused = True
            self._last_paused_timestamp = time.time()

    def unpause(self):
        if self.is_paused:
            self.is_paused = False
            self._paused_total += time.time() - self._last_paused_timestamp
            self._last_paused_timestamp = None

    def walk_steps(self, points):
        if points:
            steps = zip(chain([points[0]], points),
                             chain(points, [points[-1]]))
            steps = filter(None, [(o, d) if o != d else None for o, d in steps])
            # consume the filter as list https://github.com/th3w4y/PokemonGo-Bot/issues/27
            return list(steps)
        else:
            return []

    def get_alt(self):
        max_nr_samples = 512.0
        total_seconds = self.get_total_distance(self.points)/self.speed
        if total_seconds >= max_nr_samples:
            conversion_factor = max_nr_samples/total_seconds
        else:
            conversion_factor = 1
        if not self.is_paused:
            time_passed = time.time()
        else:
            time_passed = self._last_paused_timestamp
        seconds_passed = abs(time_passed - self._timestamp - self._paused_total)
        elevation_index = int(seconds_passed*conversion_factor)
        try:
            return round(self.polyline_elevations[elevation_index], 2)
        except IndexError:
            return round(self.polyline_elevations[-1], 2)

    def get_pos(self):
        walked_distance = 0.0
        if not self.is_paused:
            time_passed = time.time()
        else:
            time_passed = self._last_paused_timestamp
        time_passed_distance = self.speed * abs(time_passed - self._timestamp - self._paused_total)
        # check if there are any steps to take https://github.com/th3w4y/PokemonGo-Bot/issues/27
        if self.walk_steps(self.points):
            steps_dict = {}
            for step in self.walk_steps(self.points):
                walked_distance += haversine.haversine(*step)*1000
                steps_dict[walked_distance] = step
            for walked_end_step in sorted(steps_dict.keys()):
                if walked_end_step >= time_passed_distance:
                    break
            step_distance = haversine.haversine(*steps_dict[walked_end_step])*1000
            if walked_end_step >= time_passed_distance:
                percentage_walked = (time_passed_distance - (walked_end_step - step_distance)) / step_distance
            else:
                percentage_walked = 1.0
            result = self.calculate_coord(percentage_walked, *steps_dict[walked_end_step])
            self._last_pos = tuple(result[0])
            return self._last_pos
        else:
            # otherwise return the destination https://github.com/th3w4y/PokemonGo-Bot/issues/27
            self._last_pos = tuple(self.points[-1])
            return self._last_pos

    def get_last_pos(self):
        return self._last_pos

    def calculate_coord(self, percentage, o, d):
        # If this is the destination then returning as such when percentage complete = 1.0
        # Here there was a bug causing this to teleport when API quota was reached!!!
        if self.points[-1] == d and percentage == 1.0 :
            return [d]
        else:
            # intermediary points returned with 5 decimals precision only
            # this ensures ~3-50cm ofset from the geometrical point calculated
            lat = o[0]+ (d[0] -o[0]) * percentage
            lon = o[1]+ (d[1] -o[1]) * percentage
            return [(round(lat, 5), round(lon, 5))]

    def get_total_distance(self, points):
        return ceil(sum([haversine.haversine(*x)*1000 for x in self.walk_steps(points)]))

# -*- coding: utf-8 -*-
from geopy.distance import VincentyDistance
from geopy import Point
from itertools import chain

import haversine
import math
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
    def cached_polyline(origin, destination, speed, google_map_api_key=None):
        '''
        Google API has limits, so we can't generate new Polyline at every tick...
        '''

        # Absolute offset between bot origin and PolyLine get_last_pos() (in meters)
        if PolylineObjectHandler._cache and PolylineObjectHandler._cache.get_last_pos() != (None, None):
            abs_offset = haversine.haversine(tuple(origin), PolylineObjectHandler._cache.get_last_pos())*1000
        else:
            abs_offset = float("inf")
        is_old_cache = lambda : abs_offset > 8 # Consider cache old if we identified an offset more then 8 m
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

            PolylineObjectHandler._cache = Polyline(origin, destination, speed, google_map_api_key)
        else:
            # valid cache found
            PolylineObjectHandler._instability -= 1
            PolylineObjectHandler._instability = max(PolylineObjectHandler._instability, 0)
            pass # use current cache
        return PolylineObjectHandler._cache


class Polyline(object):
    def __init__(self, origin, destination, speed, google_map_api_key=None):
        self.speed = float(speed)
        self.origin = origin
        self.destination = tuple(destination)
        self.DIRECTIONS_API_URL='https://maps.googleapis.com/maps/api/directions/json?mode=walking'
        self.DIRECTIONS_URL = '{}&origin={}&destination={}'.format(self.DIRECTIONS_API_URL,
                '{},{}'.format(*self.origin),
                '{},{}'.format(*self.destination))
        if google_map_api_key:
            self.DIRECTIONS_URL = '{}&key={}'.format(self.DIRECTIONS_URL, google_map_api_key)
        self._directions_response = requests.get(self.DIRECTIONS_URL).json()
        try:
            self._directions_encoded_points = [x['polyline']['points'] for x in
                                               self._directions_response['routes'][0]['legs'][0]['steps']]
        except IndexError:
            # This handles both cases:
            # a) In case of API limit reached we get back we get a status 200 code with an empty routes []
            # {u'error_message': u'You have exceeded your rate-limit for this API.',
            #  u'routes': [],
            #  u'status': u'OVER_QUERY_LIMIT'
            # }
            # b) In case that google does not have any directions proposals we get:
            # ZERO_RESULTS {
            #    "geocoded_waypoints" : [ {}, {} ],
            #    "routes" : [],
            #    "status" : "ZERO_RESULTS"
            # }
            self._directions_encoded_points = self._directions_response['routes']
        self._points = [self.origin] + self._get_directions_points() + [self.destination]
        self._polyline = self._get_encoded_points()
        self._last_pos = self._points[0]
        self._step_dict =  self._get_steps_dict()
        self._step_keys = sorted(self._step_dict.keys())
        self._last_step = 0

        self._nr_samples = int(min(self.get_total_distance() / self.speed + 1, 512))
        self.ELEVATION_API_URL='https://maps.googleapis.com/maps/api/elevation/json?path=enc:'
        self.ELEVATION_URL = '{}{}&samples={}'.format(self.ELEVATION_API_URL,
                                                      self._polyline, self._nr_samples)
        if google_map_api_key:
            self.ELEVATION_URL = '{}&key={}'.format(self.ELEVATION_URL, google_map_api_key)
        self._elevation_response = requests.get(self.ELEVATION_URL).json()
        self._elevation_at_point = dict((tuple(x['location'].values()),
                                         x['elevation']) for x in
                                        self._elevation_response['results'])

    def _get_directions_points(self):
        points = []
        for point in self._directions_encoded_points:
            points += polyline.decode(point)
        return [x for n,x in enumerate(points) if x not in points[:n]]

    def _get_encoded_points(self):
        return polyline.encode(self._points)

    def _get_walk_steps(self):
        if self._points:
            steps = zip(chain([self._points[0]], self._points),
                        chain(self._points, [self._points[-1]]))
            steps = filter(None, [(o, d) if o != d else None for o, d in steps])
            # consume the filter as list
            return list(steps)
        else:
            return []

    def _get_steps_dict(self):
        walked_distance = 0.0
        steps_dict = {}
        for step in self._get_walk_steps():
            walked_distance += haversine.haversine(*step) * 1000
            steps_dict[walked_distance] = step
        return steps_dict

    def get_alt(self):
        closest_sample = None
        best_distance = float("inf")
        for point in self._elevation_at_point.keys():
            local_distance = haversine.haversine(self._last_pos, point)*1000
            if local_distance < best_distance:
                closest_sample = point
                best_distance = local_distance
        if closest_sample in self._elevation_at_point:
            return self._elevation_at_point[closest_sample]
        else:
            return None

    def get_pos(self):
        if self.speed > self.get_total_distance():
            self._last_pos = self.destination
            self._last_step = len(self._step_keys)-1
        if self.get_last_pos() == self.destination:
            return self.get_last_pos()
        distance = self.speed
        origin = Point(*self._last_pos)
        ((so_lat, so_lng), (sd_lat, sd_lng)) = self._step_dict[self._step_keys[self._last_step]]
        bearing = self._calc_bearing(so_lat, so_lng, sd_lat, sd_lng)
        while haversine.haversine(self._last_pos, (sd_lat, sd_lng))*1000 < distance:
            distance -= haversine.haversine(self._last_pos, (sd_lat, sd_lng))*1000
            self._last_pos = (sd_lat, sd_lng)
            if self._last_step < len(self._step_keys)-1:
                self._last_step += 1
                ((so_lat, so_lng), (sd_lat, sd_lng)) = self._step_dict[self._step_keys[self._last_step]]
                bearing = self._calc_bearing(so_lat, so_lng, sd_lat, sd_lng)
                origin = Point(so_lat, so_lng)
                lat, lng = self._calc_next_pos(origin, distance, bearing)
                if haversine.haversine(self._last_pos, (lat, lng))*1000 < distance:
                    distance -= haversine.haversine(self._last_pos, (lat, lng))*1000
                    self._last_pos = (lat, lng)
            else:
                return self.get_last_pos()
        else:
            lat, lng = self._calc_next_pos(origin, distance, bearing)
            self._last_pos = (lat, lng)
            return self.get_last_pos()


    def get_total_distance(self):
        return math.ceil(sum([haversine.haversine(*x) * 1000 for x in self._get_walk_steps()]))


    def get_last_pos(self):
        return self._last_pos

    def set_speed(self, speed):
        self.speed = speed

    def _calc_next_pos(self, origin, distance, bearing):
        lat, lng, _ = origin
        if distance == 0.0:
            return lat, lng
        if distance == float("inf"):
            return self.destination
        lat, lng, _ = VincentyDistance(kilometers=distance * 1e-3).destination(origin, bearing)
        return (lat, lng)

    def _calc_bearing(self, start_lat, start_lng, dest_lat, dest_lng):
        """
        Calculates the bearing between two points.

        The formulae used is the following:
            θ = atan2(sin(Δlong).cos(lat2),
                      cos(lat1).sin(lat2) − sin(lat1).cos(lat2).cos(Δlong))

        :Parameters:
          - `start_lat in decimal degrees
          - `start_lng in decimal degrees
          - `dest_lat in decimal degrees
          - `dest_lng in decimal degrees

        :Returns:
          The bearing in degrees

        :Returns Type:
          float
        """

        lat1 = math.radians(start_lat)
        lat2 = math.radians(dest_lat)

        diffLong = math.radians(dest_lng - start_lng)

        x = math.sin(diffLong) * math.cos(lat2)
        y = math.cos(lat1) * math.sin(lat2) - (math.sin(lat1)
                                               * math.cos(lat2) * math.cos(diffLong))

        initial_bearing = math.atan2(x, y)

        # Now we have the initial bearing but math.atan2 return values
        # from -180° to + 180° which is not what we want for a compass bearing
        # The solution is to normalize the initial bearing as shown below
        initial_bearing = math.degrees(initial_bearing)
        compass_bearing = (initial_bearing + 360) % 360

        return compass_bearing

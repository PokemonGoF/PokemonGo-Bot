# -*- coding: utf-8 -*-
from geographiclib.geodesic import Geodesic
from itertools import chain

import math
import polyline
import requests
from geopy.distance import great_circle


def distance(point1, point2):
    return Geodesic.WGS84.Inverse(point1[0], point1[1], point2[0], point2[1])["s12"]  # @UndefinedVariable


class PolylineObjectHandler:
    '''
    Does this need to be a class?
    More like a namespace...
    '''
    _cache = None
    _instability = 0
    _run = False

    @staticmethod
    def cached_polyline(origin, destination, google_map_api_key=None):
        '''
        Google API has limits, so we can't generate new Polyline at every tick...
        '''

        # Absolute offset between bot origin and PolyLine get_last_pos() (in meters)
        if PolylineObjectHandler._cache and PolylineObjectHandler._cache.get_last_pos() != (None, None):
            abs_offset = distance(origin, PolylineObjectHandler._cache.get_last_pos())
        else:
            abs_offset = float("inf")
        is_old_cache = lambda : abs_offset > 8  # Consider cache old if we identified an offset more then 8 m
        new_dest_set = lambda : tuple(destination) != PolylineObjectHandler._cache.destination

        if PolylineObjectHandler._run and (not is_old_cache()):
            # bot used to have struggle with making a decision.
            PolylineObjectHandler._instability -= 1
            if PolylineObjectHandler._instability <= 0:
                PolylineObjectHandler._instability = 0
                PolylineObjectHandler._run = False
            pass  # use current cache
        elif None == PolylineObjectHandler._cache or is_old_cache() or new_dest_set():
            # no cache, old cache or new destination set by bot, so make new polyline
            PolylineObjectHandler._instability += 2
            if 10 <= PolylineObjectHandler._instability:
                PolylineObjectHandler._run = True
                PolylineObjectHandler._instability = 20  # next N moves use same cache

            PolylineObjectHandler._cache = Polyline(origin, destination, google_map_api_key)
        else:
            # valid cache found
            PolylineObjectHandler._instability -= 1
            PolylineObjectHandler._instability = max(PolylineObjectHandler._instability, 0)
            pass  # use current cache
        return PolylineObjectHandler._cache


class Polyline(object):
    def __init__(self, origin, destination, google_map_api_key=None):
        self.origin = origin
        self.destination = tuple(destination)
        self.DIRECTIONS_API_URL = 'https://maps.googleapis.com/maps/api/directions/json?mode=walking'
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
        self._step_dict = self._get_steps_dict()
        self._step_keys = sorted(self._step_dict.keys())
        self._last_step = 0

        self._nr_samples = int(max(min(self.get_total_distance() / 3, 512), 2))
        self.ELEVATION_API_URL = 'https://maps.googleapis.com/maps/api/elevation/json?path=enc:'
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
        return [x for n, x in enumerate(points) if x not in points[:n]]

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
            walked_distance += distance(*step)
            steps_dict[walked_distance] = step
        return steps_dict

    def get_alt(self, at_point=None):
        if at_point is None:
            at_point = self._last_pos
        if self._elevation_at_point:
            elevations = sorted([(great_circle(at_point, k).meters, v, k) for k, v in self._elevation_at_point.items()])

            if len(elevations) == 1:
                return elevations[0][1]
            else:
                (distance_to_p1, ep1, p1), (distance_to_p2, ep2, p2) = elevations[:2]
                distance_p1_p2 = great_circle(p1, p2).meters
                return self._get_relative_hight(ep1, ep2, distance_p1_p2, distance_to_p1, distance_to_p2)
        else:
            return None


    def _get_relative_hight(self, ep1, ep2, distance_p1_p2, distance_to_p1, distance_to_p2):
        hdelta = ep2 - ep1
        elevation = ((math.pow(distance_p1_p2,2) + math.pow(distance_to_p1,2) - math.pow(distance_to_p2,2)) * hdelta)/ (3 * distance_p1_p2) + ep1
        return elevation

    def get_total_distance(self):
        return math.ceil(sum([distance(*x) for x in self._get_walk_steps()]))

    def get_last_pos(self):
        return self._last_pos

import time
from itertools import chain
from math import ceil
import haversine
import polyline
import requests


class Polyline(object):

    def __init__(self, origin, destination, speed):
        self.DISTANCE_API_URL='https://maps.googleapis.com/maps/api/directions/json?mode=walking'
        self.origin = origin
        self.destination = destination
        self.URL = '{}&origin={}&destination={}'.format(self.DISTANCE_API_URL,
                                                   '{},{}'.format(*self.origin),
                                                   '{},{}'.format(*self.destination))
        self.request_responce = requests.get(self.URL).json()
        try:
            self.polyline_points = [x['polyline']['points'] for x in
                                    self.request_responce['routes'][0]['legs'][0]['steps']]
        except IndexError:
            self.polyline_points = self.request_responce['routes']
        self.speed = float(speed)
        self.points = [self.origin] + self.get_points(self.polyline_points) + [self.destination]
        self.lat, self.long = self.points[0][0], self.points[0][1]
        self.polyline = self.combine_polylines(self.points)
        self._timestamp = time.time()
        self.is_paused = False
        self._last_paused_timestamp = None
        self._paused_total = 0.0

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

    def walk_steps(self):
        if self.points:
            walk_steps = zip(chain([self.points[0]], self.points),
                             chain(self.points, [self.points[-1]]))
            walk_steps = filter(None, [(o, d) if o != d else None for o, d in walk_steps])
            return walk_steps
        else:
            return []

    def get_pos(self):
        walked_distance = 0.0
        if not self.is_paused:
            time_passed = time.time()
        else:
            time_passed = self._last_paused_timestamp
        time_passed_distance = self.speed * abs(time_passed - self._timestamp - self._paused_total)
        steps_dict = {}
        for step in self.walk_steps():
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
        return self.calculate_coord(percentage_walked, *steps_dict[walked_end_step])

    def calculate_coord(self, percentage, o, d):
        # If this is the destination then returning as such
        if self.points[-1] == d:
            return [d]
        else:
            # intermediary points returned with 5 decimals precision only
            # this ensures ~3-50cm ofset from the geometrical point calculated
            lat = o[0]+ (d[0] -o[0]) * percentage
            lon = o[1]+ (d[1] -o[1]) * percentage
            return [(round(lat, 5), round(lon, 5))]

    def get_total_distance(self):
        return ceil(sum([haversine.haversine(*x)*1000 for x in self.walk_steps()]))



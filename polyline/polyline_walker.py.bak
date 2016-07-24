import polyline
import haversine
import time
from itertools import  chain

class PolylineWalker(object):

    def __init__(self, polyline_points, speed):
        """
        :param polyline_points:
        URL = 'https://maps.googleapis.com/maps/api/directions/json?origin=Cham,CH&destination=Baar,CH&mode=walking'
        polyline_points =[x['polyline']['points'] for x in
                          requests.get(URL).json()['routes'][0]['legs'][0]['steps']]
        :param speed:
        """
        self.speed = float(speed)
        self.points = self.get_points(polyline_points)
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
            return zip(chain([self.points[0]], self.points),
                       chain(self.points, [self.points[-1]]))
        else:
            return []

    def walk(self):
        if not self.is_paused:
            walked_distance = 0.0
            time_passed = time.time()
            remaining_points = []
            time_passed_distance = self.speed * abs(time_passed - self._timestamp - self._paused_total)
            for step in self.walk_steps():
                step_distance = haversine.haversine(*step)*1000
                if walked_distance + step_distance >= time_passed_distance:
                    if walked_distance > time_passed_distance:
                        percentage_walked = 0.0
                    else:
                        if step_distance == 0.0:
                            percentage_walked = 1.0
                        else:
                            percentage_walked = (time_passed_distance - walked_distance)/step_distance
                    remaining_points += self.calculate_coord(percentage_walked,*step)
                else:
                    percentage_walked = 1.0
                walked_distance += step_distance * percentage_walked
            self.points = remaining_points
            if self.points:
                self.lat, self.long = self.points[0][0], self.points[0][1]
                self.polyline = self.combine_polylines(self.points)
            else:
                self.lat, self.long = None, None
                self.polyline = ''
            self.reset_timestamps()
        return (self.lat, self.long)

    def calculate_coord(self, percentage, o, d):
        lat = o[0]+ (d[0] -o[0]) * percentage
        lon = o[1]+ (d[1] -o[1]) * percentage
        return [(lat, lon)]


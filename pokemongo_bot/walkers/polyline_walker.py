from __future__ import absolute_import
from geographiclib.geodesic import Geodesic
from random import uniform
from time import sleep

from pokemongo_bot.walkers.step_walker import StepWalker
from .polyline_generator import PolylineObjectHandler
from pokemongo_bot.human_behaviour import random_alt_delta


class PolylineWalker(StepWalker):
    def handle_flight(self):
        speed = uniform(self.bot.config.fly_min, self.bot.config.fly_max)
        origin_lat, origin_lng, origin_alt = self.bot.position
        remaining = Geodesic.WGS84.Inverse(origin_lat, origin_lng, self.dest_lat, self.dest_lng)["s12"]
        time_to_sleep = remaining / speed
        sleep(time_to_sleep)
        super(PolylineWalker, self).step(float("inf"))

    def step(self, speed=None):
        if speed is None:
            if self.mode == "walking":
                speed = uniform(self.bot.config.walk_min, self.bot.config.walk_max)
            if self.mode == "flying":
                self.handle_flight()
                return True
            else:
                try:
                    cache = PolylineObjectHandler._cache
                    _,_,speed = cache._step_dict[cache._step_keys[cache._last_step]]
                    speed = speed * uniform(0.95, 1.05)
                except Exception as e:
                    pass

        return super(PolylineWalker, self).step(speed)

    def get_next_position(self, origin_lat, origin_lng, origin_alt, dest_lat, dest_lng, dest_alt, distance):
        polyline = PolylineObjectHandler.cached_polyline((self.bot.position[0], self.bot.position[1]), (dest_lat, dest_lng), google_map_api_key=self.bot.config.gmapkey, mode=self.mode)

        while True:
            _, (dest_lat, dest_lng), _ = polyline._step_dict[polyline._step_keys[polyline._last_step]]

            next_lat, next_lng, _ = super(PolylineWalker, self).get_next_position(origin_lat, origin_lng, origin_alt, dest_lat, dest_lng, dest_alt, distance)

            if polyline._last_step == len(polyline._step_keys) - 1:
                break
            else:
                travelled = Geodesic.WGS84.Inverse(origin_lat, origin_lng, next_lat, next_lng)["s12"]
                remaining = Geodesic.WGS84.Inverse(next_lat, next_lng, dest_lat, dest_lng)["s12"]
                step_distance = Geodesic.WGS84.Inverse(origin_lat, origin_lng, dest_lat, dest_lng)["s12"]

                if remaining < (self.precision + self.epsilon):
                    polyline._last_step += 1
                    distance = abs(distance - step_distance)
                else:
                    distance = abs(distance - travelled)

                if distance > (self.precision + self.epsilon):
                    origin_lat, origin_lng, origin_alt = dest_lat, dest_lng, dest_alt
                else:
                    break

        polyline._last_pos = (next_lat, next_lng)
        next_alt = polyline.get_alt() or origin_alt

        return next_lat, next_lng, next_alt + random_alt_delta()

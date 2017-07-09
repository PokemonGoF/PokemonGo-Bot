# -*- coding: utf-8 -*-
import time

from geographiclib.geodesic import Geodesic
from random import uniform

from pokemongo_bot.human_behaviour import sleep, random_alt_delta


class StepWalker(object):
    def __init__(self, bot, dest_lat, dest_lng, dest_alt=None, precision=0.5):
        self.bot = bot
        self.api = bot.api
        self.epsilon = 0.01
        self.precision = max(precision, self.epsilon)

        self.dest_lat = dest_lat
        self.dest_lng = dest_lng

        if dest_alt is None:
            self.dest_alt = uniform(self.bot.config.alt_min, self.bot.config.alt_max)
        else:
            self.dest_alt = dest_alt

        self.saved_location = None
        self.last_update = time.time()

    def step(self, speed=None):
        now = time.time()
        t = 1 - min(now - self.last_update, 1)

        sleep(t)
        self.last_update = now + t

        if speed is None:
            speed = uniform(self.bot.config.walk_min, self.bot.config.walk_max)
        elif speed == self.bot.config.walk_max:
            # Keep it more Human like...
            speed = uniform(speed - 0.5, speed + 0.5)

        origin_lat, origin_lng, origin_alt = self.bot.position

        new_position = self.get_next_position(origin_lat, origin_lng, origin_alt, self.dest_lat, self.dest_lng, self.dest_alt, speed)

        self.api.set_position(new_position[0], new_position[1], new_position[2])
        self.bot.event_manager.emit("position_update",
                                    sender=self,
                                    level="debug",
                                    data={"current_position": (new_position[0], new_position[1], new_position[2]),
                                          "last_position": (origin_lat, origin_lng, origin_alt),
                                          "distance": "",
                                          "distance_unit": ""})

        return self.is_arrived()

    def is_arrived(self):
        inverse = Geodesic.WGS84.Inverse(self.bot.position[0], self.bot.position[1], self.dest_lat, self.dest_lng)
        return inverse["s12"] <= self.precision + self.epsilon

    def get_next_position(self, origin_lat, origin_lng, origin_alt, dest_lat, dest_lng, dest_alt, distance):
        line = Geodesic.WGS84.InverseLine(origin_lat, origin_lng, dest_lat, dest_lng)
        total_distance = line.s13

        if total_distance == 0:
            total_distance = self.precision or self.epsilon

        if distance == 0:
            if not self.saved_location:
                self.saved_location = origin_lat, origin_lng, origin_alt

            dest_lat, dest_lng, dest_alt = self.saved_location
            travel = self.precision
        else:
            self.saved_location = None
            travel = min(total_distance, distance)

        position = line.Position(travel)
        next_lat = position["lat2"]
        next_lng = position["lon2"]

        random_azi = uniform(line.azi1 - 90, line.azi1 + 90)
        random_dist = uniform(0.0, self.precision)
        direct = Geodesic.WGS84.Direct(next_lat, next_lng, random_azi, random_dist)

        next_lat = direct["lat2"]
        next_lng = direct["lon2"]
        next_alt = origin_alt + (travel / total_distance) * (dest_alt - origin_alt) + random_alt_delta()

        return next_lat, next_lng, next_alt

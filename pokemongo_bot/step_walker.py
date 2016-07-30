from time import time
from math import sqrt

from cell_workers.utils import distance
from human_behaviour import random_lat_long_delta, sleep

class StepWalker(object):

    def __init__(self, bot, speed, dest_lat, dest_lng):
        self.bot = bot
        self.api = bot.api

        self.initLat, self.initLng = self.bot.position[0:2]

        self.dist = distance(
            self.initLat,
            self.initLng,
            dest_lat,
            dest_lng
        )

        self.speed = speed

        self.destLat = dest_lat
        self.destLng = dest_lng
        self.totalDist = max(1, self.dist)
        self.lastTime = None
        self.steps = (self.dist + 0.0) / (speed + 0.0)

        if self.dist < speed or int(self.steps) <= 1:
            self.dLat = 0
            self.dLng = 0
        else:
            self.dLat = (dest_lat - self.initLat) / int(self.steps)
            self.dLng = (dest_lng - self.initLng) / int(self.steps)

    def stop(self):
        self.lastTime = None

    def step(self):
        # Since speed is m/s, we need to scale up our distance to move by
        # the number of seconds elapsed since we last moved
        time_scale = 1
        current_time = time()
        if self.lastTime is not None:
            time_scale = current_time - self.lastTime
            self.lastTime = current_time

        if (self.dLat == 0 and self.dLng == 0) or self.dist < self.speed:
            self.api.set_position(self.destLat, self.destLng, 0)
            self.lastTime = None
            return True

        cLat = self.initLat + (self.dLat * time_scale) + random_lat_long_delta()
        cLng = self.initLng + (self.dLng * time_scale) + random_lat_long_delta()

        self.api.set_position(cLat, cLng, 0)
        self.lastTime = current_time
        self.bot.heartbeat()

        sleep(1)  # sleep one second plus a random delta
        # self._work_at_position(
        #     self.initLat, self.initLng,
        #     alt, False)

    def _pythagorean(self, lat, lng):
        return sqrt((lat ** 2) + (lng ** 2))

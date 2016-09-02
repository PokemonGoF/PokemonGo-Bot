from math import sqrt

from random import uniform
from pokemongo_bot.cell_workers.utils import distance
from pokemongo_bot.human_behaviour import random_lat_long_delta, sleep, random_alt_delta

class StepWalker(object):

    def __init__(self, bot, dest_lat, dest_lng, dest_alt = None):
        self.bot = bot
        self.api = bot.api

        self.initLat, self.initLng = self.bot.position[0:2]

        self.dist = distance(
            self.initLat,
            self.initLng,
            dest_lat,
            dest_lng
        )
        if dest_alt == None:
            self.alt = uniform(self.bot.config.alt_min, self.bot.config.alt_max)
        else:
            self.alt = dest_alt
        self.speed = uniform(self.bot.config.walk_min, self.bot.config.walk_max)

        if len(self.bot.position) == 3:
            self.initAlt = self.bot.position[2]
        else:
            self.initAlt = self.alt;

        self.destLat = dest_lat
        self.destLng = dest_lng
        self.totalDist = max(1, self.dist)

        if self.speed == 0:
            raise Exception("Walking speed cannot be 0, change your walking speed higher than 1!")
        else:
            self.steps = (self.dist + 0.0) / (self.speed + 0.0)

        if self.dist < self.speed or int(self.steps) <= 1:
            self.dLat = 0
            self.dLng = 0
            self.magnitude = 0
        else:
            self.dLat = (dest_lat - self.initLat) / int(self.steps)
            self.dLng = (dest_lng - self.initLng) / int(self.steps)
            self.magnitude = self._pythagorean(self.dLat, self.dLng)
            self.unitAlt = (self.alt - self.initAlt) / int(self.steps)

    def step(self):
        if (self.dLat == 0 and self.dLng == 0) or self.dist < self.speed:
            self.api.set_position(self.destLat + random_lat_long_delta(), self.destLng + random_lat_long_delta(), self.alt)
            self.bot.event_manager.emit(
                'position_update',
                sender=self,
                level='debug',
                data={
                    'current_position': (self.destLat, self.destLng),
                    'last_position': (self.initLat, self.initLng),
                    'distance': '',
                    'distance_unit': ''
                }
            )
            self.bot.heartbeat()
            return True

        totalDLat = (self.destLat - self.initLat)
        totalDLng = (self.destLng - self.initLng)
        magnitude = self._pythagorean(totalDLat, totalDLng)
        unitLat = totalDLat / magnitude
        unitLng = totalDLng / magnitude

        scaledDLat = unitLat * self.magnitude
        scaledDLng = unitLng * self.magnitude

        cLat = self.initLat + scaledDLat + random_lat_long_delta()
        cLng = self.initLng + scaledDLng + random_lat_long_delta()
        cAlt = self.initAlt + self.unitAlt + random_alt_delta()

        self.api.set_position(cLat, cLng, cAlt)
        self.bot.event_manager.emit(
            'position_update',
            sender=self,
            level='debug',
            data={
                'current_position': (cLat, cLng, cAlt),
                'last_position': (self.initLat, self.initLng, self.initAlt),
                'distance': '',
                'distance_unit': ''
            }
        )
        self.bot.heartbeat()

        sleep(1)  # sleep one second plus a random delta
        # self._work_at_position(
        #     self.initLat, self.initLng,
        #     alt, False)

    def _pythagorean(self, lat, lng):
        return sqrt((lat ** 2) + (lng ** 2))

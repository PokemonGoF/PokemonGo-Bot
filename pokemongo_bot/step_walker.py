import logger

from cell_workers.utils import distance, i2f, format_time
from human_behaviour import random_lat_long_delta, sleep
from math import ceil


class StepWalker(object):

    def __init__(self, bot):
        self.bot = bot
        self.api = bot.api

    def step(self, speed, lat, lng):
        if self.api._position_lat == lat and self.api._position_lng == lng:
            return True

        dLat = (lat - i2f(self.api._position_lat))
        dLng = (lng - i2f(self.api._position_lng))

        cLat = i2f(self.api._position_lat) + dLat + random_lat_long_delta()
        cLng = i2f(self.api._position_lng) + dLng + random_lat_long_delta()

        self.api.set_position(cLat, cLng, 0)
        self.bot.heartbeat()
        sleep(1)  # sleep one second plus a random delta
        # self._work_at_position(
        #     i2f(self.api._position_lat), i2f(self.api._position_lng),
        #     alt, False)

from math import sqrt

from cell_workers.utils import distance
from human_behaviour import random_lat_long_delta, sleep
import sys


def progress_bar(percentage):
    percentage = min(100, max(0, percentage))
    if not sys.stdout.isatty():
        return
    sys.stdout.write('\r')
    # http://www.fileformat.info/info/unicode/char/003D/index.htm
    msg = (u"[%-40s] %d%%" % (u"\u003D"*int(percentage*2//5), percentage))
    sys.stdout.write(msg)
    sys.stdout.flush()


class StepWalker(object):

    def __init__(self, bot, speed, initLat, initLng, destLat, destLng):
        self.bot = bot
        self.api = bot.api

        dist = distance(
            initLat,
            initLng,
            destLat,
            destLng
        )

        self.speed = speed

        self.destLat = destLat
        self.destLng = destLng
        self.totalDist = max(1, dist)

        self.steps = (dist + 0.0) / (speed + 0.0)

        if dist < speed or self.steps < 1:
            self.dLat = 0
            self.dLng = 0
            self.magnitude = 0;
        else:
            self.dLat = (destLat - initLat) / self.steps
            self.dLng = (destLng - initLng) / self.steps
            self.magnitude = self._pythagorean(self.dLat, self.dLng)

    def step(self):
        dist = distance(
            self.api._position_lat,
            self.api._position_lng,
            self.destLat,
            self.destLng
        )

        progress_bar(int(100 * (1 - dist/self.totalDist)))

        if (self.dLat == 0 and self.dLng == 0) or dist < self.speed:
            if sys.stdout.isatty():
                sys.stdout.write('\n')
            self.api.set_position(self.destLat, self.destLng, 0)
            return True

        totalDLat = (self.destLat - self.api._position_lat)
        totalDLng = (self.destLng - self.api._position_lng)
        magnitude = self._pythagorean(totalDLat, totalDLng)
        unitLat = totalDLat / magnitude
        unitLng = totalDLng / magnitude

        scaledDLat = unitLat * self.magnitude
        scaledDLng = unitLng * self.magnitude

        cLat = self.api._position_lat + scaledDLat + random_lat_long_delta()
        cLng = self.api._position_lng + scaledDLng + random_lat_long_delta()

        self.api.set_position(cLat, cLng, 0)
        self.bot.heartbeat()
        sleep(1)  # sleep one second plus a random delta
        # self._work_at_position(
        #     self.api._position_lat, self.api._position_lng,
        #     alt, False)

    def _pythagorean(self, lat, lng):
        return sqrt((lat ** 2) + (lng ** 2))

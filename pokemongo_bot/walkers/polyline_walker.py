# -*- coding: utf-8 -*-
from polyline_generator import Polyline
from math import ceil
from human_behaviour import sleep
from cell_workers.utils import i2f
import logger
from pokemongo_bot.step_walker import StepWalker

class PolylineWalker(StepWalker):

    def __init__(self, bot, speed, initLat, initLng, destLat, destLng):
        super(PolylineWalker, self).__init__(bot, speed, initLat, initLng, destLat, destLng)
        self.polyline_walker = Polyline(i2f(self.api._position_lat), i2f(self.api._position_lng), self.speed)

    def step(self):
        self.polyline_walker.unpause()
        sleep(1)
        self.polyline_walker.pause()
        cLat, cLng = self.polyline_walker.get_pos()[0]
        self.api.set_position(cLat, cLng, 0)
        self.bot.heartbeat()
        if self.destLat == cLat and self.destLng == cLng:
            return True

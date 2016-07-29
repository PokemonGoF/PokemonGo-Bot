# -*- coding: utf-8 -*-
from polyline_generator import Polyline
from pokemongo_bot.human_behaviour import sleep
from pokemongo_bot.step_walker import StepWalker
from pokemongo_bot import logger

class PolylineWalker(StepWalker):

    def __init__(self, bot, speed, destLat, destLng):
        super(PolylineWalker, self).__init__(bot, speed, destLat, destLng)
        self.polyline_walker = Polyline((self.api._position_lat, self.api._position_lng),
                                        (self.destLat, self.destLng), self.speed)
        logger.log('[#] {}'.format(self.polyline_walker.URL))

    def step(self):
        self.polyline_walker.unpause()
        sleep(1)
        self.polyline_walker.pause()
        cLat, cLng = self.polyline_walker.get_pos()[0]
        self.api.set_position(round(cLat, 5), round(cLng, 5), 0)
        self.bot.heartbeat()
        if self.destLat == cLat and self.destLng == cLng:
            return True

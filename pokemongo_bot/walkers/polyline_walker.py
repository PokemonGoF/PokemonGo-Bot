# -*- coding: utf-8 -*-

from pokemongo_bot.human_behaviour import sleep
from pokemongo_bot.walkers.step_walker import StepWalker
from polyline_generator import PolylineObjectHandler
from pokemongo_bot.cell_workers.utils import distance
from pokemongo_bot.constants import Constants

class PolylineWalker(StepWalker):
    '''
    Heavy multi-botting can cause issue, since the directions API has limits.
    '''

    def __init__(self, bot, speed, dest_lat, dest_lng, parent):
        super(PolylineWalker, self).__init__(bot, speed, dest_lat, dest_lng)
        self.polyline_walker = PolylineObjectHandler.cached_polyline(bot, (self.api._position_lat, self.api._position_lng),
                                        (self.destLat, self.destLng), self.speed, parent)
        self.dist = distance(
            self.bot.position[0],
            self.bot.position[1],
            dest_lat,
            dest_lng
        )

    def step(self):
        cLat, cLng = self.api._position_lat, self.api._position_lng

        if self.dist < 10: # 10m, add config? set it at constants?
            PolylineObjectHandler.delete_cache(self.polyline_walker)
            return True

        self.polyline_walker.unpause()
        sleep(1)
        self.polyline_walker.pause()
        cLat, cLng = self.polyline_walker.get_pos()[0]
        _, _, alt = self.api.get_position()
        self.api.set_position(cLat, cLng, alt)
        self.bot.heartbeat()
        return False


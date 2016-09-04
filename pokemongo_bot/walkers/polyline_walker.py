# -*- coding: utf-8 -*-
from random import uniform

import haversine

from pokemongo_bot.walkers.step_walker import StepWalker
from polyline_generator import PolylineObjectHandler


class PolylineWalker(StepWalker):

    def __init__(self, bot, dest_lat, dest_lng):
        self.bot = bot
        self.speed = uniform(self.bot.config.walk_min, self.bot.config.walk_max)
        self.dest_lat, self.dest_lng = dest_lat, dest_lng
        self.actual_pos = tuple(self.bot.position[:2])
        self.actual_alt = self.bot.position[-1]
        self.polyline = PolylineObjectHandler.cached_polyline(self.actual_pos,
                                                              (self.dest_lat, self.dest_lng),
                                                              self.speed, google_map_api_key=self.bot.config.gmapkey)
        self.polyline.set_speedself.speed()
        self.pol_lat, self.pol_lon = self.polyline.get_pos()
        self.pol_alt = self.polyline.get_alt() or self.actual_alt
        super(PolylineWalker, self).__init__(self.bot, self.pol_lat, self.pol_lon, self.pol_alt,
                                             fixed_speed=self.speed)
        if haversine.haversine(self.polyline.destination, (self.pol_lat, self.pol_lon))*1000 > 2*self.speed:
            bearing = self._calc_bearing(self.actual_pos[0], self.actual_pos[1], self.pol_lat, self.pol_lon)
            distance = self.speed*2
            next_lat, next_lon = self._get_next_pos(self.actual_pos[0], self.actual_pos[1], bearing, distance, precision=0.0)
            super(PolylineWalker, self).__init__(self.bot, next_lat, next_lon, self.pol_alt,
                                                 fixed_speed=self.speed)

# -*- coding: utf-8 -*-

import haversine
from pokemongo_bot.human_behaviour import sleep
from polyline_generator import Polyline



class PolylineWalker(object):
    instances = {}

    def __new__(cls, bot, speed, dest_lat, dest_lng):
        try:
            self = PolylineWalker.instances[(bot, speed, dest_lat, dest_lng)]
            pol_position = self.polyline_walker.get_pos()[0]
            bot_position = (self.api._position_lat, self.api._position_lng)
            bot_pol_dist = haversine.haversine(bot_position, pol_position)*1000
            if bot_position == pol_position or bot_pol_dist >= 50:
                self = PolylineWalker.instances[(bot, speed, dest_lat, dest_lng)] = \
                    super(PolylineWalker, cls).__new__(cls)
                self.bot = bot
                self.api = bot.api
                self.dest_lat = dest_lat
                self.dest_lng = dest_lng
                self.speed = speed
                self.polyline_walker = Polyline((self.api._position_lat, self.api._position_lng),
                                                (self.dest_lat, self.dest_lng), self.speed)
                self.bot.event_manager.emit(
                    'polyline_request',
                    sender=self,
                    level='info',
                    formatted="{url}",
                    data={'url': self.polyline_walker.URL}
                )
        except KeyError:
            self = PolylineWalker.instances[(bot, speed, dest_lat, dest_lng)] = \
                super(PolylineWalker, cls).__new__(cls)
            self.bot = bot
            self.api = bot.api
            self.dest_lat = dest_lat
            self.dest_lng = dest_lng
            self.speed = speed
            self.polyline_walker = Polyline((self.api._position_lat, self.api._position_lng),
                                            (self.dest_lat, self.dest_lng), self.speed)
            self.bot.event_manager.emit(
                'polyline_request',
                sender=self,
                level='info',
                formatted="{url}",
                data={'url': self.polyline_walker.URL}
            )
        return self

    def step(self):
        cLat, cLng = self.polyline_walker.get_pos()[0]
        if self.dest_lat == cLat and self.dest_lng == cLng:
            return True
        self.api.set_position(cLat, cLng, 0)
        self.bot.heartbeat()
        sleep(1)

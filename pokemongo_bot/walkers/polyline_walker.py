from random import uniform

from pokemongo_bot.walkers.step_walker import StepWalker
from polyline_generator import PolylineObjectHandler


class PolylineWalker(StepWalker):

    def __init__(self, bot, dest_lat, dest_lng):
        self.bot = bot
        self.speed = self.bot.config.walk_min
        self.dest_lat, self.dest_lng = dest_lat, dest_lng
        self.actual_pos = tuple(self.bot.position[:2])
        self.polyline = PolylineObjectHandler.cached_polyline(self.actual_pos,
                                                              (self.dest_lat, self.dest_lng),
                                                              self.speed)
        self.pol_lat, self.pol_lon = self.polyline.get_pos()
        self.pol_alt = self.polyline.get_alt() or uniform(self.bot.config.alt_min, self.bot.config.alt_max)
        super(PolylineWalker, self).__init__(self.bot, self.pol_lat, self.pol_lon,
                                             self.pol_alt, fixed_speed=True)

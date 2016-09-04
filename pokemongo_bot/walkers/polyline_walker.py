from random import uniform

from pokemongo_bot.cell_workers.utils import distance
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
        self.pol_lat, self.pol_lon = self.polyline.get_pos()
        self.pol_alt = self.polyline.get_alt() or self.actual_alt
        super(PolylineWalker, self).__init__(self.bot, self.pol_lat, self.pol_lon,
                                             self.pol_alt, fixed_speed=self.speed)

    def step(self):
        step = super(PolylineWalker, self).step()
        if not (distance(self.pol_lat, self.pol_lon, self.dest_lat, self.dest_lng) > 10 and step):
            return False
        else:
            return True

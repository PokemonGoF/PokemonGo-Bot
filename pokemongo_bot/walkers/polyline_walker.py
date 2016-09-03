from random import uniform

from pokemongo_bot.walkers.step_walker import StepWalker
from polyline_generator import PolylineObjectHandler


class PolylineWalker(StepWalker):

    def __init__(self, bot, dest_lat, dest_lng):
        self.bot = bot
        self.speed = self.bot.config.walk_min
        self.dest_lat, self.dest_lng = dest_lat, dest_lng
        self.actual_pos = tuple(self.bot.position[:2])
        self.actual_alt = self.bot.position[-1]
        
        self.dist = distance(
            self.bot.position[0],
            self.bot.position[1],
            dest_lat,
            dest_lng
        
        # we don't need this if I call StepWalker's stepper right?
        #super(PolylineWalker, self).__init__(self.bot, self.pol_lat, self.pol_lon,
        #                                     self.pol_alt, fixed_speed=True)

    def step(self):
        self.polyline = PolylineObjectHandler.cached_polyline(self.actual_pos,
                                                              (self.dest_lat, self.dest_lng),
                                                              self.speed)
        
        if self.dist < 10: # 10m, add config? set it at constants?
            return True
        
        self.polyline_walker.unpause()
        sleep(1)
        self.polyline_walker.pause()
        
        self.pol_lat, self.pol_lon = self.polyline.get_pos()
        self.pol_alt = self.polyline.get_alt() or uniform(self.bot.config.alt_min, self.bot.config.alt_max)
        
        step_walker = StepWalker(
            self.bot,
            self.pol_lat,
            self.pol_lon.
            self.pol_alt,
            self.speed
        )

        step_walker.step():
        
        self.actual_pos (self.pol_lat, self.pol_lon) # might be a case this instance is reused in the future...
        
        self.bot.heartbeat()
        
        return False

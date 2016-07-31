from time import time
from math import sqrt
from pokemongo_bot import logger
from cell_workers.utils import distance
from human_behaviour import jitter, sleep

class StepWalker(object):

    def __init__(self, bot, speed, dest_lat, dest_lng, label='<StepWalker>'):
        self.bot = bot
        self.api = bot.api

        init_lat, init_lng = self.bot.position[0:2]

        self.dist = 0
        self.speed = speed
        self.destLat = dest_lat
        self.destLng = dest_lng
        self.lastTime = None
        self.steps = 0
        self.update_component_vectors()
        self.complete = False
        self.label = label

    def update_component_vectors(self):
        """
        Recalculate dLat and dLng based on the current position, speed, and destination
        """
        self.dist = distance(
            self.bot.position[0],
            self.bot.position[1],
            self.destLat,
            self.destLng
        )

        self.steps = (self.dist + 0.0) / (self.speed + 0.0)

        if int(self.steps) <= 1:
            self.dLat = 0
            self.dLng = 0
        else:
            self.dLat = (self.destLat - self.bot.position[0]) / int(self.steps)
            self.dLng = (self.destLng - self.bot.position[1]) / int(self.steps)

    def step(self):
        if self.complete:
            raise Exception(self.label + ' has already reached it\'s destination')

        # Since speed is m/s, we need to scale up our distance to move by
        # the number of seconds elapsed since we last moved
        time_scale = 1
        current_time = time()
        if self.lastTime is not None:
            time_scale = current_time - self.lastTime
            self.lastTime = current_time

        # Add some randomness for human-like behavior
        dist_scale = jitter(time_scale, time_scale * 0.03)

        # Check if we should end on the destination point, if it's in range
        if (self.dLat == 0 and self.dLng == 0) or self.dist < (self.speed * dist_scale):
            logger.log('{} in range of target, skipping to destination {}m away, over {} seconds'.format(self.label, self.dist, time_scale))
            self.api.set_position(self.destLat, self.destLng, 0)
            self.complete = True
            return True

        c_lat = self.bot.position[0] + (self.dLat * time_scale)
        c_lng = self.bot.position[1] + (self.dLng * time_scale)
        self.api.set_position(c_lat, c_lng, 0)


        # Recalculate components every tick to prevent long distance rounding errors from
        # screwing up the course
        self.update_component_vectors()
        self.lastTime = current_time
        self.bot.heartbeat()

        sleep(1)

    def _pythagorean(self, lat, lng):
        return sqrt((lat ** 2) + (lng ** 2))

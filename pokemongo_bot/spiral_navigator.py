# -*- coding: utf-8 -*-

import os
import json
import time
import pprint

from math import ceil
from s2sphere import CellId, LatLng
from google.protobuf.internal import encoder

from human_behaviour import sleep, random_lat_long_delta
from cell_workers.utils import distance, i2f, format_time, format_dist
from step_walker import StepWalker

from pgoapi.utilities import f2i, h2f
import logger


class SpiralNavigator(object):
    def __init__(self, bot):
        self.bot = bot
        self.api = bot.api
        self.config = bot.config

        self.pos = 1
        self.x = 0
        self.y = 0
        self.dx = 0
        self.dy = -1
        self.steplimit = self.config.max_steps
        self.steplimit2 = self.steplimit**2
        self.origin_lat = self.bot.position[0]
        self.origin_lon = self.bot.position[1]
        self._step_walker = None

    def take_step(self):
        position = (self.origin_lat, self.origin_lon, 0.0)

        logger.log('[#] Scanning area for objects....')
        # logger.log('[#] Scanning area for objects ({} / {})'.format(
        #     (step + 1), self.steplimit**2))
        if self.config.debug:
            logger.log(
                'steplimit: {} x: {} y: {} pos: {} dx: {} dy {}'.format(
                    self.steplimit2, self.x, self.y, self.pos, self.dx,
                    self.dy))
        # Scan location math

        if -self.steplimit2 / 2 < self.x <= self.steplimit2 / 2 and -self.steplimit2 / 2 < self.y <= self.steplimit2 / 2:
            position = (self.x * 0.0025 + self.origin_lat,
                        self.y * 0.0025 + self.origin_lon, 0)
            if self.config.walk > 0:
                if not self._step_walker:
                    self._step_walker = StepWalker(
                        self.bot,
                        self.config.walk,
                        self.api._position_lat,
                        self.api._position_lng,
                        position[0],
                        position[1]
                    )

                dist = distance(
                    i2f(self.api._position_lat),
                    i2f(self.api._position_lng),
                    position[0],
                    position[1]
                )

                logger.log('[#] Walking from ' + str((i2f(self.api._position_lat), i2f(
                    self.api._position_lng))) + " to " + str((str(position[0:2]))) + " " + format_dist(dist, self.config.distance_unit))

                if self._step_walker.step():
                    self._step_walker = None
            else:
                self.api.set_position(*position)
        if self.x == self.y or self.x < 0 and self.x == -self.y or self.x > 0 and self.x == 1 - self.y:
            (self.dx, self.dy) = (-self.dy, self.dx)

        if distance(
                    i2f(self.api._position_lat),
                    i2f(self.api._position_lng),
                    position[0],
                    position[1]
                ) < 1:
            (self.x, self.y) = (self.x + self.dx, self.y + self.dy)
        sleep(2)
        return position[0:2]

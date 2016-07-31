# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import pokemongo_bot.logger as logger
from pokemongo_bot.cell_workers.utils import distance, format_dist
from pokemongo_bot.step_walker import StepWalker


class FollowSpiral(object):
    def __init__(self, bot):
        self.bot = bot

        self.steplimit = self.bot.config.max_steps
        self.origin_lat = self.bot.position[0]
        self.origin_lon = self.bot.position[1]

        self.points = self._generate_spiral(
            self.origin_lat, self.origin_lon, 0.0018, self.steplimit
        )
        self.ptr = 0
        self.direction = 1
        self.step_walker = None
        self.next_point = None

    @staticmethod
    def _generate_spiral(starting_lat, starting_lng, step_size, step_limit):
        """
        Sourced from:
        https://github.com/tejado/pgoapi/blob/master/examples/spiral_poi_search.py

        :param starting_lat:
        :param starting_lng:
        :param step_size:
        :param step_limit:
        :return:
        """
        coords = [{'lat': starting_lat, 'lng': starting_lng}]
        steps, x, y, d, m = 1, 0, 0, 1, 1

        while steps < step_limit:
            while 2 * x * d < m and steps < step_limit:
                x = x + d
                steps += 1
                lat = x * step_size + starting_lat
                lng = y * step_size + starting_lng
                coords.append({'lat': lat, 'lng': lng})
            while 2 * y * d < m and steps < step_limit:
                y = y + d
                steps += 1
                lat = x * step_size + starting_lat
                lng = y * step_size + starting_lng
                coords.append({'lat': lat, 'lng': lng})

            d *= -1
            m += 1
        return coords

    def walk_to_next_point(self):
        # Turn around after getting to the end of the list
        if self.ptr == 0:
            self.direction = 1
        elif self.ptr == len(self.points) - 1:
            self.direction = -1

        self.next_point = self.points[self.ptr]
        self.ptr += self.direction
        self.step_walker = StepWalker(
            self.bot,
            self.bot.config.walk,
            self.next_point['lat'],
            self.next_point['lng'],
            label='SpiralNavigator'
        )

    def take_step(self):
        if self.step_walker is None:
            self.walk_to_next_point()

        dist = distance(
            self.bot.api._position_lat,
            self.bot.api._position_lng,
            self.next_point['lat'],
            self.next_point['lng']
        )

        logger.log('Spiraling from ' + str((self.bot.api._position_lat, self.bot.api._position_lng)) +
            ' to ' + str([self.next_point['lat'], self.next_point['lng']]) + ' ' +
            format_dist(dist, self.bot.config.distance_unit))

        if self.step_walker.step():
            self.step_walker = None


# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import math

from pokemongo_bot.cell_workers.utils import distance, format_dist
from pokemongo_bot.step_walker import StepWalker
from pokemongo_bot.base_task import BaseTask

class FollowSpiral(BaseTask):
    SUPPORTED_TASK_API_VERSION = 1

    def initialize(self):
        self.steplimit = self.config.get("diameter", 4)
        self.step_size = self.config.get("step_size", 70)
        self.origin_lat = self.bot.position[0]
        self.origin_lon = self.bot.position[1]

        self.diameter_to_steps = (self.steplimit+1) ** 2
        self.points = self._generate_spiral(
            self.origin_lat, self.origin_lon, self.step_size, self.diameter_to_steps
        )

        self.ptr = 0
        self.direction = 1
        self.cnt = 0


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

        rlat = starting_lat * math.pi
        latdeg = 111132.93 - 559.82 * math.cos(2*rlat) + 1.175*math.cos(4*rlat)
        lngdeg = 111412.84 * math.cos(rlat) - 93.5 * math.cos(3*rlat)
        step_size_lat = step_size / latdeg
        step_size_lng = step_size / lngdeg

        while steps < step_limit:
            while 2 * x * d < m and steps < step_limit:
                x = x + d
                steps += 1
                lat = x * step_size_lat + starting_lat
                lng = y * step_size_lng + starting_lng
                coords.append({'lat': lat, 'lng': lng})
            while 2 * y * d < m and steps < step_limit:
                y = y + d
                steps += 1
                lat = x * step_size_lat + starting_lat
                lng = y * step_size_lng + starting_lng
                coords.append({'lat': lat, 'lng': lng})

            d *= -1
            m += 1
        return coords

    def work(self):
        last_lat = self.bot.api._position_lat
        last_lng = self.bot.api._position_lng

        point = self.points[self.ptr]
        self.cnt += 1

        dist = distance(
            last_lat,
            last_lng,
            point['lat'],
            point['lng']
        )

        if self.bot.config.walk_max > 0:
            step_walker = StepWalker(
                self.bot,
                point['lat'],
                point['lng']
            )

            if self.cnt == 1:
                self.emit_event(
                    'position_update',
                    formatted="Walking from {last_position} to {current_position} ({distance} {distance_unit})",
                    data={
                        'last_position': (last_lat, last_lng, 0),
                        'current_position': (point['lat'], point['lng'], 0),
                        'distance': dist,
                        'distance_unit': 'm'
                    }
                )

            if step_walker.step():
                step_walker = None
        else:
            self.bot.api.set_position(point['lat'], point['lng'], 0)

            self.emit_event(
                'position_update',
                formatted="Teleported from {last_position} to {current_position} ({distance} {distance_unit})",
                data={
                    'last_position': (last_lat, last_lng, 0),
                    'current_position': (point['lat'], point['lng'], 0),
                    'distance': dist,
                    'distance_unit': 'm'
                }
            )

        if dist <= 1 or (self.bot.config.walk_min > 0 and step_walker == None):
            if self.ptr + self.direction >= len(self.points) or self.ptr + self.direction <= -1:
                self.direction *= -1
            if len(self.points) != 1:
                self.ptr += self.direction
            else:
                self.ptr = 0
            self.cnt = 0

        return [point['lat'], point['lng']]

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import math
import time
from geopy.distance import great_circle

from pokemongo_bot.base_task import BaseTask
from pokemongo_bot.cell_workers.utils import coord2merc, merc2coord
from pokemongo_bot.constants import Constants
from pokemongo_bot.walkers.polyline_walker import PolylineWalker
from pokemongo_bot.worker_result import WorkerResult
from pokemongo_bot.item_list import Item
from pokemongo_bot import inventory

LOG_TIME_INTERVAL = 60
NO_LURED_TIME_MALUS = 5
NO_BALLS_MOVING_TIME = 5 * 60


class CampFort(BaseTask):
    SUPPORTED_TASK_API_VERSION = 1

    def __init__(self, bot, config):
        super(CampFort, self).__init__(bot, config)

    def initialize(self):
        self.destination = None
        self.stay_until = 0
        self.move_until = 0
        self.walker = None
        self.no_log_until = 0

        self.config_max_distance = self.config.get("max_distance", 2000)
        self.config_min_forts_count = self.config.get("min_forts_count", 2)
        self.config_min_lured_forts_count = self.config.get("min_lured_forts_count", 1)
        self.config_camping_time = self.config.get("camping_time", 1800)
        self.config_moving_time = self.config.get("moving_time", 600)

    def work(self):
        if not self.enabled:
            return WorkerResult.SUCCESS

        now = time.time()

        if now < self.move_until:
            return WorkerResult.SUCCESS

        if 0 < self.stay_until < now:
            self.destination = None
            self.stay_until = 0
            self.move_until = now + self.config_moving_time

            if self.config_moving_time > 0:
                return WorkerResult.SUCCESS

        # Let's make sure we have balls before we sit at a lure!
        # See also catch_pokemon.py
        if self.get_pokeball_count() <= 0:
            self.emit_event(
                'refuse_to_sit',
                formatted='No pokeballs left, refuse to sit at lure!',
            )
            # Move away from lures for a time
            self.destination = None
            self.stay_until = 0
            self.move_until = now + max(self.config_moving_time, NO_BALLS_MOVING_TIME)

            return WorkerResult.SUCCESS

        if self.destination is None:
            forts = self.get_forts()
            forts_clusters = self.get_forts_clusters(forts)

            if len(forts_clusters) > 0:
                self.destination = forts_clusters[0]
                self.walker = PolylineWalker(self.bot, self.destination[0], self.destination[1])
                self.emit_event(
                    'new_destination',
                    formatted='New destination at {} meters: {} forts, {} lured'.format(
                        round(self.destination[4], 2), self.destination[3], self.destination[2]))
                self.no_log_until = now + LOG_TIME_INTERVAL
            else:
                return WorkerResult.SUCCESS

        if self.stay_until >= now:
            cluster = self.get_current_cluster()

            if self.no_log_until < now:
                self.emit_event(
                    'staying_at_destination',
                    formatted='Staying at destination: {} forts, {} lured'.format(
                        cluster[3], cluster[2]))

                self.no_log_until = now + LOG_TIME_INTERVAL

            if cluster[2] == 0:
                self.stay_until -= NO_LURED_TIME_MALUS

            self.walker.step(speed=0)
        elif self.walker.step():
            cluster = self.get_current_cluster()
            self.emit_event(
                'arrived_at_destination',
                formatted='Arrived at destination: {} forts, {} lured'.format(
                    cluster[3], cluster[2]))
            self.stay_until = now + self.config_camping_time
        elif self.no_log_until < now:
            cluster = self.get_current_cluster()

            if cluster[2] == 0:

                self.emit_event(
                    'reset_destination',
                    formatted="Lures gone! Resetting destination!")
                self.destination = None
                self.stay_until = 0
                return WorkerResult.SUCCESS

            self.emit_event(
                'moving_to_destination',
                formatted="Moving to destination at {} meters: {} forts, {} lured".format(
                round(cluster[4], 2), cluster[3], cluster[2])
            )
            self.no_log_until = now + LOG_TIME_INTERVAL

        return WorkerResult.RUNNING

    def get_pokeball_count(self):
        return sum([inventory.items().get(ball.value).count for ball in [Item.ITEM_POKE_BALL, Item.ITEM_GREAT_BALL, Item.ITEM_ULTRA_BALL]])

    def get_forts(self):
        radius = self.config_max_distance + Constants.MAX_DISTANCE_FORT_IS_REACHABLE

        forts = [f for f in self.bot.cell["forts"] if ("latitude" in f) and ("type" in f)]
        forts = [f for f in forts if self.get_distance(self.bot.start_position, f) <= radius]

        return forts

    def get_forts_clusters(self, forts):
        clusters = []
        points = self.get_all_snap_points(forts)

        for c1, c2, fort1, fort2 in points:
            cluster_1 = self.get_cluster(forts, c1)
            cluster_2 = self.get_cluster(forts, c2)
            cluster_key_1 = self.get_cluster_key(cluster_1)
            cluster_key_2 = self.get_cluster_key(cluster_2)
            radius = Constants.MAX_DISTANCE_FORT_IS_REACHABLE

            if cluster_key_1 >= cluster_key_2:
                cluster = cluster_1

                while True:
                    new_circle, _ = self.get_enclosing_circles(fort1, fort2, radius - 1)

                    if not new_circle:
                        break

                    new_cluster = self.get_cluster(forts, new_circle)

                    if new_cluster[3] < cluster[3]:
                        break

                    cluster = new_cluster
                    radius -= 1
            else:
                cluster = cluster_2

                while True:
                    _, new_circle = self.get_enclosing_circles(fort1, fort2, radius - 1)

                    if not new_circle:
                        break

                    new_cluster = self.get_cluster(forts, new_circle)

                    if new_cluster[3] < cluster[3]:
                        break

                    cluster = new_cluster
                    radius -= 1

            clusters.append(cluster)

        clusters = [c for c in clusters if c[2] >= self.config_min_lured_forts_count]
        clusters = [c for c in clusters if c[3] >= self.config_min_forts_count]
        clusters.sort(key=lambda c: self.get_cluster_key(c), reverse=True)

        return clusters

    def get_all_snap_points(self, forts):
        points = []
        radius = Constants.MAX_DISTANCE_FORT_IS_REACHABLE

        for i in range(0, len(forts)):
            for j in range(i + 1, len(forts)):
                c1, c2 = self.get_enclosing_circles(forts[i], forts[j], radius)

                if c1 and c2:
                    points.append((c1, c2, forts[i], forts[j]))

        return points

    def get_enclosing_circles(self, fort1, fort2, radius):
        # This is an approximation which is good enough for us
        # since we are dealing with small distances
        x1, y1 = coord2merc(fort1["latitude"], fort1["longitude"])
        x2, y2 = coord2merc(fort2["latitude"], fort2["longitude"])
        dx = x2 - x1
        dy = y2 - y1
        d = math.sqrt(dx ** 2 + dy ** 2)

        if (d == 0) or (d > 2 * radius):
            return None, None

        cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
        cd = math.sqrt(radius ** 2 - (d / 2) ** 2)

        c1 = merc2coord((cx - cd * dy / d, cy + cd * dx / d)) + (radius,)
        c2 = merc2coord((cx + cd * dy / d, cy - cd * dx / d)) + (radius,)

        return c1, c2

    def get_cluster(self, forts, circle):
        forts_in_circle = [f for f in forts if self.get_distance(circle, f) <= circle[2]]
        count = len(forts_in_circle)
        lured = len([f for f in forts_in_circle if "active_fort_modifier" in f])
        dst = great_circle(self.bot.position, circle).meters

        return (circle[0], circle[1], lured, count, dst)

    def get_cluster_key(self, cluster):
        return (cluster[2], cluster[3], -cluster[4])

    def get_current_cluster(self):
        forts = self.get_forts()
        circle = (self.destination[0], self.destination[1], Constants.MAX_DISTANCE_FORT_IS_REACHABLE)
        return self.get_cluster(forts, circle)

    def get_distance(self, location, fort):
        return great_circle(location, (fort["latitude"], fort["longitude"])).meters

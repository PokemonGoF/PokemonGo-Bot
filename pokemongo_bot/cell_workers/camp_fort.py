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
        self.clusters = None
        self.cluster = None
        self.walker = None
        self.bot.camping_forts = False
        self.stay_until = 0
        self.move_until = 0
        self.no_log_until = 0
        self.no_recheck_cluster_until = 0

        self.config_max_distance = self.config.get("max_distance", 2000)
        self.config_min_forts_count = self.config.get("min_forts_count", 2)
        self.config_min_lured_forts_count = self.config.get("min_lured_forts_count", 1)
        self.config_camping_time = self.config.get("camping_time", 1800)
        self.config_moving_time = self.config.get("moving_time", 600)

    def work(self):
        if not self.enabled:
            return WorkerResult.SUCCESS

        if self.bot.catch_disabled:
            if not hasattr(self.bot,"camper_disabled_global_warning") or \
                        (hasattr(self.bot,"camper_disabled_global_warning") and not self.bot.camper_disabled_global_warning):
                self.logger.info("All catching tasks are currently disabled until {}. Camping of lured forts disabled till then.".format(self.bot.catch_resume_at.strftime("%H:%M:%S")))
            self.bot.camper_disabled_global_warning = True
            return WorkerResult.SUCCESS
        else:
            self.bot.camper_disabled_global_warning = False

        if self.bot.softban:
            if not hasattr(self.bot, "camper_softban_global_warning") or \
                        (hasattr(self.bot, "camper_softban_global_warning") and not self.bot.camper_softban_global_warning):
                self.logger.info("Possible softban! Not camping forts till fixed.")
            self.bot.camper_softban_global_warning = True
            return WorkerResult.SUCCESS
        else:
            self.bot.softban_global_warning = False

        now = time.time()

        if now < self.move_until:
            return WorkerResult.SUCCESS

        if 0 < self.stay_until < now:
            self.cluster = None
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
            self.cluster = None
            self.stay_until = 0
            self.move_until = now + max(self.config_moving_time, NO_BALLS_MOVING_TIME)

            return WorkerResult.SUCCESS

        forts = self.get_forts()

        if self.cluster is None:
            if self.clusters is None:
                self.clusters = self.get_clusters(forts.values())
            # self.logger.info("Forts: {}".format(len(forts)))
            # self.logger.info("Checking {} clusters for availiblity....".format(len(self.clusters)))
            available_clusters = self.get_available_clusters(forts)

            if len(available_clusters) > 0:
                self.cluster = available_clusters[0]
                self.walker = PolylineWalker(self.bot, self.cluster["center"][0], self.cluster["center"][1])

                self.no_log_until = now + LOG_TIME_INTERVAL
                self.no_recheck_cluster_until = now + NO_BALLS_MOVING_TIME
                self.emit_event("new_destination",
                                formatted='New destination at {distance:.2f} meters: {size} forts, {lured} lured'.format(**self.cluster))
            else:
                # self.logger.info("No clusters found.")
                self.cluster = None
                self.clusters = None
                return WorkerResult.SUCCESS

        # We can check if the cluster is still the best
        elif self.no_recheck_cluster_until < now:
            self.clusters = self.get_clusters(forts.values())
            available_clusters = self.get_available_clusters(forts)
            if len(available_clusters) > 0:
                if self.cluster is not available_clusters[0]:
                    self.cluster = available_clusters[0]
                    self.stay_until = 0
                    self.emit_event("new_destination",
                                    formatted='Better destination found at {distance:.2f} meters: {size} forts, {lured} lured'.format(**self.cluster))
            self.no_recheck_cluster_until = now + NO_BALLS_MOVING_TIME

        self.update_cluster_distance(self.cluster)
        self.update_cluster_lured(self.cluster, forts)

        if self.stay_until >= now:
            if self.no_log_until < now:
                self.no_log_until = now + LOG_TIME_INTERVAL
                self.bot.camping_forts = True
                self.emit_event("staying_at_destination",
                                formatted='Staying at destination: {size} forts, {lured} lured'.format(**self.cluster))

            if self.cluster["lured"] == 0:
                self.bot.camping_forts = False # Allow hunter to move
                self.stay_until -= NO_LURED_TIME_MALUS

            self.walker.step(speed=0)
        elif self.walker.step():
            self.stay_until = now + self.config_camping_time
            self.bot.camping_forts = True
            self.emit_event("arrived_at_destination",
                            formatted="Arrived at destination: {size} forts, {lured} lured.".format(**self.cluster))
        elif self.no_log_until < now:
            if self.cluster["lured"] == 0:
                self.cluster = None
                self.bot.camping_forts = False
                self.emit_event("reset_destination",
                                formatted="Lures gone! Resetting destination!")
            else:
                self.no_log_until = now + LOG_TIME_INTERVAL
                self.emit_event("moving_to_destination",
                                formatted="Moving to destination at {distance:.2f} meters: {size} forts, {lured} lured".format(**self.cluster))

        return WorkerResult.RUNNING

    def get_pokeball_count(self):
        return sum([inventory.items().get(ball.value).count for ball in [Item.ITEM_POKE_BALL, Item.ITEM_GREAT_BALL, Item.ITEM_ULTRA_BALL]])

    def get_forts(self):
        radius = self.config_max_distance + Constants.MAX_DISTANCE_FORT_IS_REACHABLE

        forts = [f for f in self.bot.cell["forts"] if ("latitude" in f) and ("type" in f)]
        forts = [f for f in forts if self.get_distance(self.bot.start_position, f) <= radius]

        return {f["id"]: f for f in forts}

    def get_available_clusters(self, forts):
        for cluster in self.clusters:
            self.update_cluster_distance(cluster)
            self.update_cluster_lured(cluster, forts)

        available_clusters = [c for c in self.clusters if c["lured"] >= self.config_min_lured_forts_count]
        available_clusters = [c for c in available_clusters if c["size"] >= self.config_min_forts_count]
        available_clusters.sort(key=lambda c: self.get_cluster_key(c), reverse=True)

        return available_clusters

    def get_clusters(self, forts):
        clusters = []
        points = self.get_all_snap_points(forts)

        for c1, c2, fort1, fort2 in points:
            cluster_1 = self.get_cluster(forts, c1)
            cluster_2 = self.get_cluster(forts, c2)

            self.update_cluster_distance(cluster_1)
            self.update_cluster_distance(cluster_2)

            key_1 = self.get_cluster_key(cluster_1)
            key_2 = self.get_cluster_key(cluster_2)

            radius = Constants.MAX_DISTANCE_FORT_IS_REACHABLE

            if key_1 >= key_2:
                cluster = cluster_1

                while True:
                    new_circle, _ = self.get_enclosing_circles(fort1, fort2, radius - 1)

                    if not new_circle:
                        break

                    new_cluster = self.get_cluster(cluster["forts"], new_circle)

                    if len(new_cluster["forts"]) < len(cluster["forts"]):
                        break

                    cluster = new_cluster
                    radius -= 1
            else:
                cluster = cluster_2

                while True:
                    _, new_circle = self.get_enclosing_circles(fort1, fort2, radius - 1)

                    if not new_circle:
                        break

                    new_cluster = self.get_cluster(cluster["forts"], new_circle)

                    if len(new_cluster["forts"]) < len(cluster["forts"]):
                        break

                    cluster = new_cluster
                    radius -= 1

            clusters.append(cluster)

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

        cluster = {"center": (circle[0], circle[1]),
                   "distance": 0,
                   "forts": forts_in_circle,
                   "size": len(forts_in_circle),
                   "lured": sum(1 for f in forts_in_circle if f.get("active_fort_modifier", None) is not None)}

        return cluster

    def get_cluster_key(self, cluster):
        return (cluster["lured"], cluster["size"], -cluster["distance"])

    def update_cluster_distance(self, cluster):
        cluster["distance"] = great_circle(self.bot.position, cluster["center"]).meters

    def update_cluster_lured(self, cluster, forts):
        cluster["lured"] = sum(1 for f in cluster["forts"] if forts.get(f["id"], {}).get("active_fort_modifier", None) is not None)

    def get_distance(self, location, fort):
        return great_circle(location, (fort["latitude"], fort["longitude"])).meters

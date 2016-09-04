import math
import time

from pokemongo_bot.base_task import BaseTask
from pokemongo_bot.cell_workers.utils import distance, coord2merc, merc2coord
from pokemongo_bot.constants import Constants
from pokemongo_bot.human_behaviour import random_lat_long_delta, random_alt_delta
from pokemongo_bot.walkers.polyline_walker import PolylineWalker
from pokemongo_bot.worker_result import WorkerResult


class CampFort(BaseTask):
    SUPPORTED_TASK_API_VERSION = 1

    def __init__(self, bot, config):
        super(CampFort, self).__init__(bot, config)

    def initialize(self):
        self.destination = None
        self.stay_until = 0
        self.move_until = 0
        self.last_position_update = 0
        self.walker = None

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

        if self.destination is None:
            forts = self.get_forts()
            forts_clusters = self.get_forts_clusters(forts)

            if len(forts_clusters) > 0:
                self.destination = forts_clusters[0]
                self.logger.info("New destination at %s meters: %s forts, %s lured.", int(self.destination[4]), self.destination[3], self.destination[2])
            else:
                # forts = [f for f in forts if f.get("cooldown_complete_timestamp_ms", 0) < now * 1000]
                # fort = min(forts, key=lambda f: self.dist(self.bot.position, f))
                # self.destination = (fort["latitude"], fort["longitude"])
                return WorkerResult.SUCCESS

        if (now - self.last_position_update) < 1:
            return WorkerResult.RUNNING
        else:
            self.last_position_update = now

        if self.stay_until >= now:
            lat = self.destination[0] + random_lat_long_delta() / 5
            lon = self.destination[1] + random_lat_long_delta() / 5
            alt = self.walker.pol_alt + random_alt_delta() / 2
            self.bot.api.set_position(lat, lon, alt)
        else:
            self.walker = PolylineWalker(self.bot, self.destination[0], self.destination[1])
            self.walker.step()

            dst = distance(self.bot.position[0], self.bot.position[1], self.destination[0], self.destination[1])

            if dst < 1:
                forts = self.get_forts()
                circle = (self.destination[0], self.destination[1], Constants.MAX_DISTANCE_FORT_IS_REACHABLE)
                cluster = self.get_cluster(forts, circle)

                self.logger.info("Arrived at destination: %s forts, %s lured.", cluster[3], cluster[2])
                self.stay_until = now + self.config_camping_time

        return WorkerResult.RUNNING

    def get_forts(self):
        radius = self.config_max_distance + Constants.MAX_DISTANCE_FORT_IS_REACHABLE

        forts = [f for f in self.bot.cell["forts"] if ("latitude" in f) and ("type" in f)]
        forts = [f for f in forts if self.dist(self.bot.start_position, f) <= radius]

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
        forts_in_circle = [f for f in forts if self.dist(circle, f) <= circle[2]]
        count = len(forts_in_circle)
        lured = len([f for f in forts_in_circle if "active_fort_modifier" in f])
        dst = distance(self.bot.position[0], self.bot.position[1], circle[0], circle[1])

        return (circle[0], circle[1], lured, count, dst)

    def get_cluster_key(self, cluster):
        return (cluster[2], cluster[3], -cluster[4])

    def dist(self, location, fort):
        return distance(location[0], location[1], fort["latitude"], fort["longitude"])

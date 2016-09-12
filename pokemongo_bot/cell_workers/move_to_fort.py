# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import time
from geopy.distance import great_circle

from pokemongo_bot import inventory
from pokemongo_bot.walkers.walker_factory import walker_factory
from pokemongo_bot.worker_result import WorkerResult
from pokemongo_bot.base_task import BaseTask
from pokemongo_bot.constants import Constants
from utils import distance, format_dist, fort_details


class MoveToFort(BaseTask):
    SUPPORTED_TASK_API_VERSION = 1

    def initialize(self):
        self.lure_distance = 0
        self.wait_log_sent = None
        self.destination = None
        self.walker = None

        self.lure_attraction = self.config.get("lure_attraction", True)
        self.lure_max_distance = self.config.get("lure_max_distance", 2000)
        self.ignore_item_count = self.config.get("ignore_item_count", False)
        self.config_walker = self.config.get('walker', 'StepWalker')
        self.wait_at_fort = self.config.get('wait_on_lure', False)

    def should_run(self):
        has_space_for_loot = inventory.Items.has_space_for_loot()
        if not has_space_for_loot and not self.ignore_item_count:
            self.emit_event(
                'inventory_full',
                formatted="Inventory is full. You might want to change your config to recycle more items if this message appears consistently."
            )
        return has_space_for_loot or self.ignore_item_count or self.bot.softban

    def is_attracted(self):
        return (self.lure_distance > 0)

    def work(self):
        if not self.should_run():
            return WorkerResult.SUCCESS

        if self.destination is None:
            self.destination = self.get_nearest_fort()

            if self.destination is not None:
                self.walker = walker_factory(self.config_walker, self.bot, self.destination['latitude'], self.destination['longitude'])
                self.walker.is_arrived = self.walker_is_arrived
            else:
                return WorkerResult.SUCCESS

        fortID = self.destination['id']
        details = fort_details(self.bot, fortID, self.destination['latitude'], self.destination['longitude'])
        fort_name = details.get('name', 'Unknown')

        if not self.walker.step():
            self.wait_log_sent = None

            dist = distance(self.bot.position[0], self.bot.position[1], self.destination['latitude'], self.destination['longitude'])
            unit = self.bot.config.distance_unit  # Unit to use when printing formatted distance

            fort_event_data = {'fort_name': u"{}".format(fort_name),
                               'distance': format_dist(dist, unit)}

            if self.is_attracted() > 0:
                fort_event_data.update(lure_distance=format_dist(self.lure_distance, unit))

                self.emit_event('moving_to_lured_fort',
                                formatted="Moving towards pokestop {fort_name} - {distance} (attraction of lure {lure_distance})",
                                data=fort_event_data)
            else:
                self.emit_event('moving_to_fort',
                                formatted="Moving towards pokestop {fort_name} - {distance}",
                                data=fort_event_data)
        elif self.destination.get('active_fort_modifier') and self.wait_at_fort:
            now = time.time()

            if (self.wait_log_sent is None) or (self.wait_log_sent < now - 60):
                self.wait_log_sent = now

                self.emit_event('arrived_at_fort',
                                formatted='Waiting near fort %s until lure module expires' % fort_name)
        else:
            self.destination = None

            self.emit_event('arrived_at_fort',
                            formatted='Arrived at fort.')

        return WorkerResult.RUNNING

    def walker_is_arrived(self):
        return great_circle(self.bot.position, (self.walker.dest_lat, self.walker.dest_lng)).meters < Constants.MAX_DISTANCE_FORT_IS_REACHABLE

    def _get_nearest_fort_on_lure_way(self, forts):

        if not self.lure_attraction:
            return None, 0

        lures = filter(lambda x: True if x.get('lure_info', None) != None else False, forts)
        if self.wait_at_fort:
            lures = filter(lambda x: x.get('active_fort_modifier', False), forts)

        if len(lures):
            dist_lure_me = distance(self.bot.position[0], self.bot.position[1],
                                    lures[0]['latitude'], lures[0]['longitude'])
        else:
            dist_lure_me = 0

        if dist_lure_me > 0 and dist_lure_me < self.lure_max_distance:

            self.lure_distance = dist_lure_me

            for fort in forts:
                dist_lure_fort = distance(
                    fort['latitude'],
                    fort['longitude'],
                    lures[0]['latitude'],
                    lures[0]['longitude'])
                dist_fort_me = distance(
                    fort['latitude'],
                    fort['longitude'],
                    self.bot.position[0],
                    self.bot.position[1])

                if dist_lure_fort < dist_lure_me and dist_lure_me > dist_fort_me:
                    return fort, dist_lure_me

                if dist_fort_me > dist_lure_me:
                    break

            return lures[0], dist_lure_me

        else:
            return None, 0

    def get_nearest_fort(self):
        forts = self.bot.get_forts(order_by_distance=True)
        # Remove stops that are still on timeout
        forts = filter(
            lambda x: x["id"] not in self.bot.fort_timeouts or (
                x.get('active_fort_modifier', False) and self.wait_at_fort
            ),
            forts
        )

        next_attracted_pts, lure_distance = self._get_nearest_fort_on_lure_way(forts)

        # Remove all forts which were spun in the last ticks to avoid circles if set
        if self.bot.config.forts_avoid_circles or not self.wait_at_fort:
            forts = filter(lambda x: x["id"] not in self.bot.recent_forts, forts)

        self.lure_distance = lure_distance

        if (lure_distance > 0):
            return next_attracted_pts

        if len(forts):
            return forts[0]
        else:
            return None

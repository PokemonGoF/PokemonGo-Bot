# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import absolute_import

from pokemongo_bot import inventory
from pokemongo_bot.constants import Constants
from pokemongo_bot.walkers.walker_factory import walker_factory
from pokemongo_bot.worker_result import WorkerResult
from pokemongo_bot.base_task import BaseTask
from .utils import distance, format_dist, fort_details
from datetime import datetime, timedelta

class MoveToFort(BaseTask):
    SUPPORTED_TASK_API_VERSION = 1

    def initialize(self):
        self.lure_distance = 0
        self.lure_attraction = self.config.get("lure_attraction", True)
        self.lure_max_distance = self.config.get("lure_max_distance", 2000)
        self.ignore_item_count = self.config.get("ignore_item_count", False)
        self.fort_ids = []
        self.walker = self.config.get('walker', 'StepWalker')
        self.wait_at_fort = self.config.get('wait_on_lure', False)
        self.wait_log_sent = None

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

        nearest_fort = self.get_nearest_fort()

        if nearest_fort is None:
            return WorkerResult.SUCCESS

        lat = nearest_fort['latitude']
        lng = nearest_fort['longitude']
        fortID = nearest_fort['id']
        details = fort_details(self.bot, fortID, lat, lng)
        fort_name = details.get('name', 'Unknown')

        unit = self.bot.config.distance_unit  # Unit to use when printing formatted distance

        dist = distance(
            self.bot.position[0],
            self.bot.position[1],
            lat,
            lng
        )
        noised_dist = distance(
            self.bot.noised_position[0],
            self.bot.noised_position[1],
            lat,
            lng
        )

        moving = noised_dist > Constants.MAX_DISTANCE_FORT_IS_REACHABLE if self.bot.config.replicate_gps_xy_noise else dist > Constants.MAX_DISTANCE_FORT_IS_REACHABLE

        if moving:
            self.wait_log_sent = None
            fort_event_data = {
                'fort_name': u"{}".format(fort_name),
                'distance': format_dist(dist, unit),
            }

            if self.is_attracted() > 0:
                fort_event_data.update(lure_distance=format_dist(self.lure_distance, unit))
                self.emit_event(
                    'moving_to_lured_fort',
                    formatted="Moving towards pokestop {fort_name} - {distance} (attraction of lure {lure_distance})",
                    data=fort_event_data
                )
            else:
                self.emit_event(
                    'moving_to_fort',
                    formatted="Moving towards pokestop {fort_name} - {distance}",
                    data=fort_event_data
                )

            step_walker = walker_factory(self.walker,
                self.bot,
                lat,
                lng
            )

            if not step_walker.step():
                return WorkerResult.RUNNING
        else:
            if not self.bot.catch_disabled and nearest_fort.get('active_fort_modifier') and self.wait_at_fort:
                if self.wait_log_sent == None or self.wait_log_sent < datetime.now() - timedelta(seconds=60):
                    self.wait_log_sent = datetime.now()
                    self.emit_event(
                        'arrived_at_fort',
                        formatted='Waiting near fort %s until lure module expires' % fort_name
                    )
            else:
                self.emit_event(
                    'arrived_at_fort',
                    formatted='Arrived at fort %s.' % fort_name
                )

        return WorkerResult.RUNNING

    def _get_nearest_fort_on_lure_way(self, forts):
        if not self.lure_attraction:
            return None, 0

        lures = filter(lambda x: True if x.get('lure_info', None) != None else False, forts)
        if not self.bot.catch_disabled and self.wait_at_fort:
            lures = filter(lambda x: x.get('active_fort_modifier', False), forts)

        if len(lures):
            dist_lure_me = distance(self.bot.position[0], self.bot.position[1],
                                    lures[0]['latitude'],lures[0]['longitude'])
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
        nearest_fort = []
        forts = self.bot.get_forts(order_by_distance=True)
        # Remove stops that are still on timeout
        forts = filter(
            lambda x: x["id"] not in self.bot.fort_timeouts or (
                x.get('active_fort_modifier', False) and self.wait_at_fort and not self.bot.catch_disabled
            ),
            forts
        )

        next_attracted_pts, lure_distance = self._get_nearest_fort_on_lure_way(forts)

        # Remove all forts which were spun in the last ticks to avoid circles if set
        if self.bot.config.forts_avoid_circles or not self.wait_at_fort or self.bot.catch_disabled:
            forts = filter(lambda x: x["id"] not in self.bot.recent_forts, forts)

        self.lure_distance = lure_distance

        if (lure_distance > 0):
            return next_attracted_pts

        if len(forts) >= 3:
            # Get ID of fort, store it. Check index 0 & index 2. Both must not be same
            nearest_fort = forts[0]
            
            if len(self.fort_ids) < 3:
                self.fort_ids.extend(nearest_fort['id'])
            else:
                #this will always be len of 3, compare index 1 and nearest_fort
                if self.fort_ids[1] == nearest_fort['id'] and self.fort_ids[0] == self.fort_ids[2]:
                    self.fort_ids.pop(0)
                    # take the next nearest, assuming bot is bouncing between index 0 and 1
                    nearest_fort = forts[2]
                    self.fort_ids.extend(nearest_fort['id'])
                else:
                    self.fort_ids.pop(0)
                    self.fort_ids.extend(nearest_fort['id'])
                    
            return nearest_fort
        else:
            return None

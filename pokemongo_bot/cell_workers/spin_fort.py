# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json
import os
import time

from pgoapi.utilities import f2i
from pokemongo_bot import inventory

from pokemongo_bot.constants import Constants
from pokemongo_bot.human_behaviour import action_delay
from pokemongo_bot.worker_result import WorkerResult
from pokemongo_bot.base_task import BaseTask
from pokemongo_bot.base_dir import _base_dir
from utils import distance, format_time, fort_details
from pokemongo_bot.datastore import Datastore

SPIN_REQUEST_RESULT_SUCCESS = 1
SPIN_REQUEST_RESULT_OUT_OF_RANGE = 2
SPIN_REQUEST_RESULT_IN_COOLDOWN_PERIOD = 3
SPIN_REQUEST_RESULT_INVENTORY_FULL = 4


class SpinFort(Datastore, BaseTask):
    SUPPORTED_TASK_API_VERSION = 1

    def __init__(self, bot, config):
        super(SpinFort, self).__init__(bot, config)
    def initialize(self):
        self.ignore_item_count = self.config.get("ignore_item_count", False)
        self.spin_wait_min = self.config.get("spin_wait_min", 2)
        self.spin_wait_max = self.config.get("spin_wait_max", 3)

    def should_run(self):
        has_space_for_loot = inventory.Items.has_space_for_loot()
        if not has_space_for_loot and not self.ignore_item_count:
            self.emit_event(
                'inventory_full',
                formatted="Inventory is full. You might want to change your config to recycle more items if this message appears consistently."
            )
        return self.ignore_item_count or has_space_for_loot

    def work(self):
        forts = self.get_forts_in_range()

        if not self.should_run() or len(forts) == 0:
            return WorkerResult.SUCCESS

        fort = forts[0]

        lat = fort['latitude']
        lng = fort['longitude']

        details = fort_details(self.bot, fort['id'], lat, lng)
        fort_name = details.get('name', 'Unknown')

        response_dict = self.bot.api.fort_search(
            fort_id=fort['id'],
            fort_latitude=lat,
            fort_longitude=lng,
            player_latitude=f2i(self.bot.position[0]),
            player_longitude=f2i(self.bot.position[1])
        )

        if ('responses' in response_dict) and ('FORT_SEARCH' in response_dict['responses']):
            spin_details = response_dict['responses']['FORT_SEARCH']
            spin_result = spin_details.get('result', -1)

            if (spin_result == SPIN_REQUEST_RESULT_SUCCESS) or (spin_result == SPIN_REQUEST_RESULT_INVENTORY_FULL):
                self.bot.softban = False
                experience_awarded = spin_details.get('experience_awarded', 0)
                items_awarded = self.get_items_awarded_from_fort_spinned(response_dict)

                if experience_awarded or items_awarded:
                    self.emit_event(
                        'spun_pokestop',
                        formatted="Spun pokestop {pokestop}. Experience awarded: {exp}. Items awarded: {items}",
                        data={
                            'pokestop': fort_name,
                            'exp': experience_awarded,
                            'items': items_awarded
                        }
                    )
                else:
                    self.emit_event(
                        'pokestop_empty',
                        formatted='Found nothing in pokestop {pokestop}.',
                        data={'pokestop': fort_name}
                    )
                with self.bot.database as conn:
                    c = conn.cursor()
                    c.execute("SELECT COUNT(name) FROM sqlite_master WHERE type='table' AND name='pokestop_log'")
                result = c.fetchone()        
                while True:
                    if result[0] == 1:
                        conn.execute('''INSERT INTO pokestop_log (pokestop, exp, items) VALUES (?, ?, ?)''', (fort_name, str(experience_awarded), str(items_awarded)))
                        break
                    else:
                        self.emit_event(
                        'pokestop_log',
                        sender=self,
                        level='info',
                        formatted="pokestop_log table not found, skipping log"
                        )
                        break
                pokestop_cooldown = spin_details.get(
                    'cooldown_complete_timestamp_ms')
                self.bot.fort_timeouts.update({fort["id"]: pokestop_cooldown})
                self.bot.recent_forts = self.bot.recent_forts[1:] + [fort['id']]
            elif spin_result == SPIN_REQUEST_RESULT_OUT_OF_RANGE:
                self.emit_event(
                    'pokestop_out_of_range',
                    formatted="Pokestop {pokestop} out of range.",
                    data={'pokestop': fort_name}
                )
            elif spin_result == SPIN_REQUEST_RESULT_IN_COOLDOWN_PERIOD:
                pokestop_cooldown = spin_details.get(
                    'cooldown_complete_timestamp_ms')
                if pokestop_cooldown:
                    self.bot.fort_timeouts.update({fort["id"]: pokestop_cooldown})
                    seconds_since_epoch = time.time()
                    minutes_left = format_time(
                        (pokestop_cooldown / 1000) - seconds_since_epoch
                    )
                    self.emit_event(
                        'pokestop_on_cooldown',
                        formatted="Pokestop {pokestop} on cooldown. Time left: {minutes_left}.",
                        data={'pokestop': fort_name, 'minutes_left': minutes_left}
                    )
            else:
                self.emit_event(
                    'unknown_spin_result',
                    formatted="Unknown spint result {status_code}",
                    data={'status_code': str(spin_result)}
                )
            if 'chain_hack_sequence_number' in response_dict['responses'][
                    'FORT_SEARCH']:
                action_delay(self.spin_wait_min, self.spin_wait_max)
                return response_dict['responses']['FORT_SEARCH'][
                    'chain_hack_sequence_number']
            else:
                self.emit_event(
                    'pokestop_searching_too_often',
                    formatted="Possibly searching too often, take a rest."
                )
                if spin_result == 1 and not items_awarded and not experience_awarded and not pokestop_cooldown:
                    self.bot.softban = True
                    self.emit_event(
                        'softban',
                        formatted='Probably got softban.'
                    )
                    with self.bot.database as conn:
                        c = conn.cursor()
                        c.execute("SELECT COUNT(name) FROM sqlite_master WHERE type='table' AND name='softban_log'")
                    result = c.fetchone()        
                    
                    if result[0] == 1:
                        source = str("PokemonCatchWorker")
                        status = str("Possible Softban")
                        conn.execute('''INSERT INTO softban_log (status, source) VALUES (?, ?)''', (status, source))
                    else:
                        self.emit_event(
                        'softban_log',
                        sender=self,
                        level='info',
                        formatted="softban_log table not found, skipping log"
                        )
                        
                self.bot.fort_timeouts[fort["id"]] = (time.time() + 300) * 1000  # Don't spin for 5m
                    
                return WorkerResult.ERROR
        action_delay(self.spin_wait_min, self.spin_wait_max)

        if len(forts) > 1:
            return WorkerResult.RUNNING

        return WorkerResult.SUCCESS

    def get_forts_in_range(self):
        forts = self.bot.get_forts(order_by_distance=True)
        forts = filter(lambda fort: fort["id"] not in self.bot.fort_timeouts, forts)
        if self.bot.config.replicate_gps_xy_noise:
            forts = filter(lambda fort: distance(
                self.bot.noised_position[0],
                self.bot.noised_position[1],
                fort['latitude'],
                fort['longitude']
            ) <= Constants.MAX_DISTANCE_FORT_IS_REACHABLE, forts)
        else:
            forts = filter(lambda fort: distance(
                self.bot.position[0],
                self.bot.position[1],
                fort['latitude'],
                fort['longitude']
            ) <= Constants.MAX_DISTANCE_FORT_IS_REACHABLE, forts)

        return forts

    def get_items_awarded_from_fort_spinned(self, response_dict):
        items_awarded = response_dict['responses']['FORT_SEARCH'].get('items_awarded', {})
        if items_awarded:
            tmp_count_items = {}
            for item_awarded in items_awarded:

                item_awarded_id = item_awarded['item_id']
                item_awarded_name = inventory.Items.name_for(item_awarded_id)
                item_awarded_count = item_awarded['item_count']

                if not item_awarded_name in tmp_count_items:
                    tmp_count_items[item_awarded_name] = item_awarded_count
                else:
                    tmp_count_items[item_awarded_name] += item_awarded_count

                self._update_inventory(item_awarded)

            return tmp_count_items

    # TODO : Refactor this class, hide the inventory update right after the api call
    def _update_inventory(self, item_awarded):
        inventory.items().get(item_awarded['item_id']).add(item_awarded['item_count'])

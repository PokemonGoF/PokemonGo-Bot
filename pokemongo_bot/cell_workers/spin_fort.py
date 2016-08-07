# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import time

from pgoapi.utilities import f2i

from pokemongo_bot.constants import Constants
from pokemongo_bot.human_behaviour import sleep
from pokemongo_bot.worker_result import WorkerResult
from pokemongo_bot.base_task import BaseTask
from utils import distance, format_time, fort_details


class SpinFort(BaseTask):
    SUPPORTED_TASK_API_VERSION = 1

    def should_run(self):
        if not self.bot.has_space_for_loot():
            self.emit_event(
                'inventory_full',
                formatted="Not moving to any forts as there aren't enough space. You might want to change your config to recycle more items if this message appears consistently."
            )
            return False
        return True

    def work(self):
        fort = self.get_fort_in_range()

        if not self.should_run() or fort is None:
            return WorkerResult.SUCCESS

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
        if 'responses' in response_dict and \
                'FORT_SEARCH' in response_dict['responses']:

            spin_details = response_dict['responses']['FORT_SEARCH']
            spin_result = spin_details.get('result', -1)
            if spin_result == 1:
                self.bot.softban = False
                experience_awarded = spin_details.get('experience_awarded', 0)
                items_awarded = spin_details.get('items_awarded', {})
                if items_awarded:
                    self.bot.latest_inventory = None
                    tmp_count_items = {}
                    for item in items_awarded:
                        item_id = item['item_id']
                        item_name = self.bot.item_list[str(item_id)]
                        if not item_name in tmp_count_items:
                            tmp_count_items[item_name] = item['item_count']
                        else:
                            tmp_count_items[item_name] += item['item_count']

                if experience_awarded or items_awarded:
                    self.emit_event(
                        'spun_pokestop',
                        formatted="Spun pokestop {pokestop}. Experience awarded: {exp}. Items awarded: {items}",
                        data={
                            'pokestop': fort_name,
                            'exp': experience_awarded,
                            'items': tmp_count_items
                        }
                    )
                else:
                    self.emit_event(
                        'pokestop_empty',
                        formatted='Found nothing in pokestop {pokestop}.',
                        data={'pokestop': fort_name}
                    )
                pokestop_cooldown = spin_details.get(
                    'cooldown_complete_timestamp_ms')
                self.bot.fort_timeouts.update({fort["id"]: pokestop_cooldown})
                self.bot.recent_forts = self.bot.recent_forts[1:] + [fort['id']]
            elif spin_result == 2:
                self.emit_event(
                    'pokestop_out_of_range',
                    formatted="Pokestop {pokestop} out of range.",
                    data={'pokestop': fort_name}
                )
            elif spin_result == 3:
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
            elif spin_result == 4:
                self.emit_event(
                    'inventory_full',
                    formatted="Inventory is full!"
                )
            else:
                self.emit_event(
                    'unknown_spin_result',
                    formatted="Unknown spint result {status_code}",
                    data={'status_code': str(spin_result)}
                )
            if 'chain_hack_sequence_number' in response_dict['responses'][
                    'FORT_SEARCH']:
                time.sleep(2)
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
                else:
                    self.bot.fort_timeouts[fort["id"]] = (time.time() + 300) * 1000  # Don't spin for 5m
                return 11
        sleep(2)
        return 0

    def get_fort_in_range(self):
        forts = self.bot.get_forts(order_by_distance=True)

        forts = filter(lambda x: x["id"] not in self.bot.fort_timeouts, forts)

        if len(forts) == 0:
            return None

        fort = forts[0]

        distance_to_fort = distance(
            self.bot.position[0],
            self.bot.position[1],
            fort['latitude'],
            fort['longitude']
        )

        if distance_to_fort <= Constants.MAX_DISTANCE_FORT_IS_REACHABLE:
            return fort

        return None

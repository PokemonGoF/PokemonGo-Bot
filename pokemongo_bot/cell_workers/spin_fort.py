# -*- coding: utf-8 -*-

import time

from pgoapi.utilities import f2i

from pokemongo_bot import logger
from pokemongo_bot.constants import Constants
from pokemongo_bot.human_behaviour import sleep
from pokemongo_bot.worker_result import WorkerResult
from pokemongo_bot.cell_workers.base_task import BaseTask
from utils import distance, format_time, fort_details


class SpinFort(BaseTask):
    def work(self, *args, **kwargs):
        forts = self.get_fort_in_range()

        for fort in forts:
            self.spin_fort(fort)
            time.sleep(1)

        return WorkerResult.SUCCESS


    def spin_fort(self, fort):
        lat = fort['latitude']
        lng = fort['longitude']

        details = fort_details(self.bot, fort['id'], lat, lng)
        fort_name = details.get('name', 'Unknown').encode('utf8', 'replace')
        # logger.log('Now at Pokestop: {0}'.format(fort_name), 'cyan')
        # logger.log('Spinning ...', 'cyan')

        self.bot.api.fort_search(fort_id=fort['id'],
                             fort_latitude=lat,
                             fort_longitude=lng,
                             player_latitude=f2i(self.bot.position[0]),
                             player_longitude=f2i(self.bot.position[1]))
        response_dict = self.bot.api.call()
        if 'responses' in response_dict and \
                'FORT_SEARCH' in response_dict['responses']:

            spin_details = response_dict['responses']['FORT_SEARCH']
            spin_result = spin_details.get('result', -1)
            if spin_result == 1:
                self.bot.softban = False
                experience_awarded = spin_details.get('experience_awarded', False)
                if experience_awarded:
                    logger.log('[{:>+5d} xp] POKESTOP'.format(experience_awarded), 'green')

                items_awarded = spin_details.get('items_awarded', False)
                if items_awarded:
                    self.bot.latest_inventory = None
                    tmp_count_items = {}
                    for item in items_awarded:
                        item_id = item['item_id']
                        if not item_id in tmp_count_items:
                            tmp_count_items[item_id] = item['item_count']
                        else:
                            tmp_count_items[item_id] += item['item_count']

                    for item_id, item_count in tmp_count_items.iteritems():
                        item_name = self.bot.item_list[str(item_id)]
                        logger.log('+{} {} (Total: {})'.format(item_count, item_name, self.bot.item_inventory_count(item_id)))

                else:
                    logger.log('[#] Nothing found.')

                pokestop_cooldown = spin_details.get('cooldown_complete_timestamp_ms')
                self.bot.fort_timeouts.update({ fort['id']: pokestop_cooldown })

                self.bot.recent_forts = self.bot.recent_forts[1:] + [fort['id']]
            elif spin_result == 2:
                logger.log('[#] Pokestop out of range')
            elif spin_result == 3:
                pokestop_cooldown = spin_details.get(
                    'cooldown_complete_timestamp_ms')
                if pokestop_cooldown:
                    self.bot.fort_timeouts.update({fort["id"]: pokestop_cooldown})
                    seconds_since_epoch = time.time()
                    logger.log('PokeStop on cooldown. Time left: ' + str(
                        format_time((pokestop_cooldown / 1000) -
                                    seconds_since_epoch)))
            elif spin_result == 4:
                # Invetory Full
                self.bot.softban = False
                experience_awarded = spin_details.get('experience_awarded', False)
                if experience_awarded:
                    logger.log('[{:>+5d} xp] POKESTOP'.format(experience_awarded), 'green')
            else:
                logger.log('Unknown spin result: ' + str(spin_result), 'red')

            if 'chain_hack_sequence_number' in response_dict['responses']['FORT_SEARCH']:
                time.sleep(1)
                return response_dict['responses']['FORT_SEARCH']['chain_hack_sequence_number']
            else:
                logger.log('Possibly searching too often - taking a short rest :)', 'yellow')
                if spin_result == 1 and not items_awarded and not experience_awarded and not pokestop_cooldown:
                    self.bot.softban = True
                    logger.log('[!] Possibly got softban too...', 'red')
                else:
                    self.bot.fort_timeouts[fort['id']] = (time.time() + 300) * 1000  # Don't spin for 5m
                return 11
        return 0


    def get_fort_in_range(self):
        forts = self.bot.get_forts(order_by_distance=True)

        forts = filter(lambda x: 'cooldown_complete_timestamp_ms' not in x, forts)

        forts = filter(lambda x: x["id"] not in self.bot.fort_timeouts, forts)

        forts_in_range = []

        for fort in forts:

            distance_to_fort = distance(
                self.bot.position[0],
                self.bot.position[1],
                fort['latitude'],
                fort['longitude']
            )

            if distance_to_fort <= Constants.MAX_DISTANCE_FORT_IS_REACHABLE:
                forts_in_range.append(fort)

        return forts_in_range

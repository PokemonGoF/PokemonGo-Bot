# -*- coding: utf-8 -*-

import time

from pgoapi.utilities import f2i

from pokemongo_bot import logger
from pokemongo_bot.constants import Constants
from pokemongo_bot.human_behaviour import sleep
from pokemongo_bot.worker_result import WorkerResult
from utils import distance, format_time

class SeenFortWorker(object):
    def __init__(self, bot):
        self.api = bot.api
        self.bot = bot
        self.fort_timeouts = bot.fort_timeouts
        self.position = bot.position
        self.config = bot.config
        self.item_list = bot.item_list

    def should_run(self):
        return self.config.forts_spin and self.bot.has_space_for_loot()

    def work(self):
        fort = self.get_fort_in_range()

        if (not self.should_run() or fort == None):
            return WorkerResult.SUCCESS

        lat = fort['latitude']
        lng = fort['longitude']

        logger.log('Spinning ...', 'cyan')

        self.api.fort_search(fort_id=fort['id'],
                             fort_latitude=lat,
                             fort_longitude=lng,
                             player_latitude=f2i(self.position[0]),
                             player_longitude=f2i(self.position[1]))
        response_dict = self.api.call()
        if 'responses' in response_dict and \
                'FORT_SEARCH' in response_dict['responses']:

            spin_details = response_dict['responses']['FORT_SEARCH']
            spin_result = spin_details.get('result', -1)
            if spin_result == 1:
                logger.log("Loot: ", 'green')
                experience_awarded = spin_details.get('experience_awarded',
                                                      False)
                if experience_awarded:
                    logger.log(str(experience_awarded) + " xp",
                               'green')

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
                        item_name = self.item_list[str(item_id)]
                        logger.log('- ' + str(item_count) + "x " + item_name + " (Total: " + str(self.bot.item_inventory_count(item_id)) + ")", 'yellow')
                else:
                    logger.log("[#] Nothing found.", 'yellow')

                pokestop_cooldown = spin_details.get(
                    'cooldown_complete_timestamp_ms')
                self.bot.fort_timeouts.update({fort["id"]: pokestop_cooldown})
                if pokestop_cooldown:
                    seconds_since_epoch = time.time()
                    logger.log('PokeStop on cooldown. Time left: ' + str(
                        format_time((pokestop_cooldown / 1000) -
                                    seconds_since_epoch)))

                if not items_awarded and not experience_awarded and not pokestop_cooldown:
                    message = (
                        'Stopped at Pokestop and did not find experience, items '
                        'or information about the stop cooldown. You are '
                        'probably softbanned. Try to play on your phone, '
                        'if pokemons always ran away and you find nothing in '
                        'PokeStops you are indeed softbanned. Please try again '
                        'in a few hours.')
                    raise RuntimeError(message)

                self.bot.recent_forts = self.bot.recent_forts[1:] + [fort['id']]
            elif spin_result == 2:
                logger.log("[#] Pokestop out of range")
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
                logger.log("Inventory is full", 'red')
            else:
                logger.log("Unknown spin result: " + str(spin_result), 'red')

            if 'chain_hack_sequence_number' in response_dict['responses'][
                    'FORT_SEARCH']:
                time.sleep(2)
                return response_dict['responses']['FORT_SEARCH'][
                    'chain_hack_sequence_number']
            else:
                logger.log('Possibly searching too often - taking a short rest :)', 'yellow')
                self.bot.fort_timeouts[fort["id"]] = (time.time() + 300) * 1000  # Don't spin for 5m
                return 11
        sleep(2)
        return 0

    def get_fort_in_range(self):
        forts = self.bot.get_forts(order_by_distance=True)

        forts = filter(lambda x: x["id"] not in self.fort_timeouts, forts)

        if len(forts) == 0:
            return None

        fort = forts[0]

        distance_to_fort = distance(
            self.position[0],
            self.position[1],
            fort['latitude'],
            fort['longitude']
        )

        if distance_to_fort <= Constants.MAX_DISTANCE_FORT_IS_REACHABLE:
            return fort

        return None

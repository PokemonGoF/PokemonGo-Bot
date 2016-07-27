# -*- coding: utf-8 -*-

import time

from pgoapi.utilities import f2i

from pokemongo_bot import logger
from pokemongo_bot.human_behaviour import sleep
from utils import format_time


class SeenFortWorker(object):
    def __init__(self, fort, bot):
        self.fort = fort
        self.api = bot.api
        self.bot = bot
        self.position = bot.position
        self.config = bot.config
        self.item_list = bot.item_list
        self.rest_time = 50

    def work(self):
        lat = self.fort['latitude']
        lng = self.fort['longitude']

        self.api.fort_details(fort_id=self.fort['id'],
                              latitude=lat,
                              longitude=lng)
        response_dict = self.api.call()
        if 'responses' in response_dict \
                and'FORT_DETAILS' in response_dict['responses'] \
                and 'name' in response_dict['responses']['FORT_DETAILS']:
            fort_details = response_dict['responses']['FORT_DETAILS']
            fort_name = fort_details['name'].encode('utf8', 'replace')
        else:
            fort_name = 'Unknown'
        logger.log('Now at Pokestop: ' + fort_name + ' - Spinning...',
                   'cyan')
        sleep(2)
        self.api.fort_search(fort_id=self.fort['id'],
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


                        # RECYCLING UNWANTED ITEMS
                        id_filter = self.config.item_filter.get(str(item_id), 0)
                        if id_filter is not 0:
                            id_filter_keep = id_filter.get('keep',20)
                        new_bag_count = self.bot.item_inventory_count(item_id)
                        if str(item_id) in self.config.item_filter and new_bag_count >= id_filter_keep:
                            #RECYCLE_INVENTORY_ITEM
                            items_recycle_count = new_bag_count - id_filter_keep
                            logger.log("-- Recycling " + str(items_recycle_count) + "x " + item_name + " to match filter "+ str(id_filter_keep) +"...", 'green')
                            response_dict_recycle = self.bot.drop_item(item_id=item_id, count=items_recycle_count)

                            result = 0
                            if response_dict_recycle and \
                                'responses' in response_dict_recycle and \
                                'RECYCLE_INVENTORY_ITEM' in response_dict_recycle['responses'] and \
                                'result' in response_dict_recycle['responses']['RECYCLE_INVENTORY_ITEM']:
                                result = response_dict_recycle['responses']['RECYCLE_INVENTORY_ITEM']['result']

                            if result is 1: # Request success
                                logger.log("-- Recycled " + item_name + "!", 'green')
                            else:
                                logger.log("-- Recycling " + item_name + "has failed!", 'red')
                else:
                    logger.log("[#] Nothing found.", 'yellow')

                pokestop_cooldown = spin_details.get(
                    'cooldown_complete_timestamp_ms')
                self.bot.fort_timeouts.update({self.fort["id"]: pokestop_cooldown})
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
            elif spin_result == 2:
                logger.log("[#] Pokestop out of range")
            elif spin_result == 3:
                pokestop_cooldown = spin_details.get(
                    'cooldown_complete_timestamp_ms')
                if pokestop_cooldown:
                    self.bot.fort_timeouts.update({self.fort["id"]: pokestop_cooldown})
                    seconds_since_epoch = time.time()
                    logger.log('PokeStop on cooldown. Time left: ' + str(
                        format_time((pokestop_cooldown / 1000) -
                                    seconds_since_epoch)))
            elif spin_result == 4:
                logger.log("Inventory is full, switching to catch mode...", 'red')
                #self.config.mode = 'poke'
                self.api.get_player()
                response_dict_player = self.api.call()
                player = response_dict_player['responses']['GET_PLAYER']['player_data']
                items_count = self.bot.get_inventory_count('item')
                items_stock = self.bot.current_inventory()
                self.bot.check_inventory_space(items_count, player['max_item_storage'], items_stock.copy())
            else:
                logger.log("Unknown spin result: " + str(spin_result), 'red')

            if 'chain_hack_sequence_number' in response_dict['responses'][
                    'FORT_SEARCH']:
                time.sleep(2)
                return response_dict['responses']['FORT_SEARCH'][
                    'chain_hack_sequence_number']
            else:
                logger.log('Possibly searching too often - taking a short rest :)', 'yellow')
                self.bot.fort_timeouts[self.fort["id"]] = (time.time() + 300) * 1000  # Don't spin for 5m
                return 11
        sleep(8)
        return 0

    @staticmethod
    def closest_fort(current_lat, current_long, forts):
        print x

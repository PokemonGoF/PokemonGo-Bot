# -*- coding: utf-8 -*-

import time
import random

from pgoapi.utilities import f2i

from pokemongo_bot import logger
from pokemongo_bot.human_behaviour import sleep
from pokemongo_bot.cell_workers import PokemonCatchWorker
from utils import format_time


class SeenFortWorker(object):
    def __init__(self, fort, bot):
        self.fort = fort
        self.api = bot.api
        self.bot = bot
        self.position = bot.position
        self.config = bot.config
        self.item_list = bot.item_list
        self.pokemon_list = bot.pokemon_list
        self.inventory = bot.inventory
        self.current_inventory = bot.current_inventory
        self.item_inventory_count = bot.item_inventory_count
        self.metrics = bot.metrics
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
        logger.log('Now at Pokestop: ' + fort_name,
                   'cyan')
        if self.config.catch_pokemon and 'lure_info' in self.fort:
            # Check if the lure has a pokemon active
            if 'encounter_id' in self.fort['lure_info']:
                logger.log("Found a lure on this pokestop! Catching pokemon...", 'cyan')

                pokemon = {
                    'encounter_id': self.fort['lure_info']['encounter_id'],
                    'fort_id': self.fort['id'],
                    'latitude': self.fort['latitude'],
                    'longitude': self.fort['longitude']
                }

                self.catch_pokemon(pokemon)

            else:
                logger.log('Found a lure, but there is no pokemon present.', 'yellow')
            sleep(2)

        logger.log('Spinning ...', 'cyan')

        self.api.fort_search(fort_id=self.fort['id'],
                             fort_latitude=lat,
                             fort_longitude=lng,
                             player_latitude=f2i(self.position[0]),
                             player_longitude=f2i(self.position[1]))
        response_dict = self.api.call()
        if 'responses' in response_dict and \
                'FORT_SEARCH' in response_dict['responses']:

            self.spin_details = response_dict['responses']['FORT_SEARCH']
            self.spin_result = spin_details.get('result', -1)

            if spin_result == 1:
                logger.log("Loot: ", 'green')
                experience_awarded = spin_details.get('experience_awarded', False)
                ps_cooldowntimer()
                
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

                if not items_awarded and not experience_awarded and not self.spin_details.get('cooldown_complete_timestamp_ms'):
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
                ps_cooldowntimer()
            
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
                logger.log('PokeStop on Cooldown timer. Time: ' + str(format_time((actual_pokestop_cooldown / 1000))))
                return 11
        sleep(2)
        return 0

    def ps_cooldowntimer():
        actual_pokestop_cooldown = self.spin_details.get('cooldown_complete_timestamp_ms')
        ran_pokestop_cooldown = actual_pokestop_cooldown + ((time.time() + random.randint(int(self.config.add_fort_cooldown['cd_min_delta']), int(self.config.add_fort_cooldown['cd_max_delta']))) * 1000)
        if self.config.add_fort_cooldown['add_cooldown_time'] == 'random' and ran_pokestopcooldown >= 300:
            self.bot.fort_timeouts[self.fort["id"]] = ran_pokestop_cooldown
            logger.log('PokeStop on Cooldown timer. Time: ' + str(format_time((ran_pokestop_cooldown / 1000))))
        elif int(self.config.add_fort_cooldown['add_cooldown_time']) >= 0:
            self.bot.fort_timeouts[self.fort["id"]] = actual_pokestop_cooldown + int(self.config.add_fort_cooldown['add_cooldown_time'])
            logger.log('PokeStop on Cooldown timer. Time: ' + str(format_time((ran_pokestop_cooldown / 1000))))
        else:
            self.bot.fort_timeouts[self.fort["id"]] = actual_pokestop_cooldown
            logger.log('PokeStop on Cooldown timer. Time: ' + str(format_time((actual_pokestop_cooldown / 1000))))
          
    def catch_pokemon(self, pokemon):
        worker = PokemonCatchWorker(pokemon, self.bot)
        return_value = worker.work()

        # Disabled for now, importing InitialTransferWorker fails.
        # if return_value == PokemonCatchWorker.BAG_FULL:
        #    worker = InitialTransferWorker(self)
        #    worker.work()

        return return_value

    @staticmethod
    def closest_fort(current_lat, current_long, forts):
        print x

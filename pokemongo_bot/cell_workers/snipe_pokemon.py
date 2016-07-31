import json
import os
import re
import sys
import time

from . import PokemonCatchWorker
from pokemongo_bot import logger
from utils import distance

class SnipePokemon(object):

    def __init__(self, bot, config):
        self.bot = bot
        self.api = bot.api
        self.config = config
        self.pokemon_list = bot.pokemon_list
        self.position = bot.position

        self._process_config()

    def _process_config(self):
        # process additional configs

    def work(self):
        while True:
            location = raw_input('Enter snipe location: ')
            location = location.replace(' ', '')

            if len(location) > 0:
                self.snipe_pokemon(location)
            else:
                break   


    def snipe_pokemon(self, location, delay=2): 
        prevPosition = self.bot.position

        # Check if session token has expired
        self.bot.check_session(self.bot.position[0:2])
        self.bot.heartbeat()

        # Teleport to location
        logger.log('Teleport to location..', 'green')
        latitude, longitude = location.split(',')
        self.api.set_position(float(latitude), float(longitude), 0)
        self.cell = self.bot.get_meta_cell()

        catch_pokemon = None
        if 'catchable_pokemons' in self.cell and len(self.cell['catchable_pokemons']) > 0:
            logger.log('Something rustles nearby!')
            # Sort all by distance from current pos- eventually this should
            # build graph & A* it
            self.cell['catchable_pokemons'].sort(
                key=
                lambda x: distance(self.position[0], self.position[1], x['latitude'], x['longitude']))


            user_web_catchable = 'web/catchable-%s.json' % (self.bot.config.username)
            for pokemon in self.cell['catchable_pokemons']:
                with open(user_web_catchable, 'w') as outfile:
                    json.dump(pokemon, outfile)

                with open(user_web_catchable, 'w') as outfile:
                    json.dump({}, outfile)

            catch_pokemon = self.cell['catchable_pokemons'][0]

            # Try to catch VIP pokemon
            for pokemon in self.cell['catchable_pokemons']:
                pokemon_num = int(pokemon['pokemon_id']) - 1   
                pokemon_name = self.pokemon_list[int(pokemon_num)]['Name']
                vip_name = self.bot.config.vips.get(pokemon_name)
                if vip_name == {}:
                    logger.log('Found a VIP pokemon: ' + pokemon_name, 'green')
                    catch_pokemon = pokemon

                    # if VIP pokemon is nearest, break loop
                    if pokemon == self.cell['catchable_pokemons'][0]:
                        break
        
        if 'wild_pokemons' in self.cell and len(self.cell['wild_pokemons']) > 0 and not catch_pokemon:
            # Sort all by distance from current pos- eventually this should
            # build graph & A* it
            self.cell['wild_pokemons'].sort(
                key=
                lambda x: distance(self.position[0], self.position[1], x['latitude'], x['longitude']))
            catch_pokemon = self.cell['wild_pokemons'][0]

        if not catch_pokemon:
            logger.log('No pokemon found!', 'yellow')
            time.sleep(delay)
            # go back 
            self.api.set_position(*prevPosition)
            time.sleep(delay)
            self.heartbeat()

        catchWorker = PokemonCatchWorker(catch_pokemon, self.bot)
        
        logger.log('Encounter pokemon', 'green')
        apiEncounterResponse = catchWorker.create_encounter_api_call()

        time.sleep(delay)
        # go back 
        logger.log('Teleport back previous location..', 'green')
        self.api.set_position(*prevPosition)
        # wait for go back
        time.sleep(delay)
        self.bot.heartbeat()

        catchWorker.work(apiEncounterResponse)

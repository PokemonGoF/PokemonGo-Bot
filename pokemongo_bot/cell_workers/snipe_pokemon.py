import json
import os
import re
import sys
import time

from . import PokemonCatchWorker
from base_task import BaseTask
from pokemongo_bot import logger
from utils import distance

class SnipePokemon(BaseTask):

    def initialize(self):
        self.api = self.bot.api
        self.pokemon_list = self.bot.pokemon_list
        self.position = self.bot.position

    def work(self):
        if self.bot.config.snipe_list == None:
            return
        self.start_sniping()

    def start_sniping(self):
        try:
            logger.log('Reading snipping list.', 'green')
            with open(self.bot.config.snipe_list, 'r+') as f:
                try:
                    locations_json = json.load(f)
                except ValueError:
                    logger.log('Invalid json file', 'error')
                    return

                try:
                    locations = locations_json['locations']
                except KeyError:
                    logger.log('Failed to parse sniping locations', 'red')
                    return

                if isinstance(locations, list) and len(locations):
                    while locations:
                        location = locations.pop(0)
                        logger.log('Found location: ' + location, 'green')
                        location = location.replace(' ', '')
                        pattern = '^(\-?\d+(\.\d+)?),\s*(\-?\d+(\.\d+)?)$'
                        if not re.match(pattern, location):
                            logger.log('Wrong format location!', 'red')
                            continue
                        self.snipe_pokemon(location)
                        f.seek(0)
                        try:
                            json.dump(locations_json, f)
                        except IOError:
                            logger.log('Failed to remove location from snipe list.', 'red')
                            return
                        except:
                            logger.log('Unknown Error occurred attempting to remove location from snipe list.', 'red')
                        f.truncate()
                else:
                    logger.log('No locations to snipe!', 'yellow')
                return
        except IOError:
            logger.log('Error reading sniping list!', 'red')
            return

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
            self.bot.heartbeat()

            return None

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

        # Catch 'em all
        catchWorker.work(apiEncounterResponse)

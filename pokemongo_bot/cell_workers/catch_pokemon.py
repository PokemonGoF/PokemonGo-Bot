# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import absolute_import

import json
import os
import random

from pokemongo_bot.base_task import BaseTask
from pokemongo_bot.cell_workers.pokemon_catch_worker import PokemonCatchWorker
from pokemongo_bot.worker_result import WorkerResult
from pokemongo_bot.item_list import Item
from pokemongo_bot import inventory
from .utils import fort_details, distance,  format_time
from pokemongo_bot.base_dir import _base_dir
from pokemongo_bot.constants import Constants
from pokemongo_bot.inventory import Pokemons

class CatchPokemon(BaseTask):
    SUPPORTED_TASK_API_VERSION = 1

    def initialize(self):
        self.pokemon = []
        self.ignored_while_looking = []

    def work(self):
        # make sure we have SOME balls
        if sum([inventory.items().get(ball.value).count for ball in
    [Item.ITEM_POKE_BALL, Item.ITEM_GREAT_BALL, Item.ITEM_ULTRA_BALL]]) <= 0:
            return WorkerResult.ERROR

        if self.bot.softban:
            if not hasattr(self.bot, "softban_global_warning") or \
                        (hasattr(self.bot, "softban_global_warning") and not self.bot.softban_global_warning):
                self.logger.info("Possible softban! Not trying to catch Pokemon.")
            self.bot.softban_global_warning = True
            return WorkerResult.SUCCESS
        else:
            self.bot.softban_global_warning = False

	# Don't try to catch a Pokemon when catching is disabled.
        if self.bot.catch_disabled:
            if not hasattr(self.bot,"all_disabled_global_warning") or \
                        (hasattr(self.bot,"all_disabled_global_warning") and not self.bot.all_disabled_global_warning):
                self.logger.info("All catching tasks are currently disabled until {}. Ignoring all Pokemon till then.".format(self.bot.catch_resume_at.strftime("%H:%M:%S")))
            self.bot.all_disabled_global_warning = True
            return WorkerResult.SUCCESS
        else:
            self.bot.all_disabled_global_warning = False

        # check if we have already loaded a list
        if len(self.pokemon) <= 0:
            # load available pokemon by config settings
            if self.config.get('catch_visible_pokemon', True):
                self.get_visible_pokemon()
            if self.config.get('catch_lured_pokemon', True):
                self.get_lured_pokemon()
            if self._have_applied_incense() and self.config.get('catch_incensed_pokemon', True):
                self.get_incensed_pokemon()

            random.shuffle(self.pokemon)

        # Filter out already ignored mons
        if hasattr(self.bot,"hunter_locked_target"):
            if self.bot.hunter_locked_target != None:
                self.pokemon = filter(lambda x: x["pokemon_id"] not in self.ignored_while_looking, self.pokemon)
            elif len(self.ignored_while_looking) > 0:
                self.logger.info("No longer hunting for a Pokémon, resuming normal operations.")
                # Reset the ignored list when no longer needed.
                self.ignored_while_looking = []

        if hasattr(self.bot, "skipped_pokemon"):
            # Skip pokemon the catcher told us to ignore
            self.pokemon = [ p for p in self.pokemon if p not in self.bot.skipped_pokemon ]

        num_pokemon = len(self.pokemon)

        if num_pokemon > 0:
            # try catching
            mon_to_catch = self.pokemon.pop()
            is_vip = hasattr(mon_to_catch, "pokemon_id") and self._is_vip_pokemon(mon_to_catch['pokemon_id'])
            # Always catch VIP Pokemons!
            if hasattr(self.bot,"hunter_locked_target") and self.bot.hunter_locked_target != None:
                bounty = self.bot.hunter_locked_target
                mon_name = Pokemons.name_for(mon_to_catch['pokemon_id'])
                bounty_name = Pokemons.name_for(bounty['pokemon_id'])

                if mon_name != bounty_name and is_vip == False:
                    # This is not the Pokémon you are looking for...
                    self.logger.info("[Hunter locked a {}] Ignoring a {}".format(bounty_name, mon_name))
                    self.ignored_while_looking.append(mon_to_catch['pokemon_id'])

                    if num_pokemon > 1:
                        return WorkerResult.RUNNING
                    else:
                        return WorkerResult.SUCCESS
                else:
                    # We have found a vip or our target...
                    if bounty_name == mon_name:
                        self.bot.hunter_locked_target = None
                        self.logger.info("Found my target {}!".format(bounty_name))
                    else:
                        self.logger.info("While on the hunt for {}, I found a {}! I need that Pokemon! Will try to catch...".format(bounty_name, mon_name))
            try:
                if self.catch_pokemon(mon_to_catch) == WorkerResult.ERROR:
                    # give up incase something went wrong in our catch worker (ran out of balls, etc)
                    return WorkerResult.ERROR
                elif num_pokemon > 1:
                    # we have more pokemon to catch
                    return WorkerResult.RUNNING
            except ValueError:
                return WorkerResult.ERROR

        # all pokemon have been processed
        return WorkerResult.SUCCESS

    def _is_vip_pokemon(self, pokemon_id):
        # having just a name present in the list makes them vip
        # Not seen pokemons also will become vip if it's not disabled in config
        if self.bot.config.vips.get(Pokemons.name_for(pokemon_id)) == {}:
            return True
        if (not inventory.pokedex().seen(pokemon_id)):
            return True
        # If we need the Pokemon for an evolution, catch it.
        if any(not inventory.pokedex().seen(fid) for fid in self.get_family_ids(pokemon_id)):
            # self.logger.info('Found a Pokemon whoes family is not yet complete in Pokedex!')
            return True

        return False

    def get_visible_pokemon(self):
        pokemon_to_catch = []
        if 'catchable_pokemons' in self.bot.cell:
            pokemon_to_catch = self.bot.cell['catchable_pokemons']

            if len(pokemon_to_catch) > 0:
                user_web_catchable = os.path.join(_base_dir, 'web', 'catchable-{}.json'.format(self.bot.config.username))
            for pokemon in pokemon_to_catch:
                # Update web UI
                with open(user_web_catchable, 'w') as outfile:
                    json.dump(pokemon, outfile)

                self.emit_event(
                    'catchable_pokemon',
                    level='debug',
                    data={
                        'pokemon_id': pokemon['pokemon_id'],
                        'spawn_point_id': pokemon['spawn_point_id'],
                        'encounter_id': pokemon['encounter_id'],
                        'latitude': pokemon['latitude'],
                        'longitude': pokemon['longitude'],
                        'expiration_timestamp_ms': pokemon['expiration_timestamp_ms'],
                        'pokemon_name': Pokemons.name_for(pokemon['pokemon_id']),
                    }
                )

                self.add_pokemon(pokemon)

        if 'wild_pokemons' in self.bot.cell:
            for pokemon in self.bot.cell['wild_pokemons']:
                self.add_pokemon(pokemon)

    def get_lured_pokemon(self):
        if hasattr(self.bot,"hunter_locked_target") and self.bot.hunter_locked_target != None:
            # self.logger.info('Hunting Pokemon, ignoring lured Pokemons')
            return True

        forts_in_range = []
        forts = self.bot.get_forts(order_by_distance=False)

        if len(forts) == 0:
            return []

        for fort in forts:
            distance_to_fort = distance(
                self.bot.position[0],
                self.bot.position[1],
                fort['latitude'],
                fort['longitude']
            )

            # See if we have an encounter at this fort
            encounter_id = fort.get('lure_info', {}).get('encounter_id', None)
            if distance_to_fort < Constants.MAX_DISTANCE_FORT_IS_REACHABLE and encounter_id:
                forts_in_range.append(fort)


        for fort in forts_in_range:

            details = fort_details(self.bot, fort_id=fort['id'],
                                  latitude=fort['latitude'],
                                  longitude=fort['longitude'])
            fort_name = details.get('name', 'Unknown')
            encounter_id = fort['lure_info']['encounter_id']

            if hasattr(self.bot, "skipped_pokemon"):
                # Skip pokemon the catcher told us to ignore
                for p in self.bot.skipped_pokemon:
                    if p.encounter_id == encounter_id:
                        # ignore this one, move on
                        break

            pokemon = {
                'encounter_id': encounter_id,
                'fort_id': fort['id'],
                'fort_name': u"{}".format(fort_name),
                'latitude': fort['latitude'],
                'longitude': fort['longitude']
            }
            if hasattr(self.bot, 'skipped_pokemon'):
                if pokemon['encounter_id'] not in \
                    map(lambda pokemon: pokemon.encounter_id, self.bot.skipped_pokemon):
                    self.emit_event(
                        'lured_pokemon_found',
                        level='info',
                        formatted='Lured pokemon at fort {fort_name} ({fort_id})',
                        data=pokemon
                    )
            else:
                self.emit_event(
                    'lured_pokemon_found',
                    level='info',
                    formatted='Lured pokemon at fort {fort_name} ({fort_id})',
                    data=pokemon
                )

            self.add_pokemon(pokemon)

    def get_incensed_pokemon(self):
        # call self.bot.api.get_incense_pokemon
        pokemon_to_catch = self.bot.api.get_incense_pokemon()

        if len(pokemon_to_catch) > 0:
            for pokemon in pokemon_to_catch:
                self.logger.warning("Pokemon: %s", pokemon)
                self.emit_event(
                    'incensed_pokemon_found',
                    level='info',
                    formatted='Incense attracted a pokemon at {encounter_location}',
                    data=pokemon
                )

                self.add_pokemon(pokemon)

    def add_pokemon(self, pokemon):
        if pokemon['encounter_id'] not in \
                map(lambda pokemon: pokemon['encounter_id'], self.pokemon):
            self.pokemon.append(pokemon)

    def catch_pokemon(self, pokemon):
        worker = PokemonCatchWorker(pokemon, self.bot, self.config)
        return_value = worker.work()

        return return_value

    def _have_applied_incense(self):
        for applied_item in inventory.applied_items().all():
            self.logger.info(applied_item)
            if applied_item.expire_ms > 0:
                mins = format_time(applied_item.expire_ms * 1000)
                self.logger.info("Not applying incense, currently active: %s, %s minutes remaining", applied_item.item.name, mins)
                return True
            else:
                self.logger.info("")
                return False
        return False

    def get_family_ids(self, pokemon_id):
        family_id = inventory.pokemons().data_for(pokemon_id).first_evolution_id
        ids = [family_id]
        ids += inventory.pokemons().data_for(family_id).next_evolutions_all[:]

        return ids

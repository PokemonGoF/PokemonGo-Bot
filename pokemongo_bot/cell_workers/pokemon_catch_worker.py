# -*- coding: utf-8 -*-

import time
from collections import defaultdict
from operator import itemgetter
from utils import distance, print_green, print_yellow, print_red
from pokemongo_bot.human_behaviour import sleep

class PokemonCatchWorker(object):

    def __init__(self, pokemon, bot):
        self.pokemon = pokemon
        self.api = bot.api
        self.bot = bot;
        self.position = bot.position
        self.config = bot.config
        self.pokemon_list = bot.pokemon_list
        self.item_list = bot.item_list
        self.inventory = bot.inventory

    def work(self):
        encounter_id = self.pokemon['encounter_id']
        spawnpoint_id = self.pokemon['spawnpoint_id']
        player_latitude = self.pokemon['latitude']
        player_longitude = self.pokemon['longitude']
        self.api.encounter(encounter_id=encounter_id,spawnpoint_id=spawnpoint_id,player_latitude=player_latitude,player_longitude=player_longitude)
        response_dict = self.api.call()

        if response_dict and 'responses' in response_dict:
            if 'ENCOUNTER' in response_dict['responses']:
                if 'status' in response_dict['responses']['ENCOUNTER']:
                    if response_dict['responses']['ENCOUNTER']['status'] is 1:
                        cp=0
                        if 'wild_pokemon' in response_dict['responses']['ENCOUNTER']:
                            pokemon=response_dict['responses']['ENCOUNTER']['wild_pokemon']
                            if 'pokemon_data' in pokemon and 'cp' in pokemon['pokemon_data']:
                                cp=pokemon['pokemon_data']['cp']
                                pokemon_num=int(pokemon['pokemon_data']['pokemon_id'])-1
                                pokemon_name=self.pokemon_list[int(pokemon_num)]['Name']
                                print_yellow('[#] A Wild {} appeared! [CP {}]'.format(pokemon_name, cp))
                                #Simulate app
                                sleep(3)

                        balls_stock = self.bot.pokeball_inventory();
                        while(True):
                            pokeball = 0
                            for pokeball_type, pokeball_count in balls_stock.iteritems():
                                # Masterball
                                if pokeball_type == 4:
                                    break

                                if pokeball_count > 0:
                                    pokeball = pokeball_type
                                    balls_stock[pokeball_type] = balls_stock[pokeball_type] - 1
                                    break

                            if pokeball is 0:
                                print_red('[x] Out of pokeballs...')
                                # TODO: Begin searching for pokestops.
                                break
                            print('[x] Using {}...'.format(self.item_list[str(pokeball)]))
                            id_list1 = self.count_pokemon_inventory()
                            self.api.catch_pokemon(encounter_id = encounter_id,
                                pokeball = pokeball,
                                normalized_reticle_size = 1.950,
                                spawn_point_guid = spawnpoint_id,
                                hit_pokemon = 1,
                                spin_modifier = 1,
                                NormalizedHitPosition = 1)
                            response_dict = self.api.call()

                            if response_dict and \
                                'responses' in response_dict and \
                                'CATCH_POKEMON' in response_dict['responses'] and \
                                'status' in response_dict['responses']['CATCH_POKEMON']:
                                status = response_dict['responses']['CATCH_POKEMON']['status']
                                if status is 2:
                                    print_red('[-] Attempted to capture {} - failed.. trying again!'.format(pokemon_name))
                                    sleep(2)
                                    continue
                                if status is 3:
                                    print_red('[x] Oh no! {} vanished! :('.format(pokemon_name))
                                if status is 1:
                                    if cp < self.config.cp:
                                        print_green('[x] Captured {}! [CP {}]'.format(pokemon_name, cp))
                                        # Transfering Pokemon
                                        self.count_pokemon_inventory()
                                    else:
                                        print_green('[x] Captured {}! [CP {}]'.format(pokemon_name, cp))
                            break
        time.sleep(5)

    def _transfer_low_cp_pokemon(self, value):
        self.api.get_inventory()
        response_dict = self.api.call()
        self._transfer_all_low_cp_pokemon(value, response_dict)

    def _transfer_all_low_cp_pokemon(self, value, response_dict):
        try:
            reduce(dict.__getitem__, ["responses", "GET_INVENTORY", "inventory_delta", "inventory_items"], response_dict)
        except KeyError:
            pass
        else:
            for item in response_dict['responses']['GET_INVENTORY']['inventory_delta']['inventory_items']:
                try:
                    reduce(dict.__getitem__, ["inventory_item_data", "pokemon"], item)
                except KeyError:
                    pass
                else:
                    pokemon = item['inventory_item_data']['pokemon']
                    self._execute_pokemon_transfer(value, pokemon)
                    time.sleep(1.2)

    def _execute_pokemon_transfer(self, value, pokemon):
        if 'cp' in pokemon and pokemon['cp'] < value:
            self.api.release_pokemon(pokemon_id=pokemon['id'])
            response_dict = self.api.call()

    def transfer_pokemon(self, uid):
        self.api.release_pokemon(pokemon_id=uid)
        response_dict = self.api.call()
        print_green('[#] Exchanged Successfully for candy!')

    def count_pokemon_inventory(self):
        self.api.get_inventory()
        response_dict = self.api.call()
        poke_list = []
        poke_dict = {}
        self.counting_pokemon(response_dict, poke_list, poke_dict)

    def counting_pokemon(self, response_dict, poke_list, poke_dict):
        try:
            reduce(dict.__getitem__, ["responses", "GET_INVENTORY", "inventory_delta", "inventory_items"], response_dict)
        except KeyError:
            pass
        else:
            for item in response_dict['responses']['GET_INVENTORY']['inventory_delta']['inventory_items']:
                try:
                    reduce(dict.__getitem__, ["inventory_item_data"], item)
                except KeyError:
                    pass
                else:
                    if 'pokemon_data' in item['inventory_item_data']:
                        pokemon = item['inventory_item_data']['pokemon_data']
                        if 'pokemon_id' in pokemon:
                            pid = pokemon['pokemon_id']
                            uid = pokemon['id']
                            cp = pokemon['cp']
                            poke_info = (pid,uid,cp)
                            poke_list.append(poke_info)

        sorted_poke = defaultdict(list)
        for pid,uid,cp in poke_list:
            item = {'uid': uid, 'cp': cp}
            sorted_poke[pid].append(item)

        count = 0
        sorted_poke = sorted(sorted_poke.items(), key=itemgetter(0))
        for pokemon in sorted_poke:
            pokemon[1].sort(key=itemgetter('cp'), reverse=True)
            if len(pokemon[1]) > 1 :
                remove_list = pokemon[1][1:]
                for pokemons in remove_list:
                    if pokemons['cp'] < self.config.cp:
                        print_yellow('[#] {} pokemon transfered!'.format(count))
                        pid = pokemon[0]
                        uid = pokemons['uid']
                        pokemon_name=self.pokemon_list[int(pid)]['Name']
                        print_green('[#] {} having a CP of {} is going to be exchange for candy!'.format(pokemon_name, pokemons['cp']))
                        count += 1
                        self.transfer_pokemon(uid)

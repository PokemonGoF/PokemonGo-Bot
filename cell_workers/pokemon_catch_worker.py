import time
from sets import Set

class PokemonCatchWorker(object):

    def __init__(self, pokemon, bot):
        self.pokemon = pokemon
        self.api = bot.api
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
                                print('[#] A Wild ' + str(pokemon_name) + ' appeared! [CP' + str(cp) + ']')
                        while(True):
                            id_list1 = self.count_pokemon_inventory()
                            pokeball = 0
                            for i in range(3):
                                for item in self.inventory:
                                    if item['item'] is not i:
                                        continue
                                    if item['count'] is 0:
                                        continue
                                    pokeball = i
                                    item['count'] -= 1
                                    break
                            if pokeball is 0:
                                print('[x] Out of pokeballs...')
                                # TODO: Begin searching for pokestops.
                                break
                            print('[x] Using ' + self.item_list[str(pokeball)] + '...')
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
                                    print('[-] Attempted to capture ' + str(pokemon_name) + ' - failed.. trying again!')
                                    time.sleep(1.25)
                                    continue
                                if status is 3:
                                    print('[x] Oh no! ' + str(pokemon_name) + ' vanished! :(')
                                if status is 1:
                                    if cp < self.config.cp:
                                        print('[x] Captured ' + str(pokemon_name) + '! [CP' + str(cp) + '] - exchanging for candy')
                                        self._transfer_low_cp_pokemon(self.config.cp)
                                        id_list2 = self.count_pokemon_inventory()
                                        self.transfer_pokemon(list(Set(id_list2) - Set(id_list1))[0])
                                    else:
                                        print('[x] Captured ' + str(pokemon_name) + '! [CP' + str(cp) + ']')
                            break
        time.sleep(5)

    def _transfer_low_cp_pokemon(self, value):
    	self.api.get_inventory()
    	response_dict = self.api.call()
    	self._transfer_all_low_cp_pokemon(value, response_dict)

    def _transfer_all_low_cp_pokemon(self, value, response_dict):
    	if 'responses' in response_dict:
    		if 'GET_INVENTORY' in response_dict['responses']:
    			if 'inventory_delta' in response_dict['responses']['GET_INVENTORY']:
    				if 'inventory_items' in response_dict['responses']['GET_INVENTORY']['inventory_delta']:
    					for item in response_dict['responses']['GET_INVENTORY']['inventory_delta']['inventory_items']:
    						if 'inventory_item_data' in item:
    							if 'pokemon' in item['inventory_item_data']:
    								pokemon = item['inventory_item_data']['pokemon']
    								self._execute_pokemon_transfer(value, pokemon)
    								time.sleep(1.2)

    def _execute_pokemon_transfer(self, value, pokemon):
    	if 'cp' in pokemon and pokemon['cp'] < value:
    		self.api.release_pokemon(pokemon_id=pokemon['id'])
    		response_dict = self.api.call()
    		print('[x] Exchanged successfuly!')

    def transfer_pokemon(self, pid):
        self.api.release_pokemon(pokemon_id=pid)
        response_dict = self.api.call()
        print('[x] Exchanged successfuly!')

    def count_pokemon_inventory(self):
        self.api.get_inventory()
        response_dict = self.api.call()
        id_list = []
        return self.counting_pokemon(response_dict, id_list)

    def counting_pokemon(self, response_dict, id_list):
        if 'responses' in response_dict:
            if 'GET_INVENTORY' in response_dict['responses']:
                if 'inventory_delta' in response_dict['responses']['GET_INVENTORY']:
                    if 'inventory_items' in response_dict['responses']['GET_INVENTORY']['inventory_delta']:
                        for item in response_dict['responses']['GET_INVENTORY']['inventory_delta']['inventory_items']:
                            if 'inventory_item_data' in item:
                                if 'pokemon' in item['inventory_item_data']:
                                    pokemon = item['inventory_item_data']['pokemon']
                                    id_list.append(pokemon['id'])
        return id_list

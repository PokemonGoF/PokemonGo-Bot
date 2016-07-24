from utils import distance, format_dist
from pokemongo_bot.human_behaviour import sleep
from pokemongo_bot import logger
from sets import Set

class EvolveAllWorker(object):
    def __init__(self, bot):
        self.api = bot.api
        self.config = bot.config
        self.bot = bot
        # self.position = bot.position

    def work(self):
        self.api.get_inventory()
        response_dict = self.api.call()
        cache = {}

        try:
            reduce(dict.__getitem__, [
                   "responses", "GET_INVENTORY", "inventory_delta", "inventory_items"], response_dict)
        except KeyError:
            pass
        else:
            evolve_list = self._sort_by_cp(response_dict['responses']['GET_INVENTORY']['inventory_delta']['inventory_items'])
            if self.config.evolve_all[0] != 'all':
                # filter out non-listed pokemons
                evolve_list = [x for x in evolve_list if str(x[1]) in self.config.evolve_all]
            
            ## enable to limit number of pokemons to evolve. Useful for testing.
            # nn = 1
            # if len(evolve_list) > nn:
            #     evolve_list = evolve_list[:nn]
            ##

            id_list1 = self.count_pokemon_inventory()
            for pokemon in evolve_list:
                try:
                    self._execute_pokemon_evolve(pokemon, cache)
                except:
                    pass
            id_list2 = self.count_pokemon_inventory()
            release_cand_list_ids = list(Set(id_list2) - Set(id_list1))

            if release_cand_list_ids:
                print('[#] Evolved {} pokemons! Checking if any of them needs to be released ...'.format(
                    len(release_cand_list_ids)
                ))
                self._release_evolved(release_cand_list_ids)

    def _release_evolved(self, release_cand_list_ids):
        self.api.get_inventory()
        response_dict = self.api.call()
        cache = {}

        try:
            reduce(dict.__getitem__, [
                   "responses", "GET_INVENTORY", "inventory_delta", "inventory_items"], response_dict)
        except KeyError:
            pass
        else:
            release_cand_list = self._sort_by_cp(response_dict['responses']['GET_INVENTORY']['inventory_delta']['inventory_items'])
            release_cand_list = [x for x in release_cand_list if x[0] in release_cand_list_ids]

            ## at this point release_cand_list contains evolved pokemons data
            for cand in release_cand_list:
                pokemon_id = cand[0]
                pokemon_name = cand[1]
                pokemon_cp = cand[2]
                pokemon_potential = cand[3]

                if self.should_release_pokemon(pokemon_name, pokemon_cp, pokemon_potential):
                    # Transfering Pokemon
                    self.transfer_pokemon(pokemon_id)
                    logger.log(
                        '[#] {} has been exchanged for candy!'.format(pokemon_name), 'green')

    def _sort_by_cp(self, inventory_items):
        pokemons = []
        for item in inventory_items:
            try:
                reduce(dict.__getitem__, [
                       "inventory_item_data", "pokemon_data"], item)
            except KeyError:
                pass
            else:
                try:
                    pokemon = item['inventory_item_data']['pokemon_data']
                    pokemon_num = int(pokemon['pokemon_id']) - 1
                    pokemon_name = self.bot.pokemon_list[int(pokemon_num)]['Name']
                    pokemons.append([
                        pokemon['id'],
                        pokemon_name,
                        pokemon['cp'],
                        self._compute_iv(pokemon)
                        ])
                except:
                    pass

        pokemons.sort(key=lambda x: x[2], reverse=True)
        return pokemons

    def _execute_pokemon_evolve(self, pokemon, cache):
        pokemon_id = pokemon[0]
        pokemon_name = pokemon[1]
        pokemon_cp = pokemon[2]

        if pokemon_name in cache:
            return

        self.api.evolve_pokemon(pokemon_id=pokemon_id)
        response_dict = self.api.call()
        status = response_dict['responses']['EVOLVE_POKEMON']['result']
        if status == 1:
            print('[#] Successfully evolved {} with {} cp!'.format(
                pokemon_name, pokemon_cp
            ))
        else:
            # cache pokemons we can't evolve. Less server calls
            cache[pokemon_name] = 1
        sleep(5.7)

    # TODO: move to utils. These methods are shared with other workers.
    def transfer_pokemon(self, pid):
        self.api.release_pokemon(pokemon_id=pid)
        response_dict = self.api.call()

    def count_pokemon_inventory(self):
        self.api.get_inventory()
        response_dict = self.api.call()
        id_list = []
        return self.counting_pokemon(response_dict, id_list)

    def counting_pokemon(self, response_dict, id_list):
        try:
            reduce(dict.__getitem__, [
                   "responses", "GET_INVENTORY", "inventory_delta", "inventory_items"], response_dict)
        except KeyError:
            pass
        else:
            for item in response_dict['responses']['GET_INVENTORY']['inventory_delta']['inventory_items']:
                try:
                    reduce(dict.__getitem__, [
                           "inventory_item_data", "pokemon_data"], item)
                except KeyError:
                    pass
                else:
                    pokemon = item['inventory_item_data']['pokemon_data']
                    if pokemon.get('is_egg', False):
                        continue
                    id_list.append(pokemon['id'])

        return id_list

    def should_release_pokemon(self, pokemon_name, cp, iv):
        if self._check_always_capture_exception_for(pokemon_name):
            return False
        else:
            release_config = self._get_release_config_for(pokemon_name)
            cp_iv_logic = release_config.get('cp_iv_logic')
            if not cp_iv_logic:
                cp_iv_logic = self._get_release_config_for('any').get('cp_iv_logic', 'and')

            release_results = {
                'cp':               False,
                'iv':               False,
            }

            if 'release_under_cp' in release_config:
                min_cp = release_config['release_under_cp']
                if cp < min_cp:
                    release_results['cp'] = True

            if 'release_under_iv' in release_config:
                min_iv = release_config['release_under_iv']
                if iv < min_iv:
                    release_results['iv'] = True

            if release_config.get('always_release'):
                return True

            logic_to_function = {
                'or': lambda x, y: x or y,
                'and': lambda x, y: x and y
            }

            #logger.log(
            #    "[x] Release config for {}: CP {} {} IV {}".format(
            #        pokemon_name,
            #        min_cp,
            #        cp_iv_logic,
            #        min_iv
            #    ), 'yellow'
            #)

            return logic_to_function[cp_iv_logic](*release_results.values())

    def _get_release_config_for(self, pokemon):
        release_config = self.config.release_config.get(pokemon)
        if not release_config:
            release_config = self.config.release_config['any']
        return release_config

    def _get_exceptions(self):
        exceptions = self.config.release_config.get('exceptions')
        if not exceptions:
            return None
        return exceptions

    def _get_always_capture_list(self):
        exceptions = self._get_exceptions()
        if not exceptions:
            return []
        always_capture_list = exceptions['always_capture']
        if not always_capture_list:
            return []
        return always_capture_list

    def _check_always_capture_exception_for(self, pokemon_name):
        always_capture_list = self._get_always_capture_list()
        if not always_capture_list:
            return False
        else:
            for pokemon in always_capture_list:
                if pokemon_name == str(pokemon):
                    return True
        return False

    # TODO: should also go to util and refactor in catch worker
    def _compute_iv(self, pokemon):
        total_IV = 0.0
        iv_stats = ['individual_attack', 'individual_defense', 'individual_stamina']
        
        for individual_stat in iv_stats:
            try:
                total_IV += pokemon[individual_stat]
            except:
                pokemon[individual_stat] = 0
                continue
        pokemon_potential = round((total_IV / 45.0), 2)
        return pokemon_potential

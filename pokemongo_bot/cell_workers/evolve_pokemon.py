from pokemongo_bot import logger
from pokemongo_bot.human_behaviour import sleep
from pokemongo_bot.item_list import Item
from pokemongo_bot.cell_workers.base_task import BaseTask

class EvolvePokemon(BaseTask):
    def initialize(self):
        self.api = self.bot.api
        self.evolve_all = self.config.get('evolve_all', [])
        self.evolve_speed = self.config.get('evolve_speed', 3.7)
        self.first_evolve_by = self.config.get('first_evolve_by', 'cp')
        self.evolve_above_cp = self.config.get('evolve_above_cp', 500)
        self.evolve_above_iv = self.config.get('evolve_above_iv', 0.8)
        self.evolve_num_min = self.config.get('evolve_num_min', 5)
        self.cp_iv_logic = self.config.get('logic', 'or')
        self.use_lucky_egg = self.config.get('use_lucky_egg', False)
        self._validate_config()

    def _validate_config(self):
        if isinstance(self.evolve_all, basestring):
            self.evolve_all = [str(pokemon_name) for pokemon_name in self.evolve_all.split(',')]

    def work(self):
        if not self._should_run():
            return

        response_dict = self.api.get_inventory()
        cache = set()
        try:
            reduce(dict.__getitem__, [
                "responses", "GET_INVENTORY", "inventory_delta", "inventory_items"], response_dict)
        except KeyError:
            pass
        else:
            inventory_items = response_dict['responses']['GET_INVENTORY']['inventory_delta']['inventory_items']
            candy_data = self._get_candy_data(inventory_items)
            evolve_list = self._sort_and_filter(inventory_items)

            # filter out non-listed pokemons, top-tier pokemons and those with not enough candy
            evolve_list = [x for x in evolve_list if self._is_evolvable(x, candy_data)]

            # Don't evolve unless the evolvable candidates number is no less than evolve_num_min
            if len(evolve_list) < self.evolve_num_min:
                # logger.log('Evolvable candidates number is {}, which is less than {}... skipping evolve.'.format(
                #     len(evolve_list), self.evolve_num_min),
                #     'green')
                return

            if self.use_lucky_egg:
                lucky_egg_count = self.bot.item_inventory_count(Item.ITEM_LUCKY_EGG.value)
                # Sometimes remaining lucky egg count get changed, check again for sure
                if lucky_egg_count <= 0:
                    logger.log('No lucky eggs... skipping evolve!', 'yellow')
                    return

                logger.log('Using lucky egg ... you have {}'.format(lucky_egg_count))
                response_dict_lucky_egg = self.bot.use_lucky_egg()
                if response_dict_lucky_egg and 'responses' in response_dict_lucky_egg and \
                                'USE_ITEM_XP_BOOST' in response_dict_lucky_egg['responses'] and \
                                'result' in response_dict_lucky_egg['responses']['USE_ITEM_XP_BOOST']:
                    result = response_dict_lucky_egg['responses']['USE_ITEM_XP_BOOST']['result']
                    if result is 1:  # Request success
                        logger.log('Successfully used lucky egg... ({} left!)'.format(lucky_egg_count - 1), 'green')
                    else:
                        logger.log('Failed to use lucky egg!', 'red')
                        return

            evolved = 0
            for pokemon in evolve_list:
                try:
                    if self._execute_pokemon_evolve(pokemon, cache):
                        evolved += 1
                except Exception:
                    pass
            if evolved > 0:
                logger.log('Evolved {} pokemon!'.format(evolved))

    def _should_run(self):
        # Don't run after the first tick
        # Lucky Egg should only be popped at the first tick
        if not self.evolve_all or self.evolve_all[0] == 'none' or self.bot.tick_count is 1:
            return False

        # Will skip evolving if user wants to use an egg and there is none
        lucky_egg_count = self.bot.item_inventory_count(Item.ITEM_LUCKY_EGG.value)
        if self.use_lucky_egg and lucky_egg_count <= 0:
            logger.log('No lucky eggs... skipping evolve!', 'yellow')
            return False

        # Otherwise try evolving
        return True

    def _get_candy_data(self, inventory_items):
        candies = {}
        for item in inventory_items:
            try:
                candy = item['inventory_item_data']['candy']
                candies[candy['family_id']] = candy['candy']
            except KeyError:
                pass
        return candies

    def _sort_and_filter(self, inventory_items):
        pokemons = []
        logic_to_function = {
            'or': lambda pokemon: pokemon["cp"] >= self.evolve_above_cp or pokemon["iv"] >= self.evolve_above_iv,
            'and': lambda pokemon: pokemon["cp"] >= self.evolve_above_cp and pokemon["iv"] >= self.evolve_above_iv
        }
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
                    pokemon = {
                        'id': pokemon['id'],
                        'name': pokemon_name,
                        'cp': pokemon.get('cp', 0),
                        'iv': self._compute_iv(pokemon),
                        'pokemon_id': pokemon['pokemon_id'],
                    }
                    if logic_to_function[self.cp_iv_logic](pokemon):
                        pokemons.append(pokemon)
                except Exception:
                    pass

        if self.first_evolve_by == "cp":
            pokemons.sort(key=lambda x: (x["cp"], x["iv"]), reverse=True)
        else:
            pokemons.sort(key=lambda x: (x["iv"], x["cp"]), reverse=True)

        return pokemons

    def _is_evolvable(self, pokemon, candy_data):
        pokemon_name = pokemon['name']
        # python list is index 0 based, thus - 1
        pokemon_idx = int(pokemon['pokemon_id']) - 1
        # Non-evolvable or top-tier pokemon
        if 'Next Evolution Requirements' not in self.bot.pokemon_list[pokemon_idx]:
            return False

        # filter out non-listed pokemen
        if self.evolve_all[0] != 'all' and pokemon_name not in self.evolve_all:
            return False

        # filter out those with not enough candy
        family_id = pokemon['pokemon_id']
        if 'Previous evolution(s)' in self.bot.pokemon_list[pokemon_idx]:
            family_id = int(self.bot.pokemon_list[pokemon_idx]['Previous evolution(s)'][0]['Number'])

        need_candies = int(self.bot.pokemon_list[pokemon_idx]['Next Evolution Requirements']['Amount'])
        # print('{} needs {} {} candies to evolve, currently we have {}'.
        #       format(pokemon_name, need_candies,
        #              self.bot.pokemon_list[int(family_id) - 1]['Name'],
        #              candy_data[family_id]))
        if candy_data[family_id] >= need_candies:
            candy_data[family_id] -= need_candies
            return True
        return False


    def _execute_pokemon_evolve(self, pokemon, cache):
        pokemon_id = pokemon['id']
        pokemon_name = pokemon['name']
        pokemon_cp = pokemon['cp']
        pokemon_iv = pokemon['iv']

        if pokemon_name in cache:
            return False

        self.bot.api.evolve_pokemon(pokemon_id=pokemon_id)
        response_dict = self.bot.api.call()
        status = response_dict.get('responses', {}).get('EVOLVE_POKEMON', {}).get('result', 0)
        if status == 1:
            logger.log('[#] Successfully evolved {} with {} CP and {} IV!'.format(
                pokemon_name, pokemon_cp, pokemon_iv
            ))
            sleep(self.evolve_speed)
            return True

        else:
            # cache pokemons we can't evolve. Less server calls
            cache.add(pokemon_name)
            sleep(0.7)
            return False

    def _compute_iv(self, pokemon):
        total_iv = pokemon.get("individual_attack", 0) + pokemon.get("individual_stamina", 0) + pokemon.get(
            "individual_defense", 0)
        return round((total_iv / 45.0), 2)

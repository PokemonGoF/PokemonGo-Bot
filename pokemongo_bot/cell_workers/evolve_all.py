from pokemongo_bot import logger
from pokemongo_bot.human_behaviour import sleep
from pokemongo_bot.item_list import Item
from pokemongo_bot.cell_workers.base_task import BaseTask

class EvolveAll(BaseTask):
    def initialize(self):
        self.evolve_all = self.config.get('evolve_all', [])
        self.evolve_speed = self.config.get('evolve_speed', 3.7)
        self.order_by = self.config.get('order_by', 'cp')
        self.evolve_cp_min = self.config.get('evolve_cp_min', 300)
        self.evolve_iv_min = self.config.get('evolve_iv_min', 0.8)
        self.use_lucky_egg = self.config.get('use_lucky_egg', False)
        self._validate_config()

    def _validate_config(self):
        if isinstance(self.evolve_all, basestring):
            self.evolve_all = [str(pokemon_name) for pokemon_name in self.evolve_all.split(',')]

    def work(self):
        if not self._should_run():
            return

        response_dict = self.bot.get_inventory()
        inventory_items = response_dict.get('responses', {}).get('GET_INVENTORY', {}).get('inventory_delta', {}).get(
            'inventory_items', {})

        evolve_list = self._sort_and_filter(inventory_items)

        if self.evolve_all[0] != 'all':
            # filter out non-listed pokemons
            evolve_list = filter(lambda x: x["name"] in self.evolve_all, evolve_list)

        cache = {}
        candy_list = self._get_candy_list(inventory_items)
        id_list1 = self._pokemon_ids_list()
        for pokemon in evolve_list:
            if self._can_evolve(pokemon, candy_list, cache):
                self._execute_pokemon_evolve(pokemon, candy_list, cache)

        id_list2 = self._pokemon_ids_list()
        release_cand_list_ids = list(set(id_list2) - set(id_list1))

        if release_cand_list_ids:
            logger.log('Evolved {} pokemon!'.format(len(release_cand_list_ids)))

    def _should_run(self):
        if not self.evolve_all or self.evolve_all[0] == 'none':
            return False

        # Evolve all is used - Use Lucky egg only at the first tick
        if self.bot.tick_count is not 1 or not self.use_lucky_egg:
            return True

        lucky_egg_count = self.bot.item_inventory_count(Item.ITEM_LUCKY_EGG.value)

        # Make sure the user has a lucky egg and skip if not
        if lucky_egg_count > 0:
            logger.log('Using lucky egg ... you have {}'.format(lucky_egg_count))
            response_dict_lucky_egg = self.bot.use_lucky_egg()
            if response_dict_lucky_egg:
                result = response_dict_lucky_egg.get('responses', {}).get('USE_ITEM_XP_BOOST', {}).get('result', 0)
                if result is 1:  # Request success
                    logger.log('Successfully used lucky egg... ({} left!)'.format(lucky_egg_count - 1), 'green')
                    return True
                else:
                    logger.log('Failed to use lucky egg!', 'red')
                    return False
        else:
            # Skipping evolve so they aren't wasted
            logger.log('No lucky eggs... skipping evolve!', 'yellow')
            return False

    def _get_candy_list(self, inventory_items):
        candies = {}
        for item in inventory_items:
            candy = item.get('inventory_item_data', {}).get('candy', {})
            family_id = candy.get('family_id', 0)
            amount = candy.get('candy', 0)
            if family_id > 0 and amount > 0:
                family = self.bot.pokemon_list[family_id - 1]['Name'] + " candies"
                candies[family] = amount

        return candies

    def _sort_and_filter(self, inventory_items):
        pokemons = []
        for item in inventory_items:
            pokemon = item.get('inventory_item_data', {}).get('pokemon_data', {})
            pokemon_num = int(pokemon.get('pokemon_id', 0)) - 1
            next_evol = self.bot.pokemon_list[pokemon_num].get('Next Evolution Requirements', {})
            pokemons.append({
                'id': pokemon.get('id', 0),
                'num': pokemon_num,
                'name': self.bot.pokemon_list[pokemon_num]['Name'],
                'cp': pokemon.get('cp', 0),
                'iv': self._compute_iv(pokemon),
                'candies_family': next_evol.get('Name', ""),
                'candies_amount': next_evol.get('Amount', 0)
            })

        pokemons = filter(lambda x: x["id"] > 0 and x["cp"] > 0 and x["iv"] > 0 and x["candies_amount"] > 0, pokemons)

        if self.order_by == "cp":
            sort_param_a = "cp"
            sort_param_b = "iv"
            threshold = self.evolve_cp_min
        else:
            sort_param_a = "iv"
            sort_param_b = "cp"
            threshold = self.evolve_iv_min

        pokemons.sort(key=lambda x: (x['num'], 1, x[sort_param_a], x[sort_param_b]) if x[sort_param_a] > threshold
        else (x['num'], 0, x[sort_param_b], x[sort_param_a]), reverse=True)

        return pokemons

    def _can_evolve(self, pokemon, candy_list, cache):

        if pokemon["name"] in cache:
            return False

        family = pokemon["candies_family"]
        amount = pokemon["candies_amount"]
        if family in candy_list and candy_list[family] >= amount:
            return True
        else:
            cache[pokemon["name"]] = 1
            return False

    def _execute_pokemon_evolve(self, pokemon, candy_list, cache):
        pokemon_id = pokemon["id"]
        pokemon_name = pokemon["name"]
        pokemon_cp = pokemon["cp"]
        pokemon_iv = pokemon["iv"]

        if pokemon_name in cache:
            return

        self.bot.api.evolve_pokemon(pokemon_id=pokemon_id)
        response_dict = self.bot.api.call()
        if response_dict.get('responses', {}).get('EVOLVE_POKEMON', {}).get('result', 0) == 1:
            logger.log('Successfully evolved {} with {} CP and {} IV!'.format(pokemon_name, pokemon_cp, pokemon_iv))
            candy_list[pokemon["candies_family"]] -= pokemon["candies_amount"]
            sleep(self.evolve_speed)
        else:
            # cache pokemons we can't evolve. Less server calls
            cache[pokemon_name] = 1
            sleep(0.7)

    def _pokemon_ids_list(self):
        response_dict = self.bot.get_inventory()
        id_list = []
        inventory_items = response_dict.get('responses', {}).get('GET_INVENTORY', {}).get('inventory_delta', {}).get(
            'inventory_items', {})
        for item in inventory_items:
            pokemon = item.get('inventory_item_data', {}).get('pokemon_data', {})
            if pokemon.get('is_egg', False):
                continue
            id_list.append(pokemon.get('id'))

        return id_list

    # TODO: should also go to util and refactor in catch worker
    def _compute_iv(self, pokemon):
        total_iv = pokemon.get("individual_attack", 0) + pokemon.get("individual_stamina", 0) + pokemon.get(
            "individual_defense", 0)
        return round((total_iv / 45.0), 2)

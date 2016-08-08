from pokemongo_bot.human_behaviour import sleep
from pokemongo_bot.item_list import Item
from pokemongo_bot.base_task import BaseTask


class EvolvePokemon(BaseTask):
    SUPPORTED_TASK_API_VERSION = 1

    def initialize(self):
        self.api = self.bot.api
        self.evolve_all = self.config.get('evolve_all', [])
        self.evolve_speed = self.config.get('evolve_speed', 2)
        self.first_evolve_by = self.config.get('first_evolve_by', 'cp')
        self.evolve_above_cp = self.config.get('evolve_above_cp', 500)
        self.evolve_above_iv = self.config.get('evolve_above_iv', 0.8)
        self.cp_iv_logic = self.config.get('logic', 'or')
        self.use_lucky_egg = self.config.get('use_lucky_egg', False)
        self._validate_config()

    def _validate_config(self):
        if isinstance(self.evolve_all, basestring):
            self.evolve_all = [str(pokemon_name).strip() for pokemon_name in self.evolve_all.split(',')]

    def work(self):
        if not self._should_run():
            return

        response_dict = self.api.get_inventory()
        inventory_items = response_dict.get('responses', {}).get('GET_INVENTORY', {}).get('inventory_delta', {}).get(
            'inventory_items', {})

        evolve_list = self._sort_and_filter(inventory_items)

        if self.evolve_all[0] != 'all':
            # filter out non-listed pokemons
            evolve_list = filter(lambda x: x["name"] in self.evolve_all, evolve_list)

        cache = {}
        candy_list = self._get_candy_list(inventory_items)
        for pokemon in evolve_list:
            if self._can_evolve(pokemon, candy_list, cache):
                self._execute_pokemon_evolve(pokemon, candy_list, cache)

    def _should_run(self):
        if not self.evolve_all or self.evolve_all[0] == 'none':
            return False

        # Evolve all is used - Use Lucky egg only at the first tick
        if self.bot.tick_count is not 1 or not self.use_lucky_egg:
            return True

        lucky_egg_count = self.bot.item_inventory_count(Item.ITEM_LUCKY_EGG.value)

        # Make sure the user has a lucky egg and skip if not
        if lucky_egg_count > 0:
            response_dict_lucky_egg = self.bot.use_lucky_egg()
            if response_dict_lucky_egg:
                result = response_dict_lucky_egg.get('responses', {}).get('USE_ITEM_XP_BOOST', {}).get('result', 0)
                if result is 1:  # Request success
                    self.emit_event(
                        'used_lucky_egg',
                        formatted='Used lucky egg ({amount_left} left).',
                        data={
                             'amount_left': lucky_egg_count - 1
                        }
                    )
                    return True
                else:
                    self.emit_event(
                        'lucky_egg_error',
                        level='error',
                        formatted='Failed to use lucky egg!'
                    )
                    return False
        else:
            # Skipping evolve so they aren't wasted
            self.emit_event(
                'skip_evolve',
                formatted='Skipping evolve because has no lucky egg.'
            )
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
        logic_to_function = {
            'or': lambda pokemon: pokemon["cp"] >= self.evolve_above_cp or pokemon["iv"] >= self.evolve_above_iv,
            'and': lambda pokemon: pokemon["cp"] >= self.evolve_above_cp and pokemon["iv"] >= self.evolve_above_iv
        }
        for item in inventory_items:
            pokemon = item.get('inventory_item_data', {}).get('pokemon_data', {})
            pokemon_num = int(pokemon.get('pokemon_id', 0)) - 1
            next_evol = self.bot.pokemon_list[pokemon_num].get('Next Evolution Requirements', {})
            pokemon = {
                'id': pokemon.get('id', 0),
                'num': pokemon_num,
                'name': self.bot.pokemon_list[pokemon_num]['Name'],
                'cp': pokemon.get('cp', 0),
                'iv': self._compute_iv(pokemon),
                'candies_family': next_evol.get('Name', ""),
                'candies_amount': next_evol.get('Amount', 0)
            }
            if pokemon["id"] > 0 and pokemon["candies_amount"] > 0 and (logic_to_function[self.cp_iv_logic](pokemon)):
                pokemons.append(pokemon)

        if self.first_evolve_by == "cp":
            pokemons.sort(key=lambda x: (x['num'], x["cp"], x["iv"]), reverse=True)
        else:
            pokemons.sort(key=lambda x: (x['num'], x["iv"], x["cp"]), reverse=True)

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
            return False

        response_dict = self.api.evolve_pokemon(pokemon_id=pokemon_id)
        if response_dict.get('responses', {}).get('EVOLVE_POKEMON', {}).get('result', 0) == 1:
            self.emit_event(
                'pokemon_evolved',
                formatted="Successfully evolved {pokemon} with CP {cp} and IV {iv}!",
                data={
                    'pokemon': pokemon_name,
                    'iv': pokemon_iv,
                    'cp': pokemon_cp
                }
            )
            candy_list[pokemon["candies_family"]] -= pokemon["candies_amount"]
            sleep(self.evolve_speed)
            return True
        else:
            # cache pokemons we can't evolve. Less server calls
            cache[pokemon_name] = 1
            sleep(0.7)
            return False

    def _compute_iv(self, pokemon):
        total_iv = pokemon.get("individual_attack", 0) + pokemon.get("individual_stamina", 0) + pokemon.get(
            "individual_defense", 0)
        return round((total_iv / 45.0), 2)

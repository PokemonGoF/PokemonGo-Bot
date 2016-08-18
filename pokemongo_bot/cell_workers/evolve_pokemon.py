from pokemongo_bot import inventory
from pokemongo_bot.human_behaviour import sleep
from pokemongo_bot.inventory import Pokemon
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
        self.evolve_num_min = self.config.get('evolve_num_min', 5)
        self.cp_iv_logic = self.config.get('logic', 'or')
        self.use_lucky_egg = self.config.get('use_lucky_egg', False)
        self._validate_config()

    def _validate_config(self):
        if isinstance(self.evolve_all, basestring):
            self.evolve_all = [str(pokemon_name).strip() for pokemon_name in self.evolve_all.split(',')]

    def work(self):
        if not self._should_run():
            return

        cache = set()

        evolve_list = self._sort_and_filter()
        # filter out non-listed pokemons, top-tier pokemons and those with not enough candy
        evolve_list = [x for x in evolve_list if self._is_evolvable(x, inventory.candies().deepcopy())]

        # Don't evolve unless the evolvable candidates number is no less than evolve_num_min
        if len(evolve_list) < self.evolve_num_min:
            return

        if self.use_lucky_egg:
            lucky_egg_count = self.bot.item_inventory_count(Item.ITEM_LUCKY_EGG.value)
            # Sometimes remaining lucky egg count get changed, check again for sure
            if lucky_egg_count <= 0:
                self.emit_event(
                    'skip_evolve',
                    formatted='Skipping evolve because has no lucky egg.'
                )
                return

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
                else:
                    self.emit_event(
                        'lucky_egg_error',
                        level='error',
                        formatted='Failed to use lucky egg!'
                    )
                    return

        for pokemon in evolve_list:
                self._execute_pokemon_evolve(pokemon, cache)

    def _should_run(self):
        # Don't run after the first tick
        # Lucky Egg should only be popped at the first tick
        if not self.evolve_all or self.evolve_all[0] == 'none' or self.bot.tick_count is 1:
            return False

        # Will skip evolving if user wants to use an egg and there is none
        lucky_egg_count = self.bot.item_inventory_count(Item.ITEM_LUCKY_EGG.value)
        if self.use_lucky_egg and lucky_egg_count <= 0:
            self.emit_event(
                'skip_evolve',
                formatted='Skipping evolve because has no lucky egg.'
            )

            return False

        # Otherwise try evolving
        return True

    def _sort_and_filter(self):
        pokemons = []
        logic_to_function = {
            'or': lambda pokemon: pokemon.cp >= self.evolve_above_cp or pokemon.iv >= self.evolve_above_iv,
            'and': lambda pokemon: pokemon.cp >= self.evolve_above_cp and pokemon.iv >= self.evolve_above_iv
        }
        for pokemon in inventory.pokemons().all():
            if pokemon.id > 0 and pokemon.has_next_evolution() and (logic_to_function[self.cp_iv_logic](pokemon)):
                pokemons.append(pokemon)

        if self.first_evolve_by == "cp":
            pokemons.sort(key=lambda x: (x.pokemon_id, x.cp, x.iv), reverse=True)
        else:
            pokemons.sort(key=lambda x: (x.pokemon_id, x.iv, x.cp), reverse=True)

        return pokemons


    def _is_evolvable(self, pokemon, candies):
        # filter out non-listed pokemen
        if self.evolve_all[0] != 'all' and pokemon.name not in self.evolve_all:
            return False

        if not pokemon.has_seen_next_evolution():
            return False

        if candies.get(pokemon.pokemon_id).quantity >= pokemon.evolution_cost:
            candies.get(pokemon.pokemon_id).consume(pokemon.evolution_cost)
            return True
        # not enough candies
        return False


    def _execute_pokemon_evolve(self, pokemon, cache):
        if pokemon.name in cache:
            return False

        response_dict = self.api.evolve_pokemon(pokemon_id=pokemon.id)
        if response_dict.get('responses', {}).get('EVOLVE_POKEMON', {}).get('result', 0) == 1:
            self.emit_event(
                'pokemon_evolved',
                formatted="Successfully evolved {pokemon} with CP {cp} and IV {iv}!",
                data={
                    'pokemon': pokemon.name,
                    'iv': pokemon.iv,
                    'cp': pokemon.cp,
                    'ncp': '?',
                    'dps': '?',
                    'xp': '?'
                }
            )
            awarded_candies = response_dict.get('responses', {}).get('EVOLVE_POKEMON', {}).get('candy_awarded', 0)
            inventory.candies().get(pokemon.pokemon_id).consume(pokemon.evolution_cost - awarded_candies)
            inventory.pokemons().remove(pokemon.id)
            pokemon = Pokemon(response_dict.get('responses', {}).get('EVOLVE_POKEMON', {}).get('evolved_pokemon_data', {}))
            inventory.pokemons().add(pokemon)

            sleep(self.evolve_speed)
            return True
        else:
            # cache pokemons we can't evolve. Less server calls
            cache.add(pokemon.name)
            sleep(0.7)
            return False

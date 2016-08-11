from pokemongo_bot import inventory
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

        evolve_list = self._sort_and_filter()

        if self.evolve_all[0] != 'all':
            # filter out non-listed pokemons
            evolve_list = filter(lambda x: x.name in self.evolve_all, evolve_list)

        cache = {}
        for pokemon in evolve_list:
            if pokemon.can_evolve_now():
                self._execute_pokemon_evolve(pokemon, cache)

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
                    'cp': pokemon.cp
                }
            )
            inventory.candies().get(pokemon.pokemon_id).consume(pokemon.evolution_cost)
            sleep(self.evolve_speed)
            return True
        else:
            # cache pokemons we can't evolve. Less server calls
            cache[pokemon.name] = 1
            sleep(0.7)
            return False

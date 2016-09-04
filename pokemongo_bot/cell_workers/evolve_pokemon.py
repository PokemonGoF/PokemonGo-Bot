from random import uniform

from pokemongo_bot import inventory
from pokemongo_bot.human_behaviour import sleep
from pokemongo_bot.inventory import Pokemon
from pokemongo_bot.item_list import Item
from pokemongo_bot.base_task import BaseTask


class EvolvePokemon(BaseTask):
    SUPPORTED_TASK_API_VERSION = 1
    def __init__(self, bot, config):
        super(EvolvePokemon, self).__init__(bot, config)

    def initialize(self):
        self.api = self.bot.api
        self.evolve_list = self.config.get('evolve_list', [])
        self.donot_evolve_list = self.config.get('donot_evolve_list', [])
        self.min_evolve_speed = self.config.get('min_evolve_speed', 25)
        self.max_evolve_speed = self.config.get('max_evolve_speed', 30)
        self.first_evolve_by = self.config.get('first_evolve_by', 'cp')
        self.evolve_above_cp = self.config.get('evolve_above_cp', 500)
        self.evolve_above_iv = self.config.get('evolve_above_iv', 0.8)
        self.cp_iv_logic = self.config.get('logic', 'or')
        self.use_lucky_egg = self.config.get('use_lucky_egg', False)
        self._validate_config()

    def _validate_config(self):
        if isinstance(self.evolve_list, basestring):
            self.evolve_list = [str(pokemon_name).strip().lower() for pokemon_name in self.evolve_list.split(',')]
            
        if isinstance(self.donot_evolve_list, basestring):
            self.donot_evolve_list = [str(pokemon_name).strip().lower() for pokemon_name in self.donot_evolve_list.split(',')]

        if 'evolve_speed' in self.config:
            self.logger.warning("evolve_speed is deprecated, instead please use 'min_evolve_speed' and 'max_evolved_speed'.")

        if 'evolve_all' in self.config:
            self.logger.warning("evolve_all is deprecated, instead please use 'evolve_list' and 'donot_evolve_list'.")

    def work(self):
        if not self._should_run():
            return

        filtered_list = self._sort_and_filter()

        if (len(self.evolve_list) > 0) and self.evolve_list[0] != 'all':
            filtered_list = filter(lambda x: x.name.lower() in self.evolve_list, filtered_list)

        if (len(self.donot_evolve_list) > 0) and self.donot_evolve_list[0] != 'none':
            filtered_list = filter(lambda pokemon: pokemon.name.lower() not in self.donot_evolve_list, filtered_list)

        cache = {}
        for pokemon in filtered_list:
            if pokemon.can_evolve_now():
                self._execute_pokemon_evolve(pokemon, cache)

    def _should_run(self):
        if not self.evolve_list or self.evolve_list[0] == 'none':
            return False

        # Evolve all is used - Use Lucky egg only at the first tick
        if self.bot.tick_count is not 1 or not self.use_lucky_egg:
            return True

        lucky_egg = inventory.items().get(Item.ITEM_LUCKY_EGG.value)

        # Make sure the user has a lucky egg and skip if not
        if lucky_egg.count > 0:
            response_dict_lucky_egg = self.bot.use_lucky_egg()
            if response_dict_lucky_egg:
                result = response_dict_lucky_egg.get('responses', {}).get('USE_ITEM_XP_BOOST', {}).get('result', 0)
                if result is 1:  # Request success
                    lucky_egg.remove(1)
                    self.emit_event(
                        'used_lucky_egg',
                        formatted='Used lucky egg ({amount_left} left).',
                        data={
                             'amount_left': lucky_egg.count
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
            if pokemon.unique_id > 0 and pokemon.has_next_evolution() and (logic_to_function[self.cp_iv_logic](pokemon)):
                pokemons.append(pokemon)

        if self.first_evolve_by == "cp":
            pokemons.sort(key=lambda x: (x.pokemon_id, x.cp, x.iv), reverse=True)
        else:
            pokemons.sort(key=lambda x: (x.pokemon_id, x.iv, x.cp), reverse=True)

        return pokemons

    def _execute_pokemon_evolve(self, pokemon, cache):
        if pokemon.name in cache:
            return False

        response_dict = self.api.evolve_pokemon(pokemon_id=pokemon.unique_id)
        if response_dict.get('responses', {}).get('EVOLVE_POKEMON', {}).get('result', 0) == 1:
            xp = response_dict.get("responses", {}).get("EVOLVE_POKEMON", {}).get("experience_awarded", 0)
            evolution = response_dict.get("responses", {}).get("EVOLVE_POKEMON", {}).get("evolved_pokemon_data", {})
            awarded_candies = response_dict.get('responses', {}).get('EVOLVE_POKEMON', {}).get('candy_awarded', 0)
            candy = inventory.candies().get(pokemon.pokemon_id)

            candy.consume(pokemon.evolution_cost - awarded_candies)

            self.emit_event(
                'pokemon_evolved',
                formatted="Evolved {pokemon} [IV {iv}] [CP {cp}] [{candy} candies] [+{xp} xp]",
                data={
                    'pokemon': pokemon.name,
                    'iv': pokemon.iv,
                    'cp': pokemon.cp,
                    'candy': candy.quantity,
                    'xp': xp,
                }
            )

            inventory.pokemons().remove(pokemon.unique_id)
            new_pokemon = inventory.Pokemon(evolution)
            inventory.pokemons().add(new_pokemon)
            inventory.player().exp += xp

            sleep(uniform(self.min_evolve_speed, self.max_evolve_speed))
            evolve_result = True
        else:
            # cache pokemons we can't evolve. Less server calls
            cache[pokemon.name] = 1
            sleep(0.7)
            evolve_result = False

        with self.bot.database as conn:
            c = conn.cursor()
            c.execute("SELECT COUNT(name) FROM sqlite_master WHERE type='table' AND name='evolve_log'")

        result = c.fetchone()

        while True:
            if result[0] == 1:
                conn.execute('''INSERT INTO evolve_log (pokemon, iv, cp) VALUES (?, ?, ?)''', (pokemon.name, pokemon.iv, pokemon.cp))
                break
            else:
                self.emit_event(
                    'evolve_log',
                    sender=self,
                    level='info',
                    formatted="evolve_log table not found, skipping log"
                )
                break

        return evolve_result

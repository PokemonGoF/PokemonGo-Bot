
from pokemongo_bot import inventory
from pokemongo_bot.human_behaviour import sleep, action_delay
from pokemongo_bot.inventory import Pokemon
from pokemongo_bot.item_list import Item
from pokemongo_bot.base_task import BaseTask
import time

class Counter(dict):
    def __missing__(self,key):
        return 0

class EvolvePokemon(BaseTask):
    SUPPORTED_TASK_API_VERSION = 1
    def __init__(self, bot, config):
        super(EvolvePokemon, self).__init__(bot, config)

    def initialize(self):
        self.start_time = 0
        self.next_log_update = 0
        self.log_interval = self.config.get('log_interval', 120)
        self.evolve_list = self.config.get('evolve_list', [])
        self.donot_evolve_list = self.config.get('donot_evolve_list', [])
        self.min_evolve_speed = self.config.get('min_evolve_speed', 25)
        self.max_evolve_speed = self.config.get('max_evolve_speed', 30)
        self.first_evolve_by = self.config.get('first_evolve_by', 'cp')
        self.evolve_above_cp = self.config.get('evolve_above_cp', 500)
        self.evolve_above_iv = self.config.get('evolve_above_iv', 0.8)
        self.cp_iv_logic = self.config.get('logic', 'or')
        self.use_lucky_egg = self.config.get('use_lucky_egg', False)
        self.min_pokemon_to_be_evolved = self.config.get('min_pokemon_to_be_evolved', 1)
        self._validate_config()

        self.logic_to_function = {
            'or': lambda pokemon: pokemon.cp >= self.evolve_above_cp or pokemon.iv >= self.evolve_above_iv,
            'and': lambda pokemon: pokemon.cp >= self.evolve_above_cp and pokemon.iv >= self.evolve_above_iv
        }

        self.default_to_evolve = False
        if (len(self.evolve_list) > 0) and self.evolve_list[0] == 'all':
            self.default_to_evolve = True

    def _validate_config(self):
        if isinstance(self.evolve_list, basestring):
            self.evolve_list = [str(pokemon_name).lower().strip() for pokemon_name in self.evolve_list.split(',')]

        if isinstance(self.donot_evolve_list, basestring):
            self.donot_evolve_list = [str(pokemon_name).lower().strip() for pokemon_name in self.donot_evolve_list.split(',')]

        if 'evolve_speed' in self.config:
            self.logger.warning("evolve_speed is deprecated, instead please use 'min_evolve_speed' and 'max_evolved_speed'.")

        if 'evolve_all' in self.config:
            self.logger.warning("evolve_all is deprecated, instead please use 'evolve_list' and 'donot_evolve_list'.")

    def work(self):
        if not self._should_run():
            return

        filtered_list, filtered_dict = self._sort_and_filter()

        pokemon_to_be_evolved = 0
        pokemon_ids = []
        for pokemon in filtered_list:
            if pokemon.pokemon_id not in pokemon_ids:
                pokemon_ids.append(pokemon.pokemon_id)
                candy = inventory.candies().get(pokemon.pokemon_id)
                pokemon_to_be_evolved = pokemon_to_be_evolved + min(candy.quantity / (pokemon.evolution_cost - 1), filtered_dict[pokemon.pokemon_id])

        self._log_update_if_should(pokemon_to_be_evolved, self.min_pokemon_to_be_evolved)

        has_minimum_to_evolve = pokemon_to_be_evolved >= self.min_pokemon_to_be_evolved
        if has_minimum_to_evolve:
            if self.use_lucky_egg:
                self._use_lucky_egg()
            cache = {}
            for pokemon in filtered_list:
                if pokemon.can_evolve_now():
                    self._execute_pokemon_evolve(pokemon, cache)

    def _log_update_if_should(self, has, needs):
        if self._should_log_update():
            self._compute_next_log_update()
            self.emit_event(
                'pokemon_evolve_check',
                formatted='Evolvable: {has}/{needs}',
                data={'has': has, 'needs': needs}
            )

    def _compute_next_log_update(self):
        self.next_log_update = time.time() + self.log_interval

    def _should_log_update(self):
        return time.time() >= self.next_log_update

    def _should_run(self):
        if not self.evolve_list or self.evolve_list[0] == 'none':
            return False
        return True

    def _use_lucky_egg(self):
        using_lucky_egg = time.time() - self.start_time < 1800
        if using_lucky_egg:
            return False

        lucky_egg = inventory.items().get(Item.ITEM_LUCKY_EGG.value)

        # Make sure the user has a lucky egg and skip if not
        if lucky_egg.count > 0:
            response_dict_lucky_egg = self.bot.use_lucky_egg()
            if response_dict_lucky_egg:
                result = response_dict_lucky_egg.get('responses', {}).get('USE_ITEM_XP_BOOST', {}).get('result', 0)
                if result is 1:  # Request success
                    self.start_time = time.time()
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
        pokemon_count = Counter()

        for pokemon in inventory.pokemons().all():
            if self._should_evolve(pokemon):
                pokemons.append(pokemon)
                pokemon_count[pokemon.pokemon_id] += 1

        if self.first_evolve_by == "cp":
            pokemons.sort(key=lambda x: (x.pokemon_id, x.cp, x.iv), reverse=True)
        else:
            pokemons.sort(key=lambda x: (x.pokemon_id, x.iv, x.cp), reverse=True)

        return pokemons, pokemon_count

    def _should_evolve(self,pokemon):
        to_evolve = self.default_to_evolve
        if pokemon.unique_id > 0 and pokemon.has_next_evolution() and (self.logic_to_function[self.cp_iv_logic](pokemon)):
            if (len(self.evolve_list) > 0) and (self.evolve_list[0] == 'all' or pokemon.name.lower() in self.evolve_list):
                to_evolve = True
            if (len(self.donot_evolve_list) > 0) and self.donot_evolve_list[0] != 'none' and pokemon.name.lower() in self.donot_evolve_list:
                to_evolve = False
            return to_evolve
        return False

    def _execute_pokemon_evolve(self, pokemon, cache):
        if pokemon.name in cache:
            return False
        
        request = self.bot.api.create_request()
        request.evolve_pokemon(pokemon_id=pokemon.unique_id)
        response_dict = request.call()
        
        if response_dict.get('responses', {}).get('EVOLVE_POKEMON', {}).get('result', 0) == 1:
            xp = response_dict.get("responses", {}).get("EVOLVE_POKEMON", {}).get("experience_awarded", 0)
            evolution = response_dict.get("responses", {}).get("EVOLVE_POKEMON", {}).get("evolved_pokemon_data", {})
            awarded_candies = response_dict.get('responses', {}).get('EVOLVE_POKEMON', {}).get('candy_awarded', 0)
            candy = inventory.candies().get(pokemon.pokemon_id)

            candy.consume(pokemon.evolution_cost - awarded_candies)

            self.emit_event(
                'pokemon_evolved',
                formatted="*Evolved {}* (IV {}) (CP {}) ({} candies) (+{} xp)".format(pokemon.name, pokemon.iv, pokemon.cp, candy.quantity, xp),
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

            action_delay(self.min_evolve_speed, self.max_evolve_speed)
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

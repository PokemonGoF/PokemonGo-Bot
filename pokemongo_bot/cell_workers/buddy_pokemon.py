from datetime import datetime, timedelta

from pokemongo_bot import inventory
from pokemongo_bot.human_behaviour import action_delay
from pokemongo_bot.base_task import BaseTask
from pokemongo_bot.worker_result import WorkerResult


class BuddyPokemon(BaseTask):
    SUPPORTED_TASK_API_VERSION = 1

    def initialize(self):
        self.buddy = self.bot.player_data.get('buddy_pokemon', {})
        self.buddy_list = self.config.get('buddy_list', 'none')
        self.best_in_family = self.config.get('best_in_family', True)
        self.candy_limit = self.config.get('candy_limit', 0)  # 0 = No Limit
        self.force_first_change = self.config.get('force_first_change', False)
        self.buddy_change_wait_min = self.config.get('buddy_change_wait_min', 3)
        self.buddy_change_wait_max = self.config.get('buddy_change_wait_max', 5)
        self.min_interval = self.config.get('min_interval', 120)
        self.next_update = None
        self.cache = []
        self.candy_awarded = 0
        self.buddy_km_needed = 0
        self._validate_config()
        self._check_old_reward()

    def _validate_config(self):
        if isinstance(self.buddy_list, basestring):
            self.buddy_list = [str(pokemon_name).lower().replace(' ', '')
                               for pokemon_name in self.buddy_list.split(',')]
        if self.buddy_list and self.buddy_list[0] == 'none':
            self.buddy_list = []
        if self.buddy and not self.buddy_list:
            self.emit_event(
                'buddy_keep_active',
                formatted='BuddyPokemon is still active since is not possible'
                          ' to remove Buddy'
            )
        if self.buddy:
            pokemon = self._get_pokemon_by_id(self.buddy['id'])
            self.buddy_km_needed = pokemon.buddy_km_needed

    def work(self):
        if self.buddy_list:
            if self.force_first_change or not self.buddy or self.candy_limit != 0 and self.candy_awarded >= self.candy_limit:
                self.force_first_change = False

                remaining = [name for name in self.buddy_list if name not in self.cache]
                if not remaining:
                    self.cache = []
                    return WorkerResult.SUCCESS

                poke_name = remaining[0]
                self.cache.append(poke_name)

                pokemon = self._get_pokemon_by_name(poke_name)
                if pokemon is None:
                    return WorkerResult.ERROR

                if pokemon.name != self._get_pokemon_by_id(self.buddy['id']).name:
                    self._set_buddy(pokemon)

        if not self.buddy:
            return WorkerResult.SUCCESS

        if self._km_walked() - self.buddy['last_km_awarded'] >= self.buddy_km_needed:
            self.buddy['last_km_awarded'] += self.buddy_km_needed
            print("REWARDING!!! KM Walked: {}".format(self._km_walked()))
            if not self._get_award():
                return WorkerResult.ERROR

        if self._should_print():
            print("KM Walked: {}".format(self._km_walked()))
            self._print_update()
            self._compute_next_update()

        return WorkerResult.SUCCESS

    def _set_buddy(self, pokemon):
        response_dict = \
            self.bot.api.set_buddy_pokemon(pokemon_id=pokemon.unique_id)
        try:
            result = response_dict['responses']['SET_BUDDY_POKEMON']['result']
        except KeyError:
            return False

        action_delay(self.buddy_change_wait_min, self.buddy_change_wait_max)
        if result == 1:
            updated_buddy = response_dict['responses']['SET_BUDDY_POKEMON'
                                                       ]['updated_buddy']
            self.buddy = updated_buddy
            self.candy_awarded = 0
            self.buddy_km_needed = pokemon.buddy_km_needed

            self.emit_event(
                'buddy_update',
                formatted='{name} was set as Buddy Pokemon.',
                data={
                    'name': pokemon.name
                }
            )
            return True
        else:
            error_codes = {
                0: 'UNSET',
                2: 'ERROR_POKEMON_DEPLOYED',
                3: 'ERROR_POKEMON_NOT_OWNED',
                4: 'ERROR_POKEMON_IS_EGG',
            }
            self.emit_event(
                'buddy_update_fail',
                formatted='Error while setting {name} as Buddy Pokemon: {error}',
                data={
                    'name': pokemon.name,
                    'error': error_codes[result]
                }
            )
            return False

    def _get_award(self):
        response_dict = self.bot.api.get_buddy_walked()
        result = response_dict['responses']['GET_BUDDY_WALKED']
        print(response_dict)
        print(result)
        try:
            success = result['success']
            family_id = result.get('family_candy_id', -1)
            candy_earned = result.get('candy_earned_count', -1)
        except KeyError:
            return False

        if success and family_id != -1 and candy_earned != -1:
            self.candy_awarded += candy_earned

            msg = "{candy} {family} candy earned. You now have {quantity} candy!"
            if self.candy_limit != 0 and len(self.buddy_list) > 1:
                msg += " (Candy limit: {candy_earned}/{candy_limit})"
            self.emit_event(
                'buddy_candy_earned',
                formatted=msg,
                data={
                    'candy': candy_earned,
                    'family': inventory.candies().get(family_id).type,
                    'quantity': inventory.candies().get(family_id).quantity + 1,
                    'candy_earned': self.candy_awarded,
                    'candy_limit': self.candy_limit
                }
            )
            return True
        else:
            self.emit_event(
                'buddy_candy_fail',
                formatted='Error trying to get candy from buddy.'
            )
            return False

    def _check_old_reward(self):
        if not self.buddy:
            return
        pokemon = self._get_pokemon_by_id(self.buddy['id'])
        self.buddy_km_needed = pokemon.buddy_km_needed
        km_diff = self._km_walked() - self.buddy['last_km_awarded']
        rewards_size = km_diff // self.buddy_km_needed
        if rewards_size > 0:
            self._get_award()
            self.buddy['last_km_awarded'] += self.buddy_km_needed*rewards_size

    def _km_walked(self):
        inv = inventory.jsonify_inventory()
        km_walked = 0
        for inv_data in inv:
            inv_data = inv_data.get('inventory_item_data', {})
            if 'player_stats' in inv_data:
                km_walked = inv_data.get('player_stats', {}).get('km_walked', 0)
                break
        return km_walked

    def _get_pokemon_by_name(self, name):
        pokemons = inventory.pokemons().all()
        pokemon = None
        for p in pokemons:
            if p.name.lower() == name:
                pokemon = p
                break

        if pokemon is None:
            self.emit_event(
                'buddy_not_available',
                formatted='{name} was not found',
                data={
                    'name': name
                }
            )
            return None

        fam_id = pokemon.family_id
        poke_id = pokemon.pokemon_id
        if self.best_in_family:
            poke_list = [p for p in pokemons if p.family_id == fam_id]
        else:
            poke_list = [p for p in pokemons if p.pokemon_id == poke_id]
        poke_list.sort(key=lambda p: p.cp, reverse=True)
        return poke_list[0]

    def _get_pokemon_by_id(self, unique_id):
        pokemons = inventory.pokemons().all()
        for pokemon in pokemons:
            if pokemon.unique_id == unique_id:
                return pokemon

    def _should_print(self):
        return self.next_update is None or datetime.now() >= self.next_update

    def _compute_next_update(self):
        self.next_update = datetime.now() + timedelta(seconds=self.min_interval)

    def _print_update(self):
        pokemon = self._get_pokemon_by_id(self.buddy['id'])
        self.emit_event(
            'buddy_next_reward',
            formatted='({name}) Buddy next award {km_walked}/{km_total} km',
            data={
                'name': pokemon.name,
                'km_walked': round(self._km_walked() - self.buddy['last_km_awarded'], 2),
                'km_total': round(self.buddy_km_needed, 1)
            }
        )

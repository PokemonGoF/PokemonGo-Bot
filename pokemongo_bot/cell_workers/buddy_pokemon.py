from datetime import datetime, timedelta

from pokemongo_bot import inventory
from pokemongo_bot.human_behaviour import action_delay
from pokemongo_bot.base_task import BaseTask
from pokemongo_bot.worker_result import WorkerResult


class BuddyPokemon(BaseTask):
    """
    Makes use of the Pokemon Buddy system.
    It's able to switch the buddy automatically given an list of pokemon that
        should be using this feature.
    Periodically logs the status of the buddy walking.
    After setting a buddy it's not possible to remove it, only change it.
        So if a buddy is already selected and no buddy list is given, it will
        still run with the buddy already selected.

    Example config:
    {
        "type": "BuddyPokemon",
        "config": {
            "enabled": true,
            "buddy_list": "dratini, magikarp",
            "best_in_family": true,
            "// candy_limit = 0 means no limit, so it will never change current buddy": {},
            "candy_limit": 0,
            "candy_limit_absolute": 0,
            "// force_first_change = true will always change buddy at start removing current one": {},
            "force_first_change": false,
            "buddy_change_wait_min": 3,
            "buddy_change_wait_max": 5,
            "min_interval": 120
        }
    }

    buddy_list: Default: []. List of pokemon names that will be used as buddy.
                             If '[]' or 'none', will not use or change buddy.
    best_in_family: Default: True. If True, picks best Pokemon in the family
                                   (sorted by cp).
    candy_limit: Default: 0. Set the candy limit to be rewarded per buddy, when
                             reaching this limit the bot will change the buddy
                             to the next in the list. When candy_limit = 0 or
                             only one buddy in list, it has no limit and never
                             changes buddy.
    candy_limit_absolute: Default: 0. Set the absolute candy limit to be
                                      rewarded per buddy, when reaching this
                                      limit the bot will change the buddy to the
                                      next in the list. When
                                      candy_limit_absolute = 0 or only one buddy
                                      in list, it has no limit and never changes
                                      buddy. Use this to stop collecting candy
                                      when a candy threshold for your buddy's
                                      pokemon family is reached (e.g. 50 for
                                      evolving).
    force_first_change: Default: False. If True, will try to change buddy at
                        bot start according to the buddy list. If False, will
                        use the buddy already set until candy_limit is reached
                        and then use the buddy list.
    buddy_change_wait_min: Default: 3. Minimum time (in seconds) that the buddy
                                       change takes.
    buddy_change_wait_max: Default: 5. Maximum time (in seconds) that the buddy
                                    change takes.
    min_interval: Default: 120. Time (in seconds) to periodically log the buddy
                                walk status.
    """

    SUPPORTED_TASK_API_VERSION = 1

    def initialize(self):
        self.buddy = self.bot.player_data.get('buddy_pokemon', {})
        self.buddy_list = self.config.get('buddy_list', [])
        self.best_in_family = self.config.get('best_in_family', True)
        self.candy_limit = self.config.get('candy_limit', 0)  # 0 = No Limit
        self.candy_limit_absolute = self.config.get('candy_limit_absolute', 0)  # 0 = No Limit
        self.force_first_change = self.config.get('force_first_change', False)
        self.buddy_change_wait_min = self.config.get('buddy_change_wait_min', 3)
        self.buddy_change_wait_max = self.config.get('buddy_change_wait_max', 5)
        self.min_interval = self.config.get('min_interval', 120)
        self.next_update = None
        self.cache = []
        self.candy_awarded = 0
        self.buddy_distance_needed = 0
        self._validate_config()
        self._check_old_reward()

    def _validate_config(self):
        if isinstance(self.buddy_list, basestring):
            self.buddy_list = [str(pokemon_name).lower().strip()
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
            self.buddy_distance_needed = pokemon.buddy_distance_needed

    def work(self):
        if not self.enabled:
            return WorkerResult.SUCCESS

        if self.buddy_list:
            pokemon = self._get_pokemon_by_name(self._get_pokemon_by_id(self.buddy['id']).name) if 'id' in self.buddy else None
            if self.force_first_change or not self.buddy or pokemon is None or (self.candy_limit != 0 and self.candy_awarded >= self.candy_limit) or self._check_candy_limit_absolute(pokemon):
                self.force_first_change = False

                remaining = []
                for name in self.buddy_list:
                    pokemon = self._get_pokemon_by_name(name)
                    if name not in self.cache and pokemon is not None and not self._check_candy_limit_absolute(pokemon):
                        remaining.append(name)

                if not remaining:
                    self.cache = []
                    return WorkerResult.SUCCESS

                poke_name = remaining[0]
                self.cache.append(poke_name)

                pokemon = self._get_pokemon_by_name(poke_name)
                if pokemon is None:
                    return WorkerResult.ERROR

                if not self.buddy or pokemon.name != self._get_pokemon_by_id(self.buddy['id']).name:
                    self._set_buddy(pokemon)

        if not self.buddy:
            return WorkerResult.SUCCESS

        if self._km_walked() - self.buddy['last_km_awarded'] >= self.buddy_distance_needed:
            self.buddy['last_km_awarded'] += self.buddy_distance_needed
            if not self._get_award():
                return WorkerResult.ERROR

        if self._should_print():
            self._print_update()
            self._compute_next_update()

        return WorkerResult.SUCCESS

    def _set_buddy(self, pokemon):
        request = self.bot.api.create_request()
        request.set_buddy_pokemon(pokemon_id=pokemon.unique_id)
        response_dict = request.call()
        
        data = response_dict.get('responses', {}).get('SET_BUDDY_POKEMON', {})
        result = data.get('result', 0)

        action_delay(self.buddy_change_wait_min, self.buddy_change_wait_max)
        if result == 1:
            updated_buddy = data['updated_buddy']
            self.buddy = updated_buddy
            self.candy_awarded = 0
            self.buddy_distance_needed = pokemon.buddy_distance_needed

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
        request = self.bot.api.create_request()
        request.get_buddy_walked()
        response_dict = request.call()
        
        result = response_dict.get('responses', {}).get('GET_BUDDY_WALKED', {})
        success = result.get('success', False)
        family_id = result.get('family_candy_id', 0)
        candy_awarded = result.get('candy_earned_count', 0)

        if success and family_id != 0:
            candy = inventory.candies().get(family_id)
            candy.add(candy_awarded)
            self.candy_awarded += candy_awarded

            msg = "{candy} {family} candy earned. You now have {quantity} candy!"
            if self.candy_limit != 0 and len(self.buddy_list) > 1:
                msg += " (Candy limit: {candy_earned}/{candy_limit})"
            if candy_awarded == 0:
                msg += " Probably reached candy daily limit"
            self.emit_event(
                'buddy_candy_earned',
                formatted=msg,
                data={
                    'candy': candy_awarded,
                    'family': inventory.candies().get(family_id).type,
                    'quantity': candy.quantity,
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

    def _check_candy_limit_absolute(self, pokemon):
        return self.candy_limit_absolute != 0 and inventory.candies().get(pokemon.family_id).quantity >= self.candy_limit_absolute

    def _check_old_reward(self):
        if not self.buddy or 'last_km_awarded' not in self.buddy:
            return
        km_diff = self._km_walked() - self.buddy['last_km_awarded']
        rewards_size = km_diff // self.buddy_distance_needed
        if rewards_size > 0:
            self._get_award()
            self.buddy['last_km_awarded'] += self.buddy_distance_needed*rewards_size

    def _km_walked(self):
        return inventory.player().player_stats.get("km_walked", 0)

    def _get_pokemon_by_name(self, name):
        pokemons = inventory.pokemons().all()
        pokemon = None
        for p in pokemons:
            if p.name.lower() == name.lower():
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
            formatted='({name}) Buddy next award {km_walked:.2f}/{km_total:.1f} km',
            data={
                'name': pokemon.name,
                'km_walked': self._km_walked() - self.buddy['last_km_awarded'],
                'km_total': self.buddy_distance_needed
            }
        )

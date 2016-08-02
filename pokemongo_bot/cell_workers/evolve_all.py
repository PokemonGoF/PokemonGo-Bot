from pokemongo_bot import logger
from pokemongo_bot.human_behaviour import sleep
from pokemongo_bot.item_list import Item
from pokemongo_bot.cell_workers.base_task import BaseTask

class EvolveAll(BaseTask):
    def initialize(self):
        self.evolve_all = self.config.get('evolve_all', [])
        self.evolve_speed = self.config.get('evolve_speed', 3.7)
        self.evolve_cp_min = self.config.get('evolve_cp_min', 300)
        self.evolve_num_min = self.config.get('evolve_num_min', 5)
        self.use_lucky_egg = self.config.get('use_lucky_egg', False)
        self._validate_config()

    def _validate_config(self):
        if isinstance(self.evolve_all, basestring):
            self.evolve_all = [str(pokemon_name) for pokemon_name in self.evolve_all.split(',')]

    def work(self):
        if not self._should_run():
            return

        response_dict = self.bot.get_inventory()
        cache = {}

        try:
            reduce(dict.__getitem__, [
                "responses", "GET_INVENTORY", "inventory_delta", "inventory_items"], response_dict)
        except KeyError:
            pass
        else:
            inventory_items = response_dict['responses']['GET_INVENTORY']['inventory_delta']['inventory_items']
            candy_data = self._get_candy_data(inventory_items)
            evolve_list = self._sort_by_cp_iv(inventory_items)

            # filter out non-listed pokemen and those with not enough candy
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

            # enable to limit number of pokemons to evolve. Useful for testing.
            # nn = 3
            # if len(evolve_list) > nn:
            #     evolve_list = evolve_list[:nn]
            #

            id_list1 = self.count_pokemon_inventory()
            for pokemon in evolve_list:
                try:
                    self._execute_pokemon_evolve(pokemon, cache)
                except Exception:
                    pass
            id_list2 = self.count_pokemon_inventory()
            release_cand_list_ids = list(set(id_list2) - set(id_list1))

            if release_cand_list_ids:
                logger.log('[#] Evolved {} pokemons! Checking if any of them needs to be released ...'.format(
                    len(release_cand_list_ids)
                ))
                self._release_evolved(release_cand_list_ids)

    def _should_run(self):
        # Don't run after the first tick
        # Lucky Egg should only be popped at the first tick
        if not self.evolve_all or self.bot.tick_count is 1:
            return False

        # Will skip evolving if user wants to use an egg and there is none
        lucky_egg_count = self.bot.item_inventory_count(Item.ITEM_LUCKY_EGG.value)
        if self.use_lucky_egg and lucky_egg_count <= 0:
            logger.log('No lucky eggs... skipping evolve!', 'yellow')
            return False

        # Otherwise try evolving
        return True


    def _release_evolved(self, release_cand_list_ids):
        response_dict = self.bot.get_inventory()
        cache = {}

        try:
            reduce(dict.__getitem__, [
                "responses", "GET_INVENTORY", "inventory_delta", "inventory_items"], response_dict)
        except KeyError:
            pass
        else:
            release_cand_list = self._sort_by_cp_iv(
                response_dict['responses']['GET_INVENTORY']['inventory_delta']['inventory_items'])
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
                        '[#] {} has been exchanged for candy!'.format(pokemon_name), 'red')

    def _get_candy_data(self, inventory_items):
        candy = {}
        for item in inventory_items:
            try:
                reduce(dict.__getitem__, [
                    "inventory_item_data", "candy"], item)
            except KeyError:
                pass
            else:
                try:
                    pokemon_candy = item['inventory_item_data']['candy']
                    candy[pokemon_candy['family_id']] = pokemon_candy['candy']
                except Exception:
                    pass
        return candy


    def _sort_by_cp_iv(self, inventory_items):
        pokemons1 = []
        pokemons2 = []
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
                    v = [
                        pokemon['id'],
                        pokemon_name,
                        pokemon['cp'],
                        self._compute_iv(pokemon),
                        pokemon['pokemon_id']
                    ]
                    if pokemon['cp'] > self.evolve_cp_min:
                        pokemons1.append(v)
                    else:
                        pokemons2.append(v)
                except Exception:
                    pass

        # Sort larger CP pokemons by IV, tie breaking by CP
        pokemons1.sort(key=lambda x: (x[3], x[2]), reverse=True)

        # Sort smaller CP pokemons by CP, tie breaking by IV
        pokemons2.sort(key=lambda x: (x[2], x[3]), reverse=True)

        return pokemons1 + pokemons2

    def _is_evolvable(self, pokemon, candy_data):
        pokemon_name = pokemon[1]
        family_id = pokemon[4]
        # python list is index 0 based, thus - 1
        pokemon_idx = int(family_id) - 1

        # Non-evolvable or top-tier pokemon
        if 'Next Evolution Requirements' not in self.bot.pokemon_list[pokemon_idx]:
            return False

        # filter out non-listed pokemen
        if self.evolve_all[0] != 'all' and pokemon_name not in self.evolve_all:
            return False

        # filter out those with not enough candy
        if 'Previous evolution(s)' in self.bot.pokemon_list[pokemon_idx]:
            family_id = int(self.bot.pokemon_list[pokemon_idx]['Previous evolution(s)'][0]['Number'])

        need_candies = int(self.bot.pokemon_list[pokemon_idx]['Next Evolution Requirements']['Amount'])
        # print('{} need {} candies to evolve, currently have {}'.
        # format(pokemon_name, need_candies, candy_data[family_id]))
        if candy_data[family_id] >= need_candies:
            candy_data[family_id] -= need_candies
            return True
        return False

    def _execute_pokemon_evolve(self, pokemon, cache):
        pokemon_id = pokemon[0]
        pokemon_name = pokemon[1]
        pokemon_cp = pokemon[2]
        pokemon_iv = pokemon[3]

        if pokemon_name in cache:
            return

        self.bot.api.evolve_pokemon(pokemon_id=pokemon_id)
        response_dict = self.bot.api.call()
        status = response_dict['responses']['EVOLVE_POKEMON']['result']
        if status == 1:
            logger.log('[#] Successfully evolved {} with {} CP and {} IV!'.format(
                pokemon_name, pokemon_cp, pokemon_iv
            ))

            sleep(self.evolve_speed)

        else:
            # cache pokemons we can't evolve. Less server calls
            cache[pokemon_name] = 1
            sleep(0.7)

    # TODO: move to utils. These methods are shared with other workers.
    def transfer_pokemon(self, pid):
        self.bot.api.release_pokemon(pokemon_id=pid)
        response_dict = self.bot.api.call()

    def count_pokemon_inventory(self):
        response_dict = self.bot.get_inventory()
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
            cp_iv_logic = release_config.get('logic')
            if not cp_iv_logic:
                cp_iv_logic = self._get_release_config_for('any').get('logic', 'and')

            release_results = {
                'cp': False,
                'iv': False,
            }

            if 'release_below_cp' in release_config:
                min_cp = release_config['release_below_cp']
                if cp < min_cp:
                    release_results['cp'] = True

            if 'release_below_iv' in release_config:
                min_iv = release_config['release_below_iv']
                if iv < min_iv:
                    release_results['iv'] = True

            if release_config.get('always_release'):
                return True

            logic_to_function = {
                'or': lambda x, y: x or y,
                'and': lambda x, y: x and y
            }

            # logger.log(
            #    "[x] Release config for {}: CP {} {} IV {}".format(
            #        pokemon_name,
            #        min_cp,
            #        cp_iv_logic,
            #        min_iv
            #    ), 'yellow'
            # )

            return logic_to_function[cp_iv_logic](*release_results.values())

    def _get_release_config_for(self, pokemon):
        release_config = self.bot.config.release.get(pokemon)
        if not release_config:
            release_config = self.bot.config.release['any']
        return release_config

    def _get_exceptions(self):
        exceptions = self.bot.config.release.get('exceptions')
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
            except Exception:
                pokemon[individual_stat] = 0
                continue
        pokemon_potential = round((total_IV / 45.0), 2)
        return pokemon_potential

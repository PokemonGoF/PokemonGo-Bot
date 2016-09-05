from pokemongo_bot import inventory
from pokemongo_bot.human_behaviour import action_delay
from pokemongo_bot.base_task import BaseTask
from pokemongo_bot.worker_result import WorkerResult


class BuddyPokemon(BaseTask):
    SUPPORTED_TASK_API_VERSION = 1

    def initialize(self):
    	self.api = self.bot.api
        self.buddy = self.bot.player_data.get('buddy_pokemon', None)
        self.buddy_km_needed = 0
    	self.buddy_list = self.config.get('buddy_list', [])
        '''
    	self.only_one_per_family = self.config.get('only_one_per_family', True)
    	self.best_cp_in_family = self.config.get('best_cp_in_family', True)
    	self.candy_limit = self.config.get('candy_limit', 0) # 0 = Max Limit
        '''
    	self.buddy_change_wait_min = self.config.get('buddy_change_wait_min', 3)
    	self.buddy_change_wait_max = self.config.get('buddy_change_wait_max', 5)
    	self._validate_config()

    def _validate_config(self):
    	if isinstance(self.buddy_list, basestring):
            self.buddy_list = [str(pokemon_name).strip().lower() for pokemon_name in self.buddy_list.split(',')]

    def work(self):
        if self.buddy_list:
            if self.buddy_list[0] == 'none':
                return WorkerResult.SUCCESS
            # Else check for existing buddy and candy limit and set or not a new buddy

        if self.buddy is None:
            return WorkerResult.SUCCESS

        if self.buddy_km_needed == 0:
            pokemon = self._get_pokemon(self.buddy['id'])
            self.buddy_km_needed = pokemon.buddy_km_needed

        if self._km_walked() - max(self.buddy['start_km_walked'], self.buddy['last_km_awarded']) >= self.buddy_km_needed:
            if self._get_award():
                return WorkerResult.SUCCESS
            return WorkerResult.ERROR

        return WorkerResult.SUCCESS


   	def _filter_pokemon(self):
   		pokemons = pokemons = inventory.pokemons().all().sort(key=lambda x: x.pokemon_id)
   		if self.buddy_list[0] != 'all':
   			pokemons = filter(lambda x: x.name.lower() in self.buddy_list, pokemons)
   		if self.only_one_per_family:
   			ids_family = list(set(map(lambda x: x.family_id, pokemon))).sort()
   			temp_list = [filter(lambda x: x.family_id == y, pokemons) for y in ids_family]
            pokemons = [p for family in temp_list for p = family.sort(key=lambda x: x.cp, reverse=self.best_cp_in_family)[0]]
   		return pokemons

    def _set_buddy(self, pokemon):
        response_dict = self.api.set_buddy_pokemon(pokemon_id=pokemon.unique_id)
        try:
            result = response_dict['responses']['SET_BUDDY_POKEMON']['result']
        except KeyError:
            return False

        if result == 1:
            updated_buddy = response_dict['responses']['SET_BUDDY_POKEMON']['updated_buddy']
            
            ### Is it needed ??
            unique_id = updated_buddy.get('id', -1)
            start_km_walked = updated_buddy.get('start_km_walked', 0)
            last_km_awarded = updated_buddy.get('last_km_awarded', 0)

            self.emit_event(
                'buddy_update',
                formated='{name} was set as Buddy Pokemon.',
                data={
                    'name': pokemon.name
                }
            )
            return True
        else
            error_codes = {
                0: 'UNSET',
                2: 'ERROR_POKEMON_DEPLOYED',
                3: 'ERROR_POKEMON_NOT_OWNED',
                4: 'ERROR_POKEMON_IS_EGG'
            }
            self.emit_event(
                'buddy_update_fail',
                formated='Error while setting {name} as Buddy Pokemon: {error}',
                data={
                    'name': pokemon.name,
                    'error': error_codes[result]
                }
            )
            return False

    def _km_walked(self):
        inv = inventory.jsonify_inventory()
        km_walked = 0
        for inv_data in inv:
            inv_data = inv_data.get("inventory_item_data", {})
            if "player_stats" in inv_data:
                km_walked = inv_data.get("player_stats", {}).get("km_walked", 0)
                break
        return km_walked

    def _get_pokemon(self, unique_id):
        pokemons = inventory.pokemons().all()
        for pokemon in pokemons:
            if pokemon.unique_id == unique_id:
                return pokemon

    def _get_award(self):
        response_dict = self.api.get_buddy_walked()
        try:
            success = response_dict['responses']['GET_BUDDY_WALKED']['SUCCESS']
        except KeyError:
            return False

        if success:
            family_id = response_dict['responses']['GET_BUDDY_WALKED']['family_candy_id']
            candy_earned = response_dict['responses']['GET_BUDDY_WALKED']['candy_earned_count']

            self.emit_event(
                'buddy_candy_earned',
                formated='{candy} {family} candy earned.',
                data={
                    'candy': candy_earned,
                    'family': ## TO-DO
                }
            )
            return True
        else:
            self.emit_event(
                'buddy_candy_fail',
                formated='Error trying to get candy from buddy.'
            )
            return False


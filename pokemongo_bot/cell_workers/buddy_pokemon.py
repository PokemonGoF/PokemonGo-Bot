from pokemongo_bot import inventory
from pokemongo_bot.human_behaviour import action_delay
from pokemongo_bot.base_task import BaseTask
from pokemongo_bot.worker_result import WorkerResult


class BuddyPokemon(BaseTask):
    SUPPORTED_TASK_API_VERSION = 1

    def initialize(self):
    	self.api = self.bot.api
    	self.buddy_list = self.config.get('buddy_list', [])
        '''
    	self.only_one_per_family = self.config.get('only_one_per_family', True)
    	self.best_cp_in_family = self.config.get('best_cp_in_family', True)
    	self.candy_limit = self.config.get('candy_limit', 0) # 0 = Max Limit
        '''
    	self.buddy_change_wait_min = self.config.get('buddy_change_wait_min', 3)
    	self.buddy_change_wait_max = self.config.get('buddy_change_wait_max', 5)
    	self.km_walked = 0
    	self.last_km_walked = 0
    	self._validate_config()

    def _validate_config(self):
    	if isinstance(self.buddy_list, basestring):
            self.buddy_list = [str(pokemon_name).strip().lower() for pokemon_name in self.buddy_list.split(',')]

    def work(self):
        if not self._should_run():
    		return WorkerResult.ERROR

    	###filtered_list = self._filter_pokemon()
        



   	def _should_run(self):
   		if not self.buddy_list or self.buddy_list[0] == 'none':
   			return False
   		return True

   	def _filter_pokemon(self):
   		pokemons = pokemons = inventory.pokemons().all().sort(key=lambda x: x.pokemon_id)
   		if self.buddy_list[0] != 'all':
   			pokemons = filter(lambda x: x.name.lower() in self.buddy_list, pokemons)
   		if self.only_one_per_family:
   			ids_family = list(set(map(lambda x: x.family_id, pokemon))).sort()
   			temp_list = [filter(lambda x: x.family_id == y, pokemons) for y in ids_family]
   			if self.best_cp_in_family:
   				pokemons = [p for family in temp_list for p = max(family, key=lambda x: x.cp)]
   			else:
   				pokemons = [p for family in temp_list for p = min(family, key=lambda x: x.cp)]
   		return pokemons

    def _set_buddy(self, pokemon):
        response_dict = self.api.set_buddy_pokemon(pokemon_id=pokemon.unique_id)
        result = response_dict['responses']['SET_BUDDY_POKEMON']['result']

        if result == 1:
            updated_buddy = response_dict['responses']['SET_BUDDY_POKEMON']['updated_buddy']
            ### Why need those
            
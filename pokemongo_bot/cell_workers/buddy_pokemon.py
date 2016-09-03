from pokemongo_bot import inventory
from pokemongo_bot.human_behaviour import action_delay
from pokemongo_bot.base_task import BaseTask
from pokemongo_bot.worker_result import WorkerResult


class BuddyPokemon(BaseTask):
    SUPPORTED_TASK_API_VERSION = 1

    def initialize(self):
    	self.api = self.bot.api
    	self.buddy_list = self.config.get('buddy_list', [])
    	self.buddy_change_wait_min = self.config.get('buddy_change_wait_min', 3)
    	self.buddy_change_wait_max = self.config.get('buddy_change_wait_max', 5)
    	self.candy_limit = self.config.get('candy_limit', 0) # 0 = No Limit



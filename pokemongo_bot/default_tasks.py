import random
import sys

from pokemongo_bot import inventory
from human_behaviour import sleep


class DefaultTasks(object):
	"""
	Tasks that must be run by default, not enabled/disabled by the user
	"""
	def __init__(self, bot, config):
		self.bot = bot
		self.config = config
		self._process_tasks()

	def work(self):
		for task in self.tasks:
			task.work()

	def _process_tasks(self):
		self.tasks = [
			CompleteTutorial(self.bot, self.config),
			ChooseTeam(self.bot, self.config),
			CollectLevelUpReward(self.bot, self.config)
		]


class CompleteTutorial(object):
	"""
	Completes the tutorial when starting the bot.
	Nickname is configurable in the config and if not set it uses the account username.
	If nickname not available it generates another one using the first 10 chars
		from the wanted nickname and 5 random digits.
	"""
	def __init__(self, bot, config):
		self.bot = bot
		self.config = config
		self.should_run = True
		self._process_config()
		
	def work(self):
		if self.should_run:
			self.should_run = False
			self._check_tutorial_state()

	def _process_config(self):
		self.nickname = self.config.nickname

	def _check_tutorial_state(self):
		self._player=self.bot.player_data
		tutorial_state = self._player.get('tutorial_state', [])
		
		# LEGAL_SCREEN = 0
		if not 0 in tutorial_state:
			sleep(2)
			if self._set_tutorial_state(0):
				self.bot.logger.info('Completed legal screen')
				tutorial_state = self._player.get('tutorial_state', [])
			else:
				return

		# AVATAR_SELECTION = 1
		if not 1 in tutorial_state:
			sleep(7)
			if self._set_avatar():
				if self._set_tutorial_state(1):
					self.bot.logger.info('Completed avatar selection')
					tutorial_state = self._player.get('tutorial_state', [])
				else:
					return
			else:
				self.bot.logger.error('Error during avatar selection')
				return

		# POKEMON_CAPTURE = 3
		if not 3 in tutorial_state:
			sleep(10)
			if self._encounter_tutorial():
				self.bot.logger.info('Completed first capture')
			else:
				self.bot.logger.error('Error during first capture')
				return

		# NAME_SELECTION = 4
		if not 4 in tutorial_state:
			if not self.nickname:
				self.bot.logger.info("No nickname defined in config, using account username")
				self.nickname = self.config.username

			self.bot.logger.info(u'Trying to set {} as nickname'.format(self.nickname))
			sleep(5)
			if self._set_nickname(self.nickname):
				self._set_tutorial_state(4)
				tutorial_state = self._player.get('tutorial_state', [])
			else:
				self.bot.logger.error('Error trying to set {} as nickname. Trying suggested nickname'.format(self.nickname))
				generated = self._generate_nickname()
				if self._set_nickname(generated):
					self._set_tutorial_state(4)
					tutorial_state = self._player.get('tutorial_state', [])
				else:
					self.bot.logger.error('Error trying to set {} as nickname'.format(generated))
					return

		# FIRST_TIME_EXPERIENCE_COMPLETE = 7
		if not 7 in tutorial_state:
			if self._set_tutorial_state(7):
				self.bot.logger.info('Completed first time experience')
			else:
				return

	def _encounter_tutorial(self):
		# You just need to call the API with the pokemon you choose
		# Probably can't get MewTwo as first pokemon though
		first_pokemon_id = random.choice([1, 4, 7])
		response_dict = self.bot.api.encounter_tutorial_complete(pokemon_id=first_pokemon_id)
		try:
			if response_dict['responses']['ENCOUNTER_TUTORIAL_COMPLETE']['result'] == 1:
				return True
			else:
				self.bot.logger.error("Error during encouter tutorial")
				return False
		except KeyError:
			self.bot.logger.error("KeyError during encouter tutorial")
			return False

	def _random_avatar(self):
		avatar= {}
		# 0 = Male, 1 = Female
		avatar['gender']=random.randint(0,1)
		# What is the max value of each parameter ?
		# Default is 0, anyway human player will stop
		# at the first choices in general, so fully
		# random on the whole avatar space is not the way to go either
		avatar['skin']=random.randint(0,3)
		avatar['hair']=random.randint(0,3)
		avatar['shirt']=random.randint(0,3)
		avatar['pants']=random.randint(0,3)
		avatar['hat']=random.randint(0,3)
		avatar['shoes']=random.randint(0,3)
		avatar['eyes']=random.randint(0,3)
		avatar['backpack']=random.randint(0,3)
		return avatar

	def _set_avatar(self):
		avatar = self._random_avatar()
		response_dict = self.bot.api.set_avatar(player_avatar=avatar)
		status = response_dict['responses']['SET_AVATAR']['status']
		try:
			if status == 1:
				return True
			else:
				error_codes = {
					0: 'UNSET',
					1: 'SUCCESS',
					2: 'AVATAR_ALREADY_SET',
					3: 'FAILURE',
				}
				self.bot.logger.error("Error during avatar selection : {}".format(error_codes[status]))
				return False
		except KeyError:
			self.bot.logger.error("KeyError during avatar selection")
			return False

	def _generate_nickname(self):
		nickname = self.nickname[:10]
		random_nums = ''.join(random.choice("0123456789") for i in range(5))
		nickname += random_nums
		return nickname

	def _set_nickname(self, nickname):
		response_dict = self.bot.api.claim_codename(codename=nickname)
		try:
			result = response_dict['responses']['CLAIM_CODENAME']['status']
			if result == 1:
				self.bot.logger.info(u'Name changed to {}'.format(nickname))
				return True
			else:
				# Would be nice to get the text directly from the proto Enum
				error_codes = {
					0: 'UNSET',
					1: 'SUCCESS',
					2: 'CODENAME_NOT_AVAILABLE',
					3: 'CODENAME_NOT_VALID',
					4: 'CURRENT_OWNER',
					5: 'CODENAME_CHANGE_NOT_ALLOWED'
				}
				self.bot.logger.error(
					u'Error while changing nickname : {}'.format(error_codes[result]))
				return False
		except KeyError:
			return False

	def _set_tutorial_state(self, completed):
		response_dict = self.bot.api.mark_tutorial_complete(
							tutorials_completed=[completed], 
							send_marketing_emails=False, 
							send_push_notifications=False
						)
		try:
			self._player = response_dict['responses'][
				'MARK_TUTORIAL_COMPLETE']['player_data']
			return response_dict['responses']['MARK_TUTORIAL_COMPLETE']['success']
		except KeyError:
			self.bot.logger.error("KeyError while setting tutorial state")
			return False


class ChooseTeam(object):
	"""
	Picks desired team when reaching level 5.
	"""
	def __init__(self, bot, config):
		self.bot = bot
		self.config = config
		self.should_run = True
		self._process_config()
		
	def work(self):
		if self.should_run and inventory.player().level >= 5:
			self.should_run = False
			self._set_team()

	def _process_config(self):
		self.team = self.config.team

	def _set_team(self):
		if self.team == 0:
			return

		if self.bot.player_data.get('team', 0) != 0:
			self.bot.logger.info(u'Team already picked')
			return

		sleep(10)
		response_dict = self.bot.api.set_player_team(team=self.team)
		try:
			result = response_dict['responses']['SET_PLAYER_TEAM']['status']
			if result == 1:
				team_codes = {
					1: 'Mystic (BLUE)',
					2: 'Valor (RED)',
					3: 'Instinct (YELLOW)'
				}
				self.bot.logger.info(u'Picked Team {}.'.format(team_codes[self.team]))
			else:
				error_codes = {
					0: 'UNSET',
					1: 'SUCCESS',
					2: 'TEAM_ALREADY_SET',
					3: 'FAILURE'
				}
				self.bot.logger.error(u'Error while picking team : {}'.format(error_codes[result]))
		except KeyError:
			return


class CollectLevelUpReward(object):
	"""
	Collect reward when user levels up.
	"""	
	def __init__(self, bot, config):
		self.bot = bot
		self.config = config
		self.previous_level = 0
		self.current_level = 0
		self._process_config()

	def work(self):
		self.current_level = inventory.player().level
		if self.current_level > self.previous_level:
			if self.previous_level != 0:
				self.bot.event_manager.emit(
					'level_up',
					sender=self,
					level='info',
					formatted='Level up from {previous_level} to {current_level}',
					data={
						'previous_level': self.previous_level,
						'current_level': self.current_level
					}
				)
			self.previous_level = self.current_level
			self._collect_level_reward()
		if self.level_limit != -1 and self.current_level >= self.level_limit:
			sys.exit("You have reached your target level! Exiting now.")

	def _process_config(self):
		self.level_limit = self.config.level_limit

	def _collect_level_reward(self):
		response_dict = self.bot.api.level_up_rewards(level=self.current_level)
		if 'status_code' in response_dict and response_dict['status_code'] == 1:
			data = (response_dict.get('responses', {}).get('LEVEL_UP_REWARDS', {}).get('items_awarded', []))
			for item in data:
				if 'item_id' in item and str(item['item_id']) in self.bot.item_list:
					got_item = self.bot.item_list[str(item['item_id'])]
					item['name'] = got_item
					count = 'item_count' in item and item['item_count'] or 0
					inventory.items().get(item['item_id']).add(count)
			self.bot.event_manager.emit(
				'level_up_reward',
				sender=self,
				level='info',
				formatted='Received level up reward: {items}',
				data={
					# [{'item_id': 3, 'name': u'Ultraball', 'item_count': 10}, {'item_id': 103, 'name': u'Hyper Potion', 'item_count': 10}]
					'items': ', '.join(["{}x {}".format(x['item_count'], x['name']) for x in data])
				}
			)

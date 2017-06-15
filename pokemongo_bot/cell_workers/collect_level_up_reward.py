import sys

from pokemongo_bot.base_task import BaseTask
from pokemongo_bot import inventory


class CollectLevelUpReward(BaseTask):
    SUPPORTED_TASK_API_VERSION = 1

    current_level = 0
    previous_level = 0

    def initialize(self):
        self._process_config()
        self.current_level = inventory.player().level
        self.previous_level = 0

    def work(self):
        if self._should_run():
            self.current_level = inventory.player().level

            if self.collect_reward:
                # let's check level reward on bot initialization
                # to be able get rewards for old bots
                if self.previous_level == 0:
                    self._collect_level_reward()
                # level up situation
                elif self.current_level > self.previous_level:
                    self.emit_event(
                        'level_up',
                        formatted='Level up from {previous_level} to {current_level}',
                        data={
                            'previous_level': self.previous_level,
                            'current_level': self.current_level
                        }
                    )
                    self._collect_level_reward()

            if self.level_limit != -1 and self.current_level >= self.level_limit:
                sys.exit("You have reached your target level! Exiting now.")

            self.previous_level = self.current_level

    def _process_config(self):
        self.level_limit = self.config.get('level_limit', -1)
        self.collect_reward = self.config.get('collect_reward', True)

    def _should_run(self):
        return self.level_limit != -1 or self.collect_reward

    def _collect_level_reward(self):
        request = self.bot.api.create_request()
        request.level_up_rewards(level=self.current_level)
        response_dict = request.call()
        
        if 'status_code' in response_dict and response_dict['status_code'] == 1:
            data = (response_dict
                    .get('responses', {})
                    .get('LEVEL_UP_REWARDS', {})
                    .get('items_awarded', []))

            for item in data:
                if 'item_id' in item and str(item['item_id']) in self.bot.item_list:
                    got_item = self.bot.item_list[str(item['item_id'])]
                    item['name'] = got_item
                    count = 'item_count' in item and item['item_count'] or 0
                    inventory.items().get(item['item_id']).add(count)
            self.emit_event(
                'level_up_reward',
                formatted='Received level up reward: {items}',
                data={
                    # [{'item_id': 3, 'name': u'Ultraball', 'item_count': 10}, {'item_id': 103, 'name': u'Hyper Potion', 'item_count': 10}]
                    'items': ', '.join(["{}x {}".format(x['item_count'], x['name']) for x in data])
                }
            )

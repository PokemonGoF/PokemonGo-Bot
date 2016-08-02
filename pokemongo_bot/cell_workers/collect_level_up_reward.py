from pokemongo_bot import logger
from pokemongo_bot.cell_workers.base_task import BaseTask


class CollectLevelUpReward(BaseTask):
    current_level = 0
    previous_level = 0

    def initialize(self):
        self.current_level = self._get_current_level()
        self.previous_level = 0

    def work(self):
        self.current_level = self._get_current_level()

        # let's check level reward on bot initialization
        # to be able get rewards for old bots
        if self.previous_level == 0:
            self._collect_level_reward()
        # level up situation
        elif self.current_level > self.previous_level:
            logger.log('Level up from {} to {}!'.format(self.previous_level, self.current_level), 'green')
            self._collect_level_reward()

        self.previous_level = self.current_level

    def _collect_level_reward(self):
        response_dict = self.bot.api.level_up_rewards(level=self.current_level)
        if 'status_code' in response_dict and response_dict['status_code'] == 1:
            data = (response_dict
                    .get('responses', {})
                    .get('LEVEL_UP_REWARDS', {})
                    .get('items_awarded', []))

            if data:
                logger.log('Collected level up rewards:', 'green')

            for item in data:
                if 'item_id' in item and str(item['item_id']) in self.bot.item_list:
                    got_item = self.bot.item_list[str(item['item_id'])]
                    count = 'item_count' in item and item['item_count'] or 0
                    logger.log('{} x {}'.format(got_item, count), 'green')

    def _get_current_level(self):
        level = 0
        response_dict = self.bot.get_inventory()
        data = (response_dict
                .get('responses', {})
                .get('GET_INVENTORY', {})
                .get('inventory_delta', {})
                .get('inventory_items', {}))

        for item in data:
            level = (item
                     .get('inventory_item_data', {})
                     .get('player_stats', {})
                     .get('level', 0))

            # we found a level, no need to continue iterate
            if level:
                break

        return level

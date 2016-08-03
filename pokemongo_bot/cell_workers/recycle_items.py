import json
import os
from pokemongo_bot import logger
from pokemongo_bot.cell_workers.base_task import BaseTask
from pokemongo_bot.tree_config_builder import ConfigException

class RecycleItems(BaseTask):
    def initialize(self):
        self.item_filter = self.config.get('item_filter', {})
        self._validate_item_filter()
        self.balls = self.config.get('balls', {})

    def _validate_item_filter(self):
        item_list = json.load(open(os.path.join('data', 'items.json')))
        for config_item_name, bag_count in self.item_filter.iteritems():
            if config_item_name not in item_list.viewvalues():
                if config_item_name not in item_list:
                    raise ConfigException("item {} does not exist, spelling mistake? (check for valid item names in data/items.json)".format(config_item_name))

    def work(self):
        self.bot.latest_inventory = None
        item_count_dict = self.bot.item_inventory_count('all')

        balls = {};

        for item_id, bag_count in item_count_dict.iteritems():
            item_name = self.bot.item_list[str(item_id)]
            id_filter = self.item_filter.get(item_name, 0)
            if id_filter is not 0:
                id_filter_keep = id_filter.get('keep', 20)
            else:
                id_filter = self.item_filter.get(str(item_id), 0)
                if id_filter is not 0:
                    id_filter_keep = id_filter.get('keep', 20)

            bag_count = self.bot.item_inventory_count(item_id)

            if item_id in range(1,4):
                balls[item_id] = bag_count

            if (item_name in self.item_filter or str(item_id) in self.item_filter) and bag_count > id_filter_keep:
                items_recycle_count = bag_count - id_filter_keep
                self.do_recycle_item(item_id=item_id, count=items_recycle_count, item_name=item_name)

        ball_diff = sum(balls.values()) - self.balls
        if ball_diff > 0:
            for ball in range(1,5):
                item_name = self.bot.item_list[str(ball)]
                try:
                    balls[ball]
                except KeyError:
                    logger.log("-- 0 " + item_name, 'yellow')
                else:
                    if ball_diff <= balls[ball]:
                        self.do_recycle_item(item_id=ball, count=balls[ball], item_name=item_name)
                        break

                    else:
                        self.do_recycle_item(item_id=ball, count=ball_diff, item_name=item_name)
                        ball_diff -= balls[ball]

    def do_recycle_item(self, item_id, count, item_name):
        response_dict_recycle = self.send_recycle_item_request(item_id=item_id, count=count)
        result = response_dict_recycle.get('responses', {}).get('RECYCLE_INVENTORY_ITEM', {}).get('result', 0)

        if result == 1:  # Request success
            message_template = "-- Discarded {}x {} "
            message = message_template.format(str(count), item_name)
            logger.log(message, 'green')
        else:
            logger.log("-- Failed to discard " + item_name, 'red')

    def send_recycle_item_request(self, item_id, count):
        # Example of good request response
        #{'responses': {'RECYCLE_INVENTORY_ITEM': {'result': 1, 'new_count': 46}}, 'status_code': 1, 'auth_ticket': {'expire_timestamp_ms': 1469306228058L, 'start': '/HycFyfrT4t2yB2Ij+yoi+on778aymMgxY6RQgvrGAfQlNzRuIjpcnDd5dAxmfoTqDQrbz1m2dGqAIhJ+eFapg==', 'end': 'f5NOZ95a843tgzprJo4W7Q=='}, 'request_id': 8145806132888207460L}
        return self.bot.api.recycle_inventory_item(
            item_id=item_id,
            count=count
        )

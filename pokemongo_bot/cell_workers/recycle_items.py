import json
import os
from pokemongo_bot.worker_result import WorkerResult
from pokemongo_bot import logger
from pokemongo_bot.cell_workers.base_task import BaseTask
from pokemongo_bot.tree_config_builder import ConfigException

class RecycleItems(BaseTask):
    def initialize(self):
        self.items_filter = self._get_recycle_items_filter()
        self._validate_item_filter()

    def _get_recycle_items_filter(self):
        for task in self.bot.config.raw_tasks:
            task_type = task.get('type', None)
            if task_type == "RecycleItems":
                return task.get('config', {}).get('item_filter', {})

    def _validate_item_filter(self):
        item_list = json.load(open(os.path.join('data', 'items.json')))
        for config_item_name, bag_count in self.items_filter.iteritems():
            if config_item_name not in item_list.viewvalues():
                if config_item_name not in item_list:
                    raise ConfigException("item {} does not exist, spelling mistake? (check for valid item names in data/items.json)".format(config_item_name))

    def work(self):
        if not self.bot.has_space_for_loot():
            self.bot.latest_inventory = None
            item_counts_in_bag_dict = self.bot.item_inventory_count('all')

            for item_id, item_count_in_bag in item_counts_in_bag_dict.iteritems():
                item = RecycleItems.Item(item_id, self.items_filter, self.bot)

                if item.should_be_recycled():
                    item.request_recycle()
                    item.print_result_in_log()

        return WorkerResult.SUCCESS

    class Item:
        def __init__(self, item_id, items_filter, bot):
            self.bot = bot
            self.id = item_id
            self.name = bot.item_list[str(item_id)]
            self.items_filter = items_filter
            self.amount_to_keep = self.get_amount_to_keep()
            self.amount_in_bag = bot.item_inventory_count(self.id)
            self.amount_to_recycle = 0 if self.amount_to_keep is None else self.amount_in_bag - self.amount_to_keep
            self.recycle_item_request_result = None

        def get_amount_to_keep(self):
            item_filter_config = self.items_filter.get(self.name, 0)
            if item_filter_config is not 0:
                return item_filter_config.get('keep', 20)
            else:
                item_filter_config = self.items_filter.get(str(self.id), 0)
                if item_filter_config is not 0:
                    return item_filter_config.get('keep', 20)

        def should_be_recycled(self):
            return (self.name in self.items_filter or str(self.id) in self.items_filter) and self.amount_to_recycle > 0

        def request_recycle(self):
            response = self.bot.api.recycle_inventory_item(item_id=self.id, count=self.amount_to_recycle)
            # Example of good request response
            # {'responses': {'RECYCLE_INVENTORY_ITEM': {'result': 1, 'new_count': 46}}, 'status_code': 1, 'auth_ticket': {'expire_timestamp_ms': 1469306228058L, 'start': '/HycFyfrT4t2yB2Ij+yoi+on778aymMgxY6RQgvrGAfQlNzRuIjpcnDd5dAxmfoTqDQrbz1m2dGqAIhJ+eFapg==', 'end': 'f5NOZ95a843tgzprJo4W7Q=='}, 'request_id': 8145806132888207460L}
            self.recycle_item_request_result = response.get('responses', {}).get('RECYCLE_INVENTORY_ITEM', {}).get('result', 0)

        def is_recycling_success(self):
            return self.recycle_item_request_result == 1

        def print_result_in_log(self):
            if self.is_recycling_success():
                message_template = "-- Discarded {}x {} (keeps only {} maximum) "
                message = message_template.format(str(self.amount_to_recycle), self.name, str(self.amount_to_keep))
                logger.log(message, 'green')
            else:
                logger.log("-- Failed to discard " + self.name, 'red')

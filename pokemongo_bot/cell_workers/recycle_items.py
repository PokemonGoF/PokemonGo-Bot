import json
import os
from pokemongo_bot.base_task import BaseTask
from pokemongo_bot.tree_config_builder import ConfigException

class RecycleItems(BaseTask):
    SUPPORTED_TASK_API_VERSION = 1

    def initialize(self):
        self.item_filter = self.config.get('item_filter', {})
        self._validate_item_filter()

    def _validate_item_filter(self):
        item_list = json.load(open(os.path.join('data', 'items.json')))
        for config_item_name, bag_count in self.item_filter.iteritems():
            if config_item_name not in item_list.viewvalues():
                if config_item_name not in item_list:
                    raise ConfigException("item {} does not exist, spelling mistake? (check for valid item names in data/items.json)".format(config_item_name))

    def work(self):
        self.bot.latest_inventory = None
        item_count_dict = self.bot.item_inventory_count('all')

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
            if (item_name in self.item_filter or str(item_id) in self.item_filter) and bag_count > id_filter_keep:
                items_recycle_count = bag_count - id_filter_keep
                response_dict_recycle = self.send_recycle_item_request(item_id=item_id, count=items_recycle_count)
                result = response_dict_recycle.get('responses', {}).get('RECYCLE_INVENTORY_ITEM', {}).get('result', 0)

                if result == 1: # Request success
                    self.emit_event(
                        'item_discarded',
                        formatted='Discarded {amount}x {item} (maximum {maximum}).',
                        data={
                            'amount': str(items_recycle_count),
                            'item': item_name,
                            'maximum': str(id_filter_keep)
                        }
                    )
                else:
                    self.emit_event(
                        'item_discard_fail',
                        formatted="Failed to discard {item}",
                        data={
                            'item': item_name
                        }
                    )

    def send_recycle_item_request(self, item_id, count):
        # Example of good request response
        #{'responses': {'RECYCLE_INVENTORY_ITEM': {'result': 1, 'new_count': 46}}, 'status_code': 1, 'auth_ticket': {'expire_timestamp_ms': 1469306228058L, 'start': '/HycFyfrT4t2yB2Ij+yoi+on778aymMgxY6RQgvrGAfQlNzRuIjpcnDd5dAxmfoTqDQrbz1m2dGqAIhJ+eFapg==', 'end': 'f5NOZ95a843tgzprJo4W7Q=='}, 'request_id': 8145806132888207460L}
        return self.bot.api.recycle_inventory_item(
            item_id=item_id,
            count=count
        )

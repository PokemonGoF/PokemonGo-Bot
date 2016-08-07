import json
import os
from pokemongo_bot.base_task import BaseTask
from pokemongo_bot.worker_result import WorkerResult
from pokemongo_bot.tree_config_builder import ConfigException

class RecycleItems(BaseTask):
    SUPPORTED_TASK_API_VERSION = 1

    """
    Recycle undesired items if there is less than five space in inventory.
    You can use either item's name or id. For the full list of items see ../../data/items.json

    It's highly recommended to put this task before the move_to_fort task in the config file so you'll most likely be able to loot.

    Example config :
    {
      "type": "RecycleItems",
      "config": {
        "item_filter": {
          "Pokeball": {"keep": 20},
          "Greatball": {"keep": 50},
          "Ultraball": {"keep": 100},
          "Potion": {"keep": 0},
          "Super Potion": {"keep": 0},
          "Hyper Potion": {"keep": 20},
          "Max Potion": {"keep": 50},
          "Revive": {"keep": 0},
          "Max Revive": {"keep": 20},
          "Razz Berry": {"keep": 20}
        }
      }
    }
    """

    def initialize(self):
        self.items_filter = self.config.get('item_filter', {})
        self._validate_item_filter()

    def _validate_item_filter(self):
        """
        Validate user's item filter config
        :return: Nothing.
        :rtype: None
        :raise: ConfigException: When an item doesn't exist in ../../data/items.json
        """
        item_list = json.load(open(os.path.join('data', 'items.json')))
        for config_item_name, bag_count in self.items_filter.iteritems():
            if config_item_name not in item_list.viewvalues():
                if config_item_name not in item_list:
                    raise ConfigException("item {} does not exist, spelling mistake? (check for valid item names in data/items.json)".format(config_item_name))

    def work(self):
        """
        Discard items if necessary.
        :return: Always returns WorkerResult.SUCCESS.
        :rtype: WorkerResult
        """
        if not self.bot.has_space_for_loot():
            # Updating user's inventory
            self.bot.latest_inventory = None
            # Getting every item in user's inventory
            item_counts_in_bag_dict = self.bot.item_inventory_count('all')

            # For each user's item in inventory recycle the item if needed
            for item_id, item_count_in_bag in item_counts_in_bag_dict.iteritems():
                item = RecycleItems._Item(item_id, self.items_filter, self)

                if item.should_be_recycled():
                    item.request_recycle()
                    item.emit_recycle_result()

        return WorkerResult.SUCCESS

    class _Item:
        """
        An item found in user's inventory.

        This class contains details of recycling process.
        """
        def __init__(self, item_id, items_filter, recycle_items):
            """
            Initializes an item
            :param item_id: Item's id.
            :param items_filter: List of items and their maximum amount to keep.
            :param recycle_items: The recycle_items instance.
            """
            self.recycle_items = recycle_items
            self.bot = recycle_items.bot
            self.id = item_id
            self.name = recycle_items.bot.item_list[str(item_id)]
            self.items_filter = items_filter
            self.amount_to_keep = self._get_amount_to_keep()
            self.amount_in_inventory = recycle_items.bot.item_inventory_count(self.id)
            self.amount_to_recycle = 0 if self.amount_to_keep is None else self.amount_in_inventory - self.amount_to_keep
            self.recycle_item_request_result = None

        def _get_amount_to_keep(self):
            """
            Determine item's amount to keep in inventory.
            :return: Item's amount to keep in inventory.
            :rtype: int
            """
            item_filter_config = self.items_filter.get(self.name, 0)
            if item_filter_config is not 0:
                return item_filter_config.get('keep', 20)
            else:
                item_filter_config = self.items_filter.get(str(self.id), 0)
                if item_filter_config is not 0:
                    return item_filter_config.get('keep', 20)

        def should_be_recycled(self):
            """
            Returns a value indicating whether the item should be recycled.
            :return: True if the title should be recycled; otherwise, False.
            :rtype: bool
            """
            return (self.name in self.items_filter or str(self.id) in self.items_filter) and self.amount_to_recycle > 0

        def request_recycle(self):
            """
            Request recycling of the item and store api call response's result.
            :return: Nothing.
            :rtype: None
            """
            response = self.bot.api.recycle_inventory_item(item_id=self.id, count=self.amount_to_recycle)
            # Example of good request response
            # {'responses': {'RECYCLE_INVENTORY_ITEM': {'result': 1, 'new_count': 46}}, 'status_code': 1, 'auth_ticket': {'expire_timestamp_ms': 1469306228058L, 'start': '/HycFyfrT4t2yB2Ij+yoi+on778aymMgxY6RQgvrGAfQlNzRuIjpcnDd5dAxmfoTqDQrbz1m2dGqAIhJ+eFapg==', 'end': 'f5NOZ95a843tgzprJo4W7Q=='}, 'request_id': 8145806132888207460L}
            self.recycle_item_request_result = response.get('responses', {}).get('RECYCLE_INVENTORY_ITEM', {}).get('result', 0)

        def _is_recycling_success(self):
            """
            Returns a value indicating whether the item has been successfully recycled.
            :return: True if the item has been successfully recycled; otherwise, False.
            :rtype: bool
            """
            return self.recycle_item_request_result == 1

        def emit_recycle_result(self):
            """
            Emits recycle result in logs
            :return: Nothing.
            :rtype: None
            """
            if self._is_recycling_success():
                self.recycle_items.emit_event(
                    'item_discarded',
                    formatted='Discarded {amount}x {item} (maximum {maximum}).',
                    data={
                        'amount': str(self.amount_to_recycle),
                        'item': self.name,
                        'maximum': str(self.amount_to_keep)
                    }
                )
            else:
                self.recycle_items.emit_event(
                    'item_discard_fail',
                    formatted="Failed to discard {item}",
                    data={
                        'item': self.name
                    }
                )

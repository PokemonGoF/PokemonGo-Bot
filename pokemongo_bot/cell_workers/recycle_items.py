import json
import os
from pokemongo_bot import inventory
from pokemongo_bot.base_dir import _base_dir
from pokemongo_bot.base_task import BaseTask
from pokemongo_bot.worker_result import WorkerResult
from pokemongo_bot.tree_config_builder import ConfigException

DEFAULT_MIN_EMPTY_SPACE = 6

class RecycleItems(BaseTask):
    SUPPORTED_TASK_API_VERSION = 1

    """
    Recycle undesired items if there is less than five space in inventory.
    You can use either item's name or id. For the full list of items see ../../data/items.json

    It's highly recommended to put this task before move_to_fort and spin_fort task in the config file so you'll most likely be able to loot.

    Example config :
    {
      "type": "RecycleItems",
      "config": {
        "min_empty_space": 6,           # 6 by default
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
        self.min_empty_space = self.config.get('min_empty_space', None)
        self._validate_item_filter()

    def _validate_item_filter(self):
        """
        Validate user's item filter config
        :return: Nothing.
        :rtype: None
        :raise: ConfigException: When an item doesn't exist in ../../data/items.json
        """
        item_list = json.load(open(os.path.join(_base_dir, 'data', 'items.json')))
        for config_item_name, bag_count in self.items_filter.iteritems():
            if config_item_name not in item_list.viewvalues():
                if config_item_name not in item_list:
                    raise ConfigException("item {} does not exist, spelling mistake? (check for valid item names in data/items.json)".format(config_item_name))

    def should_run(self):
        """
        Returns a value indicating whether the recycling process should be run.
        :return: True if the recycling process should be run; otherwise, False.
        :rtype: bool
        """
        if inventory.items().get_space_left() < (DEFAULT_MIN_EMPTY_SPACE if self.min_empty_space is None else self.min_empty_space):
            return True
        return False

    def work(self):
        """
        Discard items if necessary.
        :return: Always returns WorkerResult.SUCCESS.
        :rtype: WorkerResult
        """
        # Updating inventory
        inventory.refresh_inventory()
        if self.should_run():
            # For each user's item in inventory recycle it if needed
            for item_in_inventory in inventory.items().all():
                item = RecycleItems._Item(item_in_inventory['item_id'], self.items_filter, self)

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
            self.amount_in_inventory = inventory.items().count_for(self.id)
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

        def update_inventory(self):
            """
            Update inventory if the item has been recycled. Prevent an unnecessary call to the api
            :return: Nothing.
            :rtype: None
            """
            if self.is_recycling_success():
                inventory.items().remove(self.id, self.amount_to_recycle)


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
            self.update_inventory()

        def is_recycling_success(self):
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
            if self.is_recycling_success():
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

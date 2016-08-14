import json
import os

from pokemongo_bot import inventory
from pokemongo_bot.base_dir import _base_dir
from pokemongo_bot.base_task import BaseTask
from pokemongo_bot.human_behaviour import action_delay
from pokemongo_bot.services.item_recycle_worker import ItemRecycler
from pokemongo_bot.tree_config_builder import ConfigException
from pokemongo_bot.worker_result import WorkerResult

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
        "max_balls_keep": 150,
        "max_potions_keep": 50,
        "max_berries_keep": 70,
        "max_revives_keep": 70,
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
        self.max_balls_keep = self.config.get('max_balls_keep', None)
        self.max_potions_keep = self.config.get('max_potions_keep', None)
        self.max_berries_keep = self.config.get('max_berries_keep', None)
        self.max_revives_keep = self.config.get('max_revives_keep', None)

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
                    raise ConfigException(
                        "item {} does not exist, spelling mistake? (check for valid item names in data/items.json)".format(
                            config_item_name))

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
        :return: Returns wether or not the task went well
        :rtype: WorkerResult
        """
        # TODO: Use new inventory everywhere and then remove the inventory update
        # Updating inventory
        inventory.refresh_inventory()
        worker_result = WorkerResult.SUCCESS

        if self.should_run():

            if not (self.max_balls_keep is None):
                self.recycle_excess_category_max(self.max_balls_keep, [1,2,3,4])
            if not (self.max_potions_keep is None):
                self.recycle_excess_category_max(self.max_potions_keep, [101,102,103,104])
            if not (self.max_berries_keep is None):
                self.recycle_excess_category_max(self.max_potions_keep, [701,702,703,704])
            if not (self.max_revives_keep is None):
                self.recycle_excess_category_max(self.max_potions_keep, [201,202])

            # For each user's item in inventory recycle it if needed
            for item_in_inventory in inventory.items().all():
                amount_to_recycle = self.get_amount_to_recycle(item_in_inventory)

                if self.item_should_be_recycled(item_in_inventory, amount_to_recycle):
                    action_delay(self.bot.config.action_wait_min, self.bot.config.action_wait_max)
                    if ItemRecycler(self.bot, item_in_inventory, amount_to_recycle).work() == WorkerResult.ERROR:
                        worker_result = WorkerResult.ERROR

        return worker_result
    
    def recycle_excess_category_max(self, category_max, category_items_list):
        """
        Recycle the item which excess the category max
        :param category_max:
        :param category_items_list:
        :return: none:
        :rtype: None
        """
        category_inventory = self.get_category_inventory_list(inventory, category_items_list)
        category_count = 0
        for i in category_inventory:
           category_count = category_count + i[1]
        items_to_recycle = self.get_category_items_to_recycle(category_inventory, category_count, category_max)
        for item in items_to_recycle:
            action_delay(self.bot.config.action_wait_min, self.bot.config.action_wait_max)
            if ItemRecycler(self.bot, inventory.items().get(item[0]), item[1]).work() == WorkerResult.ERROR:
                worker_result = WorkerResult.ERROR 

    def get_category_inventory_list(self, inventory, category_inventory):
        """
        Returns an array of items with the item id and item count.
        :param inventory:
        :param category_inventory:
        :return: array of items within a category:
        :rtype: array
        """
        x = 0
        category_inventory_list = []
        for c in category_inventory:
            category_inventory_list.append([])
            category_inventory_list[x].append(c)
            category_inventory_list[x].append(inventory.items().get(c).count)
            x = x + 1
        return category_inventory_list

    def get_category_items_to_recycle(self, category_inventory, category_count, category_max):
        """
        Returns an array to be recycle within a category of items with the item id and item count.
        :param category_inventory:
        :param category_count:
        :param category_max:
        :return: array of items to be recycle.
        :rtype: array
        """
        x = 0
        items_to_recycle = []
        if category_count > self.max_balls_keep:
            items_to_be_recycled = category_count - category_max

            for item in category_inventory:
                if items_to_be_recycled == 0: 
                    break
                if items_to_be_recycled >= item[1]:
                    items_to_recycle.append([])
                    items_to_recycle[x].append(item[0])
                    items_to_recycle[x].append(item[1])
                else:
                    items_to_recycle.append([])
                    items_to_recycle[x].append(item[0])
                    items_to_recycle[x].append(items_to_be_recycled)
                items_to_be_recycled = items_to_be_recycled - items_to_recycle[x][1]      
                x = x + 1
        return items_to_recycle

    def item_should_be_recycled(self, item, amount_to_recycle):
        """
        Returns a value indicating whether the item should be recycled.
        :param amount_to_recycle:
        :param item:
        :return: True if the title should be recycled; otherwise, False.
        :rtype: bool
        """
        return (item.name in self.items_filter or str(
            item.id) in self.items_filter) and amount_to_recycle > 0

    def get_amount_to_recycle(self, item):
        """
        Determine the amount to recycle accordingly to user config
        :param item: Item to determine the amount to recycle
        :return: The amount to recycle
        :rtype: int
        """
        amount_to_keep = self.get_amount_to_keep(item)
        return 0 if amount_to_keep is None else item.count - amount_to_keep

    def get_amount_to_keep(self, item):
        """
        Determine item's amount to keep in inventory.
        :param item:
        :return: Item's amount to keep in inventory.
        :rtype: int
        """
        item_filter_config = self.items_filter.get(item.name, 0)
        if item_filter_config is not 0:
            return item_filter_config.get('keep', 20)
        else:
            item_filter_config = self.items_filter.get(str(item.id), 0)
            if item_filter_config is not 0:
                return item_filter_config.get('keep', 20)

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
    SUPPORTED_TASK_API_VERSION = 1

    def __init__(self, bot, config):
        """

        :param bot:
        :type bot: pokemongo_bot.PokemonGoBot
        :param config:
        :return:
        """
        super(RecycleItems, self).__init__(bot, config)

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
                    raise ConfigException(
                        "item {} does not exist, spelling mistake? (check for valid item names in data/items.json)".format(
                            config_item_name))

    def should_run(self):
        """
        Returns a value indicating whether the recycling process should be run.
        :return: True if the recycling process should be run; otherwise, False.
        :rtype: bool
        """
        if inventory.Items.get_space_left() < (DEFAULT_MIN_EMPTY_SPACE if self.min_empty_space is None else self.min_empty_space):
            return True
        return False

    def work(self):
        """
        Start the process of recycling items if necessary.
        :return: Returns whether or not the task went well
        :rtype: WorkerResult
        """

        worker_result = WorkerResult.SUCCESS
        if self.should_run():
            for item_in_inventory in inventory.items().all():

                if self.item_should_be_recycled(item_in_inventory):
                    # Make the bot appears more human
                    action_delay(self.bot.config.action_wait_min, self.bot.config.action_wait_max)
                    # If at any recycling process call we got an error, we consider that the result of this task is error too.
                    if ItemRecycler(self.bot, item_in_inventory, self.get_amount_to_recycle(item_in_inventory)).work() == WorkerResult.ERROR:
                        worker_result = WorkerResult.ERROR
        return worker_result

    def item_should_be_recycled(self, item):
        """
        Returns a value indicating whether the item should be recycled.
        :param item: The Item to test
        :return: True if the title should be recycled; otherwise, False.
        :rtype: bool
        """
        return (item.name in self.items_filter or str(item.id) in self.items_filter) and self.get_amount_to_recycle(item) > 0

    def get_amount_to_recycle(self, item):
        """
        Determine the amount to recycle accordingly to user config
        :param item: Item to determine the amount to recycle.
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

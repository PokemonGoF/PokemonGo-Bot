import json
import os
from pokemongo_bot.base_task import BaseTask
from pokemongo_bot import inventory
from pokemongo_bot.base_dir import _base_dir


class UpdateWebInventory(BaseTask):
    SUPPORTED_TASK_API_VERSION = 1

    def initialize(self):
        pass

    def work(self):
        inventory.update_web_inventory()
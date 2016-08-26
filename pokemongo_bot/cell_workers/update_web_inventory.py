from pokemongo_bot.base_task import BaseTask
from pokemongo_bot import inventory


class UpdateWebInventory(BaseTask):
    SUPPORTED_TASK_API_VERSION = 1

    def initialize(self):
        pass

    def work(self):
        inventory.update_web_inventory()

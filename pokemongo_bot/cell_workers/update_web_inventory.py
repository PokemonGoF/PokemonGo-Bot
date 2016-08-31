from pokemongo_bot import inventory
from pokemongo_bot.base_task import BaseTask
from pokemongo_bot.worker_result import WorkerResult


class UpdateWebInventory(BaseTask):
    SUPPORTED_TASK_API_VERSION = 1

    def work(self):
        inventory.update_web_inventory()

        return WorkerResult.SUCCESS

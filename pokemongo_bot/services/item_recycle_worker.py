from pokemongo_bot.worker_result import WorkerResult
from pokemongo_bot.base_task import BaseTask
from pokemongo_bot import inventory
from pokemongo_bot.tree_config_builder import ConfigException

RECYCLE_REQUEST_RESPONSE_SUCCESS = 1
class ItemRecycler(BaseTask):
    """
    This class contains details of recycling process.
    """
    SUPPORTED_TASK_API_VERSION = 1
    def __init__(self, bot, item_to_recycle, amount_to_recycle):
        """
        Initialise an instance of ItemRecycler
        :param bot: The instance of the Bot
        :param item_to_recycle: The item to recycle
        :type item_to_recycle: inventory.Item
        :param amount_to_recycle: The amount to recycle
        :type amount_to_recycle: int
        :return: Nothing.
        :rtype: None
        """
        self.bot = bot
        self.item_to_recycle = item_to_recycle
        self.amount_to_recycle = amount_to_recycle
        self.recycle_item_request_result = None

    def work(self):
        """
        Start the recycling process
        :return: Returns whether or not the task went well
        :rtype: WorkerResult
        """
        if self.should_run():
            self.request_recycle()
            if self.is_recycling_success():
                self._update_inventory()
                self._emit_recycle_succeed()
                return WorkerResult.SUCCESS
            else:
                self._emit_recycle_failed()
                return WorkerResult.ERROR

    def should_run(self):
        """
        Returns a value indicating whether or not the recycler should be run.
        :return: True if the recycler should be run; otherwise, False.
        :rtype: bool
        """
        if self.amount_to_recycle > 0 and self.item_to_recycle is not None:
            return True
        return False

    def request_recycle(self):
        """
        Request recycling of the item and store api call response's result.
        :return: Nothing.
        :rtype: None
        """
        response = self.bot.api.recycle_inventory_item(item_id=self.item_to_recycle.id,
                                                       count=self.amount_to_recycle)
        # Example of good request response
        # {'responses': {'RECYCLE_INVENTORY_ITEM': {'result': 1, 'new_count': 46}}, 'status_code': 1, 'auth_ticket': {'expire_timestamp_ms': 1469306228058L, 'start': '/HycFyfrT4t2yB2Ij+yoi+on778aymMgxY6RQgvrGAfQlNzRuIjpcnDd5dAxmfoTqDQrbz1m2dGqAIhJ+eFapg==', 'end': 'f5NOZ95a843tgzprJo4W7Q=='}, 'request_id': 8145806132888207460L}
        self.recycle_item_request_result = response.get('responses', {}).get('RECYCLE_INVENTORY_ITEM', {}).get('result', 0)

    def _update_inventory(self):
        """
        Updates the inventory. Prevent an unnecessary call to the api
        :return: Nothing.
        :rtype: None
        """
        inventory.items().get(self.item_to_recycle.id).remove(self.amount_to_recycle)

    def is_recycling_success(self):
        """
        Returns a value indicating whether or not the item has been successfully recycled.
        :return: True if the item has been successfully recycled; otherwise, False.
        :rtype: bool
        """
        return self.recycle_item_request_result == RECYCLE_REQUEST_RESPONSE_SUCCESS

    def _emit_recycle_succeed(self):
        """
        Emits recycle succeed event in logs
        :return: Nothing.
        :rtype: None
        """
        self.emit_event(
                'item_discarded',
                formatted='Discarded {amount}x {item}.',
                data={
                    'amount': str(self.amount_to_recycle),
                    'item': self.item_to_recycle.name,
                }
        )

    def _emit_recycle_failed(self):
        """
        Emits recycle failed event in logs
        :return: Nothing.
        :rtype: None
        """
        self.emit_event(
                'item_discard_fail',
                formatted="Failed to discard {item}",
                data={
                    'item': self.item_to_recycle.name
                }
        )

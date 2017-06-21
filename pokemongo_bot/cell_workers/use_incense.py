from __future__ import absolute_import
import time
from pokemongo_bot.base_task import BaseTask
from pokemongo_bot.worker_result import WorkerResult
from pokemongo_bot.item_list import Item
from pokemongo_bot import inventory
from .utils import format_time


class UseIncense(BaseTask):
    SUPPORTED_TASK_API_VERSION = 1

    def initialize(self):
        self.start_time = 0
        self.use_incense = self.config.get('use_incense', False)
        self.use_order = self.config.get('use_order', {})
        self._update_inventory()

        self.types = {
          401: "Ordinary",
          402: "Spicy",
          403: "Cool",
          404: "Floral"
      }

    def _have_applied_incense(self):
        for applied_item in inventory.applied_items().all():
            if applied_item.expire_ms > 0:
                    mins = format_time(applied_item.expire_ms * 1000)
                    self.logger.info("Not applying incense, currently active: %s, %s minutes remaining", applied_item.item.name, mins)
                    return False
            else:
                    return True

    def _get_type(self):
        for order in self.use_order:
            if order == "ordinary" and self.incense_ordinary_count > 0:
                return Item.ITEM_INCENSE_ORDINARY.value
            if order == "spicy" and self.incense_spicy_count > 0:
                return Item.ITEM_INCENSE_SPICY.value
            if order == "cool" and self.incense_cool_count > 0:
                return Item.ITEM_INCENSE_COOL.value
            if order == "floral" and self.incense_floral_count > 0:
                return Item.ITEM_INCENSE_FLORAL.value

        return Item.ITEM_INCENSE_ORDINARY.value

    def _update_inventory(self):
        self.incense_ordinary_count = inventory.items().get(Item.ITEM_INCENSE_ORDINARY.value).count
        self.incense_spicy_count = inventory.items().get(Item.ITEM_INCENSE_SPICY.value).count
        self.incense_cool_count = inventory.items().get(Item.ITEM_INCENSE_COOL.value).count
        self.incense_floral_count = inventory.items().get(Item.ITEM_INCENSE_FLORAL.value).count

    def _has_count(self):
        return self.incense_ordinary_count > 0 or self.incense_spicy_count > 0 or self.incense_cool_count > 0 or self.incense_floral_count > 0

    def _should_run(self):
        if self._have_applied_incense:
            return False

        if not self.use_incense:
            return False

        if self._has_count() > 0 and self.start_time == 0:
            return True

        self._update_inventory()
        if self._has_count() and self.use_incense:
            return True

    def work(self):
        if self._should_run():
            self.start_time = time.time()
            
            request = self.bot.api.create_request()
            request.use_incense(incense_type=self._get_type())
            response_dict = request.call()
            
            result = response_dict.get('responses', {}).get('USE_INCENSE', {}).get('result', 0)
            if result is 1:
                self.emit_event(
                    'use_incense',
                    formatted="Using {type} incense. {incense_count} incense remaining",
                    data={
                        'type': self.types.get(type, 'Unknown'),
                        'incense_count': inventory.items().get(type).count
                    }
                )
            else:
                self.emit_event(
                    'use_incense',
                    formatted="Unable to use incense {type}. {incense_count} incense remaining",
                    data={
                        'type': self.types.get(type, 'Unknown'),
                        'incense_count': inventory.items().get(type).count
                    }
                )
        return WorkerResult.SUCCESS

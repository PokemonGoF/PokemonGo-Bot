import time
from pokemongo_bot.base_task import BaseTask
from pokemongo_bot.worker_result import WorkerResult
from pokemongo_bot.item_list import Item

class UseIncense(BaseTask):
    SUPPORTED_TASK_API_VERSION = 1

    def initialize(self):
      self.start_time = 0
      self.use_incense = self.config.get('use_incense', False)
      self.use_order = self.config.get('use_order', {})
      self.incense_ordinary_count = self.bot.item_inventory_count(Item.ITEM_INCENSE_ORDINARY.value)      
      self.incense_spicy_count = self.bot.item_inventory_count(Item.ITEM_INCENSE_SPICY.value)
      self.incense_cool_count = self.bot.item_inventory_count(Item.ITEM_INCENSE_COOL.value)      
      self.incense_floral_count = self.bot.item_inventory_count(Item.ITEM_INCENSE_FLORAL.value)
      self.types = {
        401: "Ordinary",
        402: "Spicy",
        403: "Cool",
        404: "Floral"
      }
      
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
      
    def _has_count(self):
      return self.incense_ordinary_count > 0 or self.incense_spicy_count > 0 or self.incense_cool_count > 0 or self.incense_floral_count > 0
            
    def _should_run(self):         
      if self._has_count() > 0 and self.start_time == 0:
        return True      
      
      using_incense = time.time() - self.start_time < 1800    
      if self._has_count() and self.use_incense and not using_incense:
        return True

    def work(self):
      if self._should_run():
        self.start_time = time.time()
        type = self._get_type()        
        response_dict = self.bot.api.use_incense(incense_type=type)
        result = response_dict.get('responses', {}).get('USE_INCENSE', {}).get('result', 0)
        if result is 1:
          self.emit_event(
              'use_incense',
              formatted="Using {type} incense. {incense_count} incense remaining",
              data={
                  'type': self.types.get(type, 'Unknown'),
                  'incense_count': self.bot.item_inventory_count(type)
              }
          )
        else:
          self.emit_event(
              'use_incense',
              formatted="Unable to use incense {type}. {incense_count} incense remaining",
              data={
                  'type': self.types.get(type, 'Unknown'),
                  'incense_count': self.bot.item_inventory_count(type)
              }
          )
      
      return WorkerResult.SUCCESS

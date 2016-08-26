import logging

import time


class BaseTask(object):
  TASK_API_VERSION = 1

  def __init__(self, bot, config):
    """

    :param bot:
    :type bot: pokemongo_bot.PokemonGoBot
    :param config:
    :return:
    """
    self.bot = bot
    self.config = config
    self._validate_work_exists()
    self.logger = logging.getLogger(type(self).__name__)
    self.enabled = config.get('enabled', True)
    self.last_log_time = time.time()
    self.initialize()

  def _validate_work_exists(self):
    method = getattr(self, 'work', None)
    if not method or not callable(method):
      raise NotImplementedError('Missing "work" method')

  def emit_event(self, event, sender=None, level='info', formatted='', data={}):
    if not sender:
      sender=self

    # Print log only if X seconds are passed from last log
    if (time.time() - self.last_log_time) > self.config.get('log_interval', 0):
      self.last_log_time = time.time()
      self.bot.event_manager.emit(
        event,
        sender=sender,
        level=level,
        formatted=formatted,
        data=data
      )

  def initialize(self):
    pass

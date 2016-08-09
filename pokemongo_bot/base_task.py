import logging


class BaseTask(object):
  TASK_API_VERSION = 1

  def __init__(self, bot, config):
    self.bot = bot
    self.config = config
    self._validate_work_exists()
    self.logger = logging.getLogger(type(self).__name__)
    self.initialize()

  def _validate_work_exists(self):
    method = getattr(self, 'work', None)
    if not method or not callable(method):
      raise NotImplementedError('Missing "work" method')

  def emit_event(self, event, sender=None, level='info', formatted='', data={}):
    if not sender:
      sender=self
    self.bot.event_manager.emit(
      event,
      sender=sender,
      level=level,
      formatted=formatted,
      data=data
    )

  def initialize(self):
    pass

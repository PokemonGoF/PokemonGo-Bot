class BaseTask(object):
  def __init__(self, bot, config, type):
    self.bot = bot
    self.type = type
    self.config = config
    self._validate_work_exists()
    self.initialize()

  def _validate_work_exists(self):
    method = getattr(self, 'work', None)
    if not method or not callable(method):
      raise NotImplementedError('Missing "work" method')

  def initialize(self):
    pass

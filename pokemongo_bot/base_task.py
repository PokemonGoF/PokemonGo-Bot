import logging
import time


class BaseTask(object):
    TASK_API_VERSION = 1

    def __init__(self, bot, config):
        self.bot = bot
        self.config = config
        self._validate_work_exists()
        self.logger = logging.getLogger(type(self).__name__)
        self.last_ran = time.time()
        self.run_interval = config.get('run_interval', 10)
        self.initialize()

    def _update_last_ran(self):
        self.last_ran = time.time()

    def _time_to_run(self):
        interval = time.time() - self.last_ran
        if interval > self.run_interval:
            return True
        return False

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

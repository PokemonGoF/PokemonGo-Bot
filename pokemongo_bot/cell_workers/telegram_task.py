# -*- coding: utf-8 -*-

import telegram
from pokemongo_bot.base_task import BaseTask
from pokemongo_bot.base_dir import _base_dir
from pokemongo_bot.event_handlers import TelegramHandler

class FileIOException(Exception):
    pass

class TelegramTask(BaseTask):
    SUPPORTED_TASK_API_VERSION = 1

    def initialize(self):
        if not self.enabled:
            return
        self.bot.event_manager.add_handler(TelegramHandler(self.bot, self.config))

    def work(self):
        if not self.enabled:
            return

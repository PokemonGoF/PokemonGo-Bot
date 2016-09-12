# -*- coding: utf-8 -*-

from pokemongo_bot.base_task import BaseTask
from pokemongo_bot.event_handlers import DiscordHandler

class FileIOException(Exception):
    pass

class DiscordTask(BaseTask):
    SUPPORTED_TASK_API_VERSION = 1

    def initialize(self):
        if not self.enabled:
            return
        self.bot.event_manager.add_handler(DiscordHandler(self.bot, self.config))

    def work(self):
        if not self.enabled:
            return

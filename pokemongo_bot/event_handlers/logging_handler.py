# -*- coding: utf-8 -*-
from __future__ import unicode_literals


import logging

from pokemongo_bot.event_manager import EventHandler


class LoggingHandler(EventHandler):
    
    def __init__(self, bot):
        self.bot = bot
        
    def handle_event(self, event, sender, level, formatted_msg, data):

        # Honour config settings if log level disabled
        for event_level in ['info', 'warning', 'error', 'critical', 'debug']:
            if event_level == level and hasattr(self.bot.config, event_level) and not getattr(self.bot.config, event_level):
                self._last_event = event
                return

        logger = logging.getLogger(type(sender).__name__)
        if formatted_msg:
            message = "[{}] {}".format(event, formatted_msg)
        else:
            message = '{}: {}'.format(event, str(data))
        getattr(logger, level)(message)

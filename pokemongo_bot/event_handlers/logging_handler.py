# -*- coding: utf-8 -*-
from __future__ import unicode_literals


import logging

from pokemongo_bot.event_manager import EventHandler


class LoggingHandler(EventHandler):

    def __init__(self, bot):
        self.bot = bot

    def handle_event(self, event, sender, level, formatted_msg, data):

        # Honour config settings if log level disabled
        if hasattr(self.bot.config, level) and not getattr(self.bot.config, level):
            return

        logger = logging.getLogger(type(sender).__name__)
        if formatted_msg:
            message = "[{}] {}".format(event, formatted_msg)
        else:
            message = '{}: {}'.format(event, str(data))
        getattr(logger, level)(message)

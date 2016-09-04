# -*- coding: utf-8 -*-
from __future__ import unicode_literals


import logging

from pokemongo_bot.event_manager import EventHandler


class LoggingHandler(EventHandler):

    def __init__(self, bot):
        self.bot = bot

    def handle_event(self, event, sender, level, formatted_msg, data):
        if not formatted_msg:
            formatted_msg = str(data)
        if self.bot.config.debug:
            formatted_msg = '[{}] {}'.format(event, formatted_msg)

        logger = logging.getLogger(type(sender).__name__)
        getattr(logger, level)(formatted_msg)

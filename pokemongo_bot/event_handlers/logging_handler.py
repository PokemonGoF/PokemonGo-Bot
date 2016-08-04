# -*- coding: utf-8 -*-
from __future__ import unicode_literals


import logging

from pokemongo_bot.event_manager import EventHandler


class LoggingHandler(EventHandler):

    def handle_event(self, event, sender, level, formatted_msg, data, **kwargs):
        logger = logging.getLogger(type(sender).__name__)
        if formatted_msg:
            message = "[{}] {}".format(event, formatted_msg)
        else:
            message = '{}: {}'.format(event, str(data))
        color = kwargs.get('color', 'white')
        logger.colorized(level, message, color)

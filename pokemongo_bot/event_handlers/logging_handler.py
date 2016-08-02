# -*- coding: utf-8 -*-

import logging

from pokemongo_bot.event_manager import EventHandler


class LoggingHandler(EventHandler):

    def handle_event(self, event, sender, level, formatted_msg, data):
        logger = logging.getLogger(type(sender).__name__)
        if formatted_msg:
            message = u"[{}] {}".format(event, formatted_msg)
        else:
            message = u'{}: {}'.format(event, str(data).decode('utf8'))
        getattr(logger, level)(message)

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import sys
import logging
from pokemongo_bot import logger
from pokemongo_bot.event_manager import EventHandler


class LoggingHandler(EventHandler):

    def __init__(self):
        # We call super constructor just to play it safe
        EventHandler.__init__(self)

        root_logger = logging.getLogger()
        # We need to now essentially override basicConfig
        root_logger.handlers = []

        # We now need to set up the stream/file handler
        #XXX: Should this be hard-coded to stdout?
        stream_handler = logging.StreamHandler(sys.stdout)

        # We're done with the basic **** and now turn on
        # the oh-so-pretty color logging
        stream_handler.setFormatter(logger.ColorizedLogFormatter())
        root_logger.addHandler(stream_handler)

    def handle_event(self, event, sender, level, formatted_msg, data, **kwargs):
        logger = logging.getLogger(type(sender).__name__)
        if formatted_msg:
            message = "[{}] {}".format(event, formatted_msg)
        else:
            message = '{}: {}'.format(event, str(data))
        color = kwargs.get('color', 'white')
        logger.colorized(level, message, color)
